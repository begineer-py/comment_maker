#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
文件處理模塊
處理文件處理相關功能
"""

import os
import sys
import subprocess
import threading
import queue
import time

class FileProcessor:
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
    
    def start_processing(self, folder, output, recursive, api_key, file_filter="*.py", 
                        delay=6.0, max_backoff=64.0, comment_style="line_end", 
                        model_name="gemini-1.5-pro"):
        """開始處理文件
        
        Args:
            folder: 源文件夾路徑
            output: 輸出文件夾路徑
            recursive: 是否遞歸處理子文件夾
            api_key: API密鑰
            file_filter: 文件過濾器
            delay: 請求延遲時間
            max_backoff: 最大退避時間
            comment_style: 註釋風格
            model_name: 模型名稱
        """
        if self.is_processing:
            return
            
        self.is_processing = True
        
        # 在單獨的線程中處理文件
        try:
            threading.Thread(
                target=self.process_files,
                args=(folder, output, recursive, api_key, file_filter, delay, max_backoff, comment_style, model_name),
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"[ERROR] 啟動處理時出錯: {e}")
            import traceback
            traceback.print_exc()
            self.queue.put(("message", ("錯誤", f"啟動處理時出錯: {str(e)}", True)))
            self.is_processing = False
    
    def process_files(self, folder, output, recursive, api_key, file_filter="*.py", 
                     delay=6.0, max_backoff=64.0, comment_style="line_end", 
                     model_name="gemini-1.5-pro"):
        """處理選定的文件夾中的文件（在單獨的線程中運行）
        
        Args:
            folder: 源文件夾路徑
            output: 輸出文件夾路徑
            recursive: 是否遞歸處理子文件夾
            api_key: API密鑰
            file_filter: 文件過濾器
            delay: 請求延遲時間
            max_backoff: 最大退避時間
            comment_style: 註釋風格
            model_name: 模型名稱
        """
        print(f"[INFO] 開始處理文件: 當前線程ID={threading.get_ident()}, 主線程ID={threading.main_thread().ident}")
        print(f"[INFO] 是否在主線程中: {threading.current_thread() is threading.main_thread()}")
        
        try:
            # 確保我們有有效的延遲和最大退避時間值
            if delay is None or delay < 0:
                print("[WARNING] 延遲值無效，使用默認值 1.0")
                delay = 1.0
            
            if max_backoff is None or max_backoff <= 0:
                print("[WARNING] 最大退避時間值無效，使用默認值 60.0")
                max_backoff = 60.0
                
            print(f"[INFO] 使用延遲={delay}秒, 最大退避時間={max_backoff}秒, 註釋風格={comment_style}, 模型={model_name}")
            
            # 打印API密鑰信息（部分隱藏）
            masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            print(f"[INFO] 使用API密鑰: {masked_key} (長度: {len(api_key)})")
            
            # 構建命令
            command = [
                "python", 
                "gemini_commenter.py",
                "--folder", folder,
                "--output", output,
                "--delay", str(delay),
                "--max-backoff", str(max_backoff),
                "--model", model_name,
                "--api-key", api_key  # 直接傳遞API密鑰，避免環境變量問題
            ]
            
            # 添加遞歸參數
            if recursive:
                command.append("--recursive")
                
            # 添加文件過濾參數
            if file_filter and file_filter != "*.py":
                command.extend(["--filter", file_filter])
                
            # 添加註釋風格參數
            command.extend(["--comment-style", comment_style])
            
            # 打印命令（隱藏API密鑰）
            safe_command = command.copy()
            api_key_index = safe_command.index("--api-key") + 1
            safe_command[api_key_index] = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            print(f"[INFO] 執行命令: {' '.join(safe_command)}")
            
            # 設置環境變量
            env = os.environ.copy()
            # 確保環境變量中也有API密鑰
            env["GEMINI_API_KEY"] = api_key
            print(f"[INFO] 已設置環境變量 GEMINI_API_KEY")
            
            # 運行命令並處理輸出
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            # 使用計數器而不是直接訪問進度條
            processed_count = 0
            total_files = 0
            
            # 讀取輸出
            for line in self.process.stdout:
                line = line.strip()
                # 只記錄重要的輸出行
                if "ERROR" in line or "WARNING" in line or "Processing" in line or "Completed" in line or "Successfully" in line:
                    print(f"[OUTPUT] {line}")
                
                # 添加到日誌
                self.queue.put(("log", line))
                
                # 檢查是否找到了文件總數 - 同時支持中英文
                if ("Found" in line and "files" in line) or ("找到" in line and "個Python文件" in line) or ("找到" in line and "個文件" in line):
                    try:
                        # 嘗試從不同格式的輸出中提取文件數量
                        if "Found" in line and "files" in line:
                            # 英文格式: "Found 2 files"
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "Found" and i+1 < len(parts):
                                    try:
                                        total_files = int(parts[i+1])
                                        break
                                    except:
                                        pass
                        else:
                            # 中文格式: "找到 2 個Python文件" 或 "找到 2 個文件"
                            total_files = int(line.split("找到")[1].split("個")[0].strip())
                        
                        if total_files > 0:
                            self.queue.put(("progress_max", total_files))
                            self.queue.put(("status", f"處理 {total_files} 個文件..."))
                            print(f"[INFO] 設置總文件數: {total_files}")
                    except Exception as e:
                        print(f"[ERROR] 解析文件總數時出錯: {e}")
                
                # 檢查是否處理了新文件 - 同時支持中英文
                elif ("Completed" in line and "->" in line) or ("已完成" in line) or ("Processing completed" in line and "successfully" in line):
                    # 如果是處理完成的總結行，提取總數
                    if "Processing completed" in line and "successfully" in line:
                        try:
                            # 格式: "Processing completed: 2/2 files successfully commented"
                            parts = line.split(":")
                            if len(parts) > 1:
                                fraction = parts[1].split("files")[0].strip()
                                success, total = fraction.split("/")
                                processed_count = int(success.strip())
                                if total_files == 0:  # 如果之前沒有設置總數
                                    total_files = int(total.strip())
                                    self.queue.put(("progress_max", total_files))
                        except Exception as e:
                            print(f"[ERROR] 解析處理完成信息時出錯: {e}")
                    else:
                        # 單個文件處理完成
                        processed_count += 1
                        
                    # 更新進度
                    self.queue.put(("progress", processed_count))
                    if total_files > 0:
                        self.queue.put(("status", f"已處理 {processed_count}/{total_files} 個文件"))
                    else:
                        self.queue.put(("status", f"已處理 {processed_count} 個文件"))
                    print(f"[INFO] 更新處理計數: {processed_count}/{total_files}")
            
            # 等待進程完成
            return_code = self.process.wait()
            
            # 處理完成
            if return_code == 0:
                if total_files > 0:
                    self.queue.put(("status", f"成功處理了 {processed_count}/{total_files} 個文件"))
                    self.queue.put(("message", ("處理完成", f"成功處理了 {processed_count}/{total_files} 個文件", False)))
                else:
                    self.queue.put(("status", f"成功處理了 {processed_count} 個文件"))
                    self.queue.put(("message", ("處理完成", f"成功處理了 {processed_count} 個文件", False)))
            else:
                self.queue.put(("status", f"處理完成，但有錯誤 (返回碼: {return_code})"))
                self.queue.put(("message", ("處理錯誤", f"處理完成，但有錯誤 (返回碼: {return_code})", True)))
            
        except Exception as e:
            print(f"[ERROR] 處理文件時出錯: {e}")
            import traceback
            traceback.print_exc()
            self.queue.put(("status", "處理時出錯"))
            self.queue.put(("message", ("處理錯誤", f"處理文件時出錯: {str(e)}", True)))
        
        finally:
            # 通知主線程處理已完成
            print("[INFO] 文件處理完成")
            self.queue.put(("processing_done", None))
            self.is_processing = False
            self.process = None
            
            # 調用完成回調
            if self.on_complete_callback:
                self.on_complete_callback()
    
    def stop_processing(self):
        """停止處理"""
        if not self.is_processing:
            return
            
        # 終止進程
        if self.process:
            try:
                self.process.terminate()
                # 給進程一些時間來終止
                time.sleep(0.5)
                # 如果進程仍在運行，強制終止
                if self.process.poll() is None:
                    self.process.kill()
            except Exception as e:
                print(f"[ERROR] 終止進程時出錯: {e}")
        
        # 使用隊列更新狀態，避免線程問題
        self.queue.put(("status", "已停止"))
        self.queue.put(("log", "處理已停止"))
        self.queue.put(("message", ("已停止", "處理已停止", False)))
        self.is_processing = False 