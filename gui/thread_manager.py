#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件處理模塊
處理文件處理相關功能
"""

import os
from core.orchestrator import ProjectOrchestrator
import subprocess
import threading
import queue
import time
from config.config import Config


class ProcessingThreadManager:
    """文件處理類"""

    def __init__(self, queue, on_complete_callback=None):
        """初始化文件處理器

        Args:
            queue: 消息隊列，用於與主線程通信
            on_complete_callback: 處理完成後的回調函數
        """
        self.queue = queue
        self.on_complete_callback = on_complete_callback
        self.is_processing = False
        self.process = None

    def start_processing(self, settings):  # 將所有參數替換為一個 settings 字典
        """開始處理文件
        Args:
            settings (dict): 包含所有配置的字典
        """
        if self.is_processing:
            return

        self.is_processing = True

        # 從 settings 字典中提取參數
        folder = settings.get("folder")
        output = settings.get("output")
        recursive = settings.get("recursive")
        api_key = settings.get("api_key")
        file_filter = settings.get("file_filter", Config.DEFAULT_FILE_FILTER)
        delay = settings.get("delay", Config.DEFAULT_REQUEST_DELAY)
        max_backoff = settings.get("max_backoff", Config.DEFAULT_MAX_BACKOFF)
        model_name = settings.get("model_name", Config.DEFAULT_MODEL_NAME)
        use_nyaproxy = settings.get("nyaproxy", False)  # 注意這裡的鍵名

        # 在單獨的線程中處理文件
        try:
            threading.Thread(
                target=self.process_files,
                args=(
                    folder,
                    output,
                    recursive,
                    api_key,
                    file_filter,
                    delay,
                    max_backoff,
                    model_name,
                    use_nyaproxy,
                ),
                daemon=True,
            ).start()

        except Exception as e:
            print(f"[ERROR] 啟動處理時出錯: {e}")
            import traceback

            traceback.print_exc()
            self.queue.put(("message", ("錯誤", f"啟動處理時出錯: {str(e)}", True)))
            self.is_processing = False

    def process_files(
        self,
        folder,
        output,
        recursive,
        api_key,
        file_filter=Config.DEFAULT_FILE_FILTER,
        delay=Config.DEFAULT_REQUEST_DELAY,
        max_backoff=Config.DEFAULT_MAX_BACKOFF,
        model_name=Config.DEFAULT_MODEL_NAME,
        use_nyaproxy=False,
    ):
        """處理選定的文件夾中的文件（在單獨的線程中運行）

        Args:
            folder: 源文件夾路徑
            output: 輸出文件夾路徑
            recursive: 是否遞歸處理子文件夾
            api_key: API密鑰
            file_filter: 文件過濾器
            delay: 請求延遲時間
            max_backoff: 最大退避時間
            model_name: 模型名稱
        """
        print(
            f"[INFO] 開始處理文件: 當前線程ID={threading.get_ident()}, 主線程ID={threading.main_thread().ident}"
        )
        print(
            f"[INFO] 是否在主線程中: {threading.current_thread() is threading.main_thread()}"
        )

        try:
            # 確保我們有有效的延遲和最大退避時間值
            if delay is None or delay < 0:
                print("[WARNING] 延遲值無效，使用默認值 1.0")
                delay = 1.0

            if max_backoff is None or max_backoff <= 0:
                print("[WARNING] 最大退避時間值無效，使用默認值 60.0")
                max_backoff = 60.0

            print(
                f"[INFO] 使用延遲={delay}秒, 最大退避時間={max_backoff}秒, 模型={model_name}"
            )

            # 打印API密鑰信息（部分隱藏）
            print(f"[DEBUG] api_key 的值: {api_key}, 類型: {type(api_key)}")  # 新增日誌
            if api_key is not None:  # 避免 NoneType 錯誤
                masked_key = (
                    f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
                )
                print(f"[INFO] 使用API密鑰: {masked_key} (長度: {len(api_key)})")
            else:
                print("[WARNING] API密鑰為 None，無法打印其長度。")

            # 構建命令
            command = [
                "python",
                "gemini_commenter.py",
                "--folder",
                folder,
                "--output",
                output,
                "--filter",
                file_filter,
                "--delay",
                str(delay),
                "--max-backoff",
                str(max_backoff),
                "--model",
                model_name,
                "--api-key",
                api_key,
            ]
            if use_nyaproxy:
                command.append("--nyaproxy")
            if recursive:
                command.append("--recursive")

            if file_filter and file_filter != "*.py":
                command.extend(["--filter", file_filter])
            # 打印命令（隱藏API密鑰）
            safe_command = command.copy()
            api_key_index = safe_command.index("--api-key") + 1
            safe_command[api_key_index] = (
                f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            )
            print(f"[INFO] 執行命令: {' '.join(safe_command)}")

            settings = {
                "folder": folder,
                "output": output,
                "recursive": recursive,
                "api_key": api_key,
                "filter": file_filter,  # 將 file_filter 鍵改為 filter
                "delay": delay,
                "max_backoff": max_backoff,
                "use_nyaproxy": use_nyaproxy,
                "model_name": model_name,
            }

            # 創建並運行協調器
            orchestrator = ProjectOrchestrator(settings, self.queue)
            orchestrator.run()

        except Exception as e:
            self.queue.put(
                ("log", f"[FATAL] An error occurred in the processing thread: {e}")
            )
        finally:
            # Safely signal the main thread that processing is finished.
            if self.on_complete_callback:
                self.queue.put(("callback", self.on_complete_callback))

    def stop_processing(self):
        """Requests to stop the processing thread."""
        # This is a simplified stop mechanism. A truly graceful stop would require
