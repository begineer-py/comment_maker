#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gemini代碼註釋器GUI
使用Google Gemini AI為代碼添加中文註釋的圖形界面工具
從環境變量讀取API密鑰
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import subprocess
import platform
import time

# 導入API金鑰管理模組
from config.API_config.api_manager import get_api_key, save_api_key
from config.API_config.test_api_connection import TestApiConnection
from gui.components import (
    SettingsPanel,
    LogPanel,
    StatusBar,
    HelpDialog,
    AboutDialog,
    ExcludeSettingsDialog,  # 新增導入
)
from gui.thread_manager import ProcessingThreadManager

from config.config import Config
from config.show_config import show_system_info


class GeminiCommenterGUI:
    """Gemini代碼註釋器GUI主類"""

    def __init__(self, root):
        """初始化GUI

        Args:
            root: Tkinter根窗口
        """
        self.API_KEY_ENV_NAME = Config.API_KEY_ENV_NAME
        self.root = root
        self.root.title("Gemini代碼註釋器")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)

        # 設置主題
        self.available_themes = sorted(ttk.Style().theme_names())
        self.current_theme = "alt"  # 默認主題
        ttk.Style().theme_use(self.current_theme)

        # 打印系統信息
        show_system_info(self)

        # 創建消息隊列
        self.queue = queue.Queue()
        print("[DEBUG] 消息隊列已創建")

        # 初始化變量
        self.api_key = None
        self.is_processing = False

        # 獲取API密鑰
        self._get_api_key()

        # 創建UI組件
        self._create_ui()

        # 創建菜單
        self._create_menu()

        # 創建文件處理器
        self.file_processor = ProcessingThreadManager(
            self.queue, on_complete_callback=self._on_processing_complete
        )

        # 開始處理消息隊列
        self._start_queue_processing()

        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # 打印初始化完成信息
        show_system_info(self)

    def _get_api_key(self):
        """獲取API密鑰"""
        self.api_key = get_api_key()

        if self.api_key:
            masked_key = (
                f"{self.api_key[:4]}...{self.api_key[-4:]}"
                if len(self.api_key) > 8
                else "***"
            )
            print(f"[LOG] 已獲取API密鑰: {masked_key} (長度: {len(self.api_key)})")
            if hasattr(self, "settings_panel"):  # 確保 settings_panel 已初始化
                self.settings_panel.update_api_key(
                    self.api_key
                )  # 更新 settings_panel 中的 api_key
        else:
            print(f"[WARNING] 未找到API密鑰，請設置環境變量 {self.API_KEY_ENV_NAME}")

    def _create_ui(self):
        """創建UI組件"""
        # 創建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 創建設置面板
        self.settings_panel = SettingsPanel(
            self.main_frame,
            self._browse_folder,
            self._browse_output,
            initial_api_key=self.api_key,  # 傳遞 initial_api_key
        )

        # 創建按鈕框架
        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(fill=tk.X, padx=10, pady=5)

        # 添加開始處理按鈕
        self.start_btn = ttk.Button(
            self.btn_frame, text="開始處理", command=self._start_processing
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        # 添加停止處理按鈕
        self.stop_btn = ttk.Button(
            self.btn_frame,
            text="停止處理",
            command=self._stop_processing,
            state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 添加打開輸出文件夾按鈕
        self.open_output_btn = ttk.Button(
            self.btn_frame, text="打開輸出文件夾", command=self._open_output_folder
        )
        self.open_output_btn.pack(side=tk.RIGHT, padx=5)

        # 創建日誌面板
        self.log_panel = LogPanel(self.main_frame)

        # 創建狀態欄
        self.status_bar = StatusBar(self.root)

    def _create_menu(self):
        """創建菜單"""
        # 創建菜單欄
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # 創建文件菜單
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="開始處理", command=self._start_processing)
        file_menu.add_command(label="停止處理", command=self._stop_processing)
        file_menu.add_separator()
        file_menu.add_command(label="打開輸出文件夾", command=self._open_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)

        # 創建設置菜單
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="設置", menu=settings_menu)
        settings_menu.add_command(label="API密鑰設置", command=self._show_api_settings)
        settings_menu.add_command(
            label="文件排除設置", command=self._show_exclude_settings
        )  # 新增菜單項

        # 創建主題子菜單
        theme_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="主題", menu=theme_menu)

        # 添加主題選項
        for theme in self.available_themes:
            theme_menu.add_command(
                label=theme, command=lambda t=theme: self._change_theme(t)
            )

        # 創建幫助菜單
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="幫助", menu=help_menu)
        help_menu.add_command(label="使用幫助", command=self._show_help)
        help_menu.add_command(label="關於", command=self._show_about)

    def _start_queue_processing(self):
        """開始處理消息隊列"""
        print("[DEBUG] 啟動消息隊列處理")
        print(
            f"[DEBUG] 檢查消息隊列: 當前線程ID={threading.get_ident()}, 主線程ID={threading.main_thread().ident}"
        )
        print(
            f"[DEBUG] 是否在主線程中: {threading.current_thread() is threading.main_thread()}"
        )

        self._process_queue()
        print("[DEBUG] 消息隊列處理已啟動")

    def _process_queue(self):
        """處理消息隊列"""
        try:
            # 檢查隊列中是否有消息
            while not self.queue.empty():
                message_type, data = self.queue.get(0)

                # 根據消息類型處理
                if message_type == "log":
                    self.log_panel.add_log(data)
                elif message_type == "status":
                    self.status_bar.update_status(data)
                elif message_type == "progress":
                    progress_value, status_message = data  # 解包進度值和狀態消息
                    self.status_bar.update_progress(progress_value)
                    self.status_bar.update_status(status_message)  # 更新狀態欄文本
                elif message_type == "progress_max":
                    self.status_bar.set_progress_max(data)
                elif message_type == "message":
                    title, message, error = data
                    self._show_message(title, message, error)
                elif message_type == "processing_done":
                    self._mark_processing_done()

                # 標記消息已處理
                self.queue.task_done()
                print(f"[DEBUG] 消息 {message_type} 處理完成")
        except Exception as e:
            print(f"[ERROR] 處理消息隊列時出錯: {e}")

        # 每100毫秒檢查一次隊列
        self.root.after(100, self._process_queue)

    def _check_api_key(self):
        """檢查API密鑰是否有效

        Returns:
            bool: 如果API密鑰有效則返回True，否則返回False
        """
        if not self.api_key:
            print(f"[WARNING] API密鑰未設置，請設置環境變量 {self.API_KEY_ENV_NAME}")
            self._prompt_for_api_key()
            return False

        # 打印部分API密鑰信息，保護隱私
        masked_key = (
            f"{self.api_key[:4]}...{self.api_key[-4:]}"
            if len(self.api_key) > 8
            else "***"
        )
        print(f"[DEBUG] 使用API密鑰: {masked_key} (長度: {len(self.api_key)})")

        return True

    def _prompt_for_api_key(self):
        """提示用戶輸入API密鑰"""
        self._show_api_settings()

    def _show_api_settings(self):
        """顯示API設置對話框"""
        # 創建API設置對話框
        # 由於 ApiSettingsDialog 未定義，這裡假設它是一個需要實現的類
        # 為了不阻礙當前任務，暫時註釋或替換為一個佔位符
        # api_settings = ApiSettingsDialog(self.root, self.api_key, self._save_api_key)
        # api_settings.show()
        messagebox.showinfo("提示", "API密鑰設置功能待實現或修復。")  # 臨時佔位符

    def _show_exclude_settings(self):
        """顯示文件排除設置對話框"""
        exclude_settings = ExcludeSettingsDialog(self.root)
        exclude_settings.show()

    def _save_api_key(self, api_key):
        """保存API密鑰

        Args:
            api_key: API密鑰
        """
        if api_key:
            self.api_key = api_key
            save_api_key(api_key)

            # 更新日誌
            masked_key = (
                f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            )
            self.log_panel.add_log(
                f"API密鑰已更新: {masked_key} (長度: {len(api_key)})"
            )
            if hasattr(self, "settings_panel"):  # 確保 settings_panel 已初始化
                self.settings_panel.update_api_key(
                    api_key
                )  # 更新 settings_panel 中的 api_key
            if hasattr(self, "settings_panel"):  # 確保 settings_panel 已初始化
                self.settings_panel.update_api_key(
                    api_key
                )  # 更新 settings_panel 中的 api_key
            if hasattr(self, "settings_panel"):  # 確保 settings_panel 已初始化
                self.settings_panel.update_api_key(
                    api_key
                )  # 更新 settings_panel 中的 api_key

    def _test_api_connection(self, nyaproxy_enabled):
        """測試API連接"""
        # 使用新的測試函數，直接接收 nyaproxy 狀態
        return TestApiConnection(self.api_key, nyaproxy_enabled).test_api_connection()

    def _browse_folder(self):
        """瀏覽選擇源文件夾"""
        folder = filedialog.askdirectory(title="選擇源文件夾")
        if folder:
            self.settings_panel.folder_entry.delete(0, tk.END)
            self.settings_panel.folder_entry.insert(0, folder)

    def _browse_output(self):
        """瀏覽選擇輸出文件夾"""
        folder = filedialog.askdirectory(title="選擇輸出文件夾")
        if folder:
            self.settings_panel.output_entry.delete(0, tk.END)
            self.settings_panel.output_entry.insert(0, folder)

    def _start_processing(self):
        """開始處理文件"""
        # 0. 檢查是否有正在進行的任務
        if self.is_processing:
            self._show_message("警告", "一個處理程序已在運行中", True)
            return

        # 1. 檢查API金鑰
        if not self._check_api_key():
            return

        # 2. 獲取所有設定
        settings = self.settings_panel.get_settings()
        folder = settings["folder"]
        output = settings["output"]

        # 3. 驗證資料夾路徑
        if not folder or not output:
            self._show_message("錯誤", "請選擇源文件夾和輸出文件夾", True)
            return
        if not os.path.exists(folder):
            self._show_message("錯誤", f"源文件夾不存在: {folder}", True)
            return

        # 4. 測試API連線 (使用從設定中獲取的值)
        if not self._test_api_connection(settings["nyaproxy"]):
            self._show_message(
                "錯誤", "無法連接到Gemini API，請檢查API金鑰和網絡連接", True
            )
            return

        # 5. 更新UI狀態並記錄日誌
        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_bar.update_status("正在準備處理...")
        self.status_bar.update_progress(0)

        # 添加日誌
        self.log_panel.add_log(f"開始處理文件夾: {folder}")
        self.log_panel.add_log(f"輸出到: {output}")
        self.log_panel.add_log(f"遞歸處理: {'是' if settings['recursive'] else '否'}")
        self.log_panel.add_log(f"文件過濾: {settings['file_filter']}")
        self.log_panel.add_log(f"使用模型: {settings['model_name']}")
        self.log_panel.add_log(f"請求延遲: {settings['delay']}秒")
        self.log_panel.add_log("使用指數退避算法處理API限制")
        self.log_panel.add_log(
            f"使用nyaproxy: {'是' if settings['nyaproxy'] else '否'}"
        )

        # 6. 開始處理
        self.file_processor.start_processing(settings)

    def _stop_processing(self):
        """停止處理"""
        if not self.is_processing:
            return

        # 停止處理
        self.file_processor.stop_processing()

        # 更新UI狀態
        self._mark_processing_done()

    def _mark_processing_done(self):
        """標記處理完成"""
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        print("[DEBUG] 標記處理完成成功")

    def _on_processing_complete(self):
        """處理完成回調"""
        # 更新UI狀態
        self._mark_processing_done()

    def _open_output_folder(self):
        """打開輸出文件夾"""
        output = self.settings_panel.output_entry.get()

        if not output:
            self._show_message("錯誤", "請先設置輸出文件夾", True)
            return

        if not os.path.exists(output):
            try:
                os.makedirs(output, exist_ok=True)
            except Exception as e:
                self._show_message("錯誤", f"無法創建輸出文件夾: {e}", True)
                return

        # 根據不同操作系統打開文件夾
        try:
            if sys.platform == "win32":
                os.startfile(output)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", output])
            else:  # Linux
                subprocess.run(["xdg-open", output])
        except Exception as e:
            self._show_message("錯誤", f"無法打開輸出文件夾: {e}", True)

    def _change_theme(self, theme):
        """更改主題

        Args:
            theme: 主題名稱
        """
        try:
            ttk.Style().theme_use(theme)
            self.current_theme = theme
            print(f"[INFO] 已切換到'{theme}'主題")
        except Exception as e:
            print(f"[ERROR] 切換主題時出錯: {e}")

    def _show_help(self):
        """顯示幫助對話框"""
        help_dialog = HelpDialog(self.root)
        help_dialog.show()

    def _show_about(self):
        """顯示關於對話框"""
        about_dialog = AboutDialog(self.root)
        about_dialog.show()

    def _show_message(self, title, message, error=False):
        """顯示消息對話框

        Args:
            title: 標題
            message: 消息內容
            error: 是否為錯誤消息
        """
        if threading.current_thread() is threading.main_thread():
            self._show_message_internal(title, message, error)
        else:
            self.root.after(
                0, lambda: self._show_message_internal(title, message, error)
            )

    def _show_message_internal(self, title, message, error=False):
        """內部顯示消息對話框（在主線程中調用）

        Args:
            title: 標題
            message: 消息內容
            error: 是否為錯誤消息
        """
        if error:
            messagebox.showerror(title, message)
        else:
            messagebox.showinfo(title, message)
        print(f"[DEBUG] 消息對話框顯示成功: {title}")

    def _on_closing(self):
        """關閉窗口時的處理"""
        if self.is_processing:
            confirm = messagebox.askyesno("確認", "處理正在進行中，確定要退出嗎？")
            if not confirm:
                return

            # 停止處理
            self.file_processor.stop_processing()

        # 關閉窗口
        self.root.destroy()
