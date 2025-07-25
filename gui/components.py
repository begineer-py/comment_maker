#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
UI組件模塊
處理UI相關功能
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import webbrowser


class LogPanel:
    """日誌面板類"""

    def __init__(self, parent):
        """初始化日誌面板

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.frame = ttk.LabelFrame(parent, text="日誌")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 創建日誌文本框和滾動條
        self.log_frame = ttk.Frame(self.frame)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.scrollbar = ttk.Scrollbar(self.log_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            self.log_frame,
            height=10,
            width=80,
            wrap=tk.WORD,
            yscrollcommand=self.scrollbar.set,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.log_text.yview)

        # 創建按鈕框架
        self.btn_frame = ttk.Frame(self.frame)
        self.btn_frame.pack(fill=tk.X, padx=5, pady=5)

        # 添加清除按鈕
        self.clear_btn = ttk.Button(self.btn_frame, text="清除日誌", command=self.clear)
        self.clear_btn.pack(side=tk.RIGHT, padx=5)

    def add_log(self, message):
        """添加日誌消息

        Args:
            message: 日誌消息
        """
        # 確保在主線程中執行
        if threading.current_thread() is threading.main_thread():
            self._add_log_internal(message)
        else:
            self.parent.after(0, lambda: self._add_log_internal(message))

    def _add_log_internal(self, message):
        """內部添加日誌消息（在主線程中調用）

        Args:
            message: 日誌消息
        """
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def clear(self):
        """清除日誌"""
        # 確保在主線程中執行
        if threading.current_thread() is threading.main_thread():
            self._clear_internal()
        else:
            self.parent.after(0, self._clear_internal)

    def _clear_internal(self):
        """內部清除日誌（在主線程中調用）"""
        self.log_text.delete(1.0, tk.END)


class StatusBar:
    """狀態欄類"""

    def __init__(self, parent):
        """初始化狀態欄

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)

        # 創建狀態標籤
        self.status_label = ttk.Label(self.frame, text="就緒", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 創建進度條
        self.progress = ttk.Progressbar(self.frame, mode="determinate", length=200)
        self.progress.pack(side=tk.RIGHT, padx=5)

        # 設置默認最大值
        self.progress["maximum"] = 100
        self.progress["value"] = 0

    def update_status(self, status):
        """更新狀態文本

        Args:
            status: 狀態文本
        """
        # 確保在主線程中執行
        if threading.current_thread() is threading.main_thread():
            self._update_status_internal(status)
        else:
            self.parent.after(0, lambda: self._update_status_internal(status))

    def _update_status_internal(self, status):
        """內部更新狀態文本（在主線程中調用）

        Args:
            status: 狀態文本
        """
        self.status_label.config(text=status)

    def update_progress(self, value):
        """更新進度條值

        Args:
            value: 進度值
        """
        # 確保在主線程中執行
        if threading.current_thread() is threading.main_thread():
            self._update_progress_internal(value)
        else:
            self.parent.after(0, lambda: self._update_progress_internal(value))

    def _update_progress_internal(self, value):
        """內部更新進度條值（在主線程中調用）

        Args:
            value: 進度值
        """
        self.progress["value"] = value

    def set_progress_max(self, max_value):
        """設置進度條最大值

        Args:
            max_value: 最大值
        """
        # 確保在主線程中執行
        if threading.current_thread() is threading.main_thread():
            self._set_progress_max_internal(max_value)
        else:
            self.parent.after(0, lambda: self._set_progress_max_internal(max_value))

    def _set_progress_max_internal(self, max_value):
        """內部設置進度條最大值（在主線程中調用）

        Args:
            max_value: 最大值
        """
        self.progress["maximum"] = max_value

    def reset(self):
        """重置狀態欄"""
        # 確保在主線程中執行
        if threading.current_thread() is threading.main_thread():
            self._reset_internal()
        else:
            self.parent.after(0, self._reset_internal)

    def _reset_internal(self):
        """內部重置狀態欄（在主線程中調用）"""
        self.status_label.config(text="就緒")
        self.progress["value"] = 0


class SettingsPanel:
    """設置面板類"""

    def __init__(
        self, parent, on_browse_folder, on_browse_output, initial_api_key=None
    ):  # 新增 initial_api_key
        """初始化設置面板

        Args:
            parent: 父窗口
            on_browse_folder: 瀏覽源文件夾回調
            on_browse_output: 瀏覽輸出文件夾回調
            initial_api_key: 初始API密鑰
        """
        self.parent = parent
        self.on_browse_folder = on_browse_folder
        self.on_browse_output = on_browse_output
        self.api_key = initial_api_key  # 保存API密鑰

        # 創建設置框架
        self.frame = ttk.LabelFrame(parent, text="設置")
        self.frame.pack(fill=tk.X, padx=10, pady=5)

        # 創建網格佈局
        self.grid = ttk.Frame(self.frame)
        self.grid.pack(fill=tk.X, padx=5, pady=5)

        # 源文件夾設置
        ttk.Label(self.grid, text="源文件夾:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )

        self.folder_frame = ttk.Frame(self.grid)
        self.folder_frame.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        self.folder_entry = ttk.Entry(self.folder_frame)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            self.folder_frame, text="瀏覽...", command=self.on_browse_folder
        ).pack(side=tk.RIGHT, padx=5)

        # 輸出文件夾設置
        ttk.Label(self.grid, text="輸出文件夾:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )

        self.output_frame = ttk.Frame(self.grid)
        self.output_frame.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

        self.output_entry = ttk.Entry(self.output_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            self.output_frame, text="瀏覽...", command=self.on_browse_output
        ).pack(side=tk.RIGHT, padx=5)

        # 遞歸處理設置
        ttk.Label(self.grid, text="遞歸處理:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )

        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.grid, variable=self.recursive_var).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5
        )

        # 文件過濾器設置
        ttk.Label(self.grid, text="文件過濾器:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5
        )

        self.filter_frame = ttk.Frame(self.grid)
        self.filter_frame.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)

        self.filter_entry = ttk.Entry(self.filter_frame)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.filter_entry.insert(0, "*.py")

        ttk.Label(self.filter_frame, text="(例如: *.py,*.js,*.html)").pack(
            side=tk.RIGHT, padx=5
        )

        # nyaproxy 選項
        self.nyaproxy_var = tk.BooleanVar(value=False)  # 默認為不使用
        nyaproxy_check = ttk.Checkbutton(
            self.grid, text="使用 nyaproxy", variable=self.nyaproxy_var
        )
        nyaproxy_check.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        # 模型設置
        ttk.Label(self.grid, text="模型:").grid(
            row=5, column=0, sticky=tk.W, padx=5, pady=5
        )

        self.model_frame = ttk.Frame(self.grid)
        self.model_frame.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)

        self.model_var = tk.StringVar(value="gemini-2.5-flash")
        self.model_combo = ttk.Combobox(
            self.model_frame, textvariable=self.model_var, state="readonly"
        )
        self.model_combo["values"] = "gemini-2.5-flash"
        self.model_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 延遲設置
        ttk.Label(self.grid, text="請求延遲(秒):").grid(
            row=6, column=0, sticky=tk.W, padx=5, pady=5
        )

        self.delay_frame = ttk.Frame(self.grid)
        self.delay_frame.grid(row=6, column=1, sticky=tk.EW, padx=5, pady=5)

        self.delay_var = tk.DoubleVar(value=6.0)
        self.delay_spin = ttk.Spinbox(
            self.delay_frame,
            from_=0.5,
            to=30.0,
            increment=0.5,
            textvariable=self.delay_var,
            width=10,
        )
        self.delay_spin.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.delay_frame, text="(避免API限制)").pack(side=tk.LEFT, padx=5)

        # 設置列的權重
        self.grid.columnconfigure(1, weight=1)

    def get_settings(self):
        """獲取設置值

        Returns:
            dict: 設置值字典
        """
        return {
            "folder": self.folder_entry.get(),
            "output": self.output_entry.get(),
            "recursive": self.recursive_var.get(),
            "file_filter": self.filter_entry.get(),
            "model_name": self.model_var.get(),
            "delay": self.delay_var.get(),
            "nyaproxy": self.nyaproxy_var.get(),
            "api_key": self.api_key,  # 新增 api_key
        }

    def update_api_key(self, new_api_key):  # 新增方法
        """更新API密鑰"""
        self.api_key = new_api_key


class HelpDialog:
    """幫助對話框類"""

    def __init__(self, parent):
        """初始化幫助對話框

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.dialog = None

    def show(self):
        """顯示幫助對話框"""
        # 創建對話框
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("幫助")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 設置對話框在父窗口中居中
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.parent.winfo_width() - width) // 2 + self.parent.winfo_x()
        y = (self.parent.winfo_height() - height) // 2 + self.parent.winfo_y()
        self.dialog.geometry(f"+{x}+{y}")

        # 創建主框架
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # 創建標題
        title_label = ttk.Label(
            frame, text="Gemini代碼註釋器使用幫助", font=("Arial", 14, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # 創建幫助文本框和滾動條
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        help_text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        help_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=help_text.yview)

        # 設置幫助文本
        help_content = """
Gemini代碼註釋器是一個使用Google Gemini AI為代碼添加中文註釋的工具。

基本使用步驟：

1. 設置API密鑰
   - 點擊「設置」菜單中的「API密鑰設置」
   - 輸入您的Gemini API密鑰
   - 點擊「測試連接」確保API密鑰有效
   - 點擊「保存到會話」或「永久保存」

2. 設置源文件夾和輸出文件夾
   - 源文件夾：包含要添加註釋的代碼文件的文件夾
   - 輸出文件夾：保存添加註釋後的代碼文件的文件夾

3. 配置處理選項
   - 遞歸處理：是否處理子文件夾中的文件
   - 文件過濾器：指定要處理的文件類型，如：*.py,*.js,*.html
   - 註釋風格：選擇行尾註釋或行前註釋
   - 模型：選擇要使用的Gemini模型
   - 請求延遲：設置API請求之間的延遲時間，避免API限制

4. 開始處理
   - 點擊「開始處理」按鈕
   - 處理過程中可以在日誌面板查看進度
   - 處理完成後會顯示處理結果

5. 查看結果
   - 點擊「打開輸出文件夾」查看生成的文件
   - 生成的文件保持原始文件的目錄結構

注意事項：

- API密鑰：您需要有一個有效的Google Gemini API密鑰
- 文件大小：大文件處理可能需要更長時間
- API限制：Gemini API有使用限制，請適當設置延遲時間
- 處理時間：處理時間取決於文件數量、大小和API響應速度

獲取API密鑰：
您可以從Google AI Studio獲取免費的Gemini API密鑰：
https://aistudio.google.com/

如需更多幫助，請訪問項目主頁或聯繫開發者。
        """

        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)

        # 添加關閉按鈕
        ttk.Button(frame, text="關閉", command=self.dialog.destroy).pack(
            side=tk.RIGHT, pady=10
        )

        # 添加訪問Google AI Studio的按鈕
        def open_ai_studio():
            webbrowser.open("https://aistudio.google.com/")

        ttk.Button(frame, text="訪問Google AI Studio", command=open_ai_studio).pack(
            side=tk.LEFT, pady=10
        )


class AboutDialog:
    """關於對話框類"""

    def __init__(self, parent):
        """初始化關於對話框

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.dialog = None

    def show(self):
        """顯示關於對話框"""
        # 創建對話框
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("關於")
        self.dialog.geometry("800x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 設置對話框在父窗口中居中
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.parent.winfo_width() - width) // 2 + self.parent.winfo_x()
        y = (self.parent.winfo_height() - height) // 2 + self.parent.winfo_y()
        self.dialog.geometry(f"+{x}+{y}")

        # 創建主框架
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # 創建標題
        title_label = ttk.Label(
            frame, text="Gemini代碼註釋器", font=("Arial", 16, "bold")
        )
        title_label.pack(anchor=tk.CENTER, pady=(10, 5))

        # 創建版本信息
        version_label = ttk.Label(frame, text="版本 1.0.0")
        version_label.pack(anchor=tk.CENTER, pady=(0, 20))

        # 創建描述
        desc_label = ttk.Label(
            frame, text="使用Google Gemini AI為代碼添加中文註釋的工具", wraplength=350
        )
        desc_label.pack(anchor=tk.CENTER, pady=(0, 20))

        # 創建版權信息
        copyright_label = ttk.Label(frame, text="© 2024 版權所有")
        copyright_label.pack(anchor=tk.CENTER, pady=(0, 5))

        # 創建技術信息
        tech_label = ttk.Label(
            frame,
            text="使用Python和Tkinter開發\n基於Google Generative AI API",
            justify=tk.CENTER,
        )
        tech_label.pack(anchor=tk.CENTER, pady=(0, 20))

        # 添加關閉按鈕
        ttk.Button(frame, text="關閉", command=self.dialog.destroy).pack(
            side=tk.BOTTOM, pady=10
        )


class ExcludeSettingsDialog:
    """文件排除設置對話框類"""

    def __init__(self, parent):
        """初始化文件排除設置對話框

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.dialog = None
        self.exclude_patterns = []
        self._load_exclude_patterns()

    def _load_exclude_patterns(self):
        """從 config/exclude.yaml 載入排除模式"""
        from config.exclude_file import exclude_patterns

        try:
            self.exclude_patterns = exclude_patterns()
        except Exception as e:
            messagebox.showerror("錯誤", f"載入排除模式失敗: {e}")
            self.exclude_patterns = []  # 確保即使載入失敗也有一個空列表

    def _save_exclude_patterns(self):
        """將排除模式保存到 config/exclude.yaml"""
        from config.exclude_file import save_exclude_patterns

        try:
            save_exclude_patterns(self.exclude_patterns)
            messagebox.showinfo("成功", "排除模式已成功保存。")
            self.dialog.destroy()  # 保存後關閉對話框
        except Exception as e:
            messagebox.showerror("錯誤", f"保存排除模式失敗: {e}")

    def show(self):
        """顯示文件排除設置對話框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("文件排除設置")
        self.dialog.geometry("600x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 設置對話框在父窗口中居中
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.parent.winfo_width() - width) // 2 + self.parent.winfo_x()
        y = (self.parent.winfo_height() - height) // 2 + self.parent.winfo_y()
        self.dialog.geometry(f"+{x}+{y}")

        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 列表框顯示現有模式
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.listbox = tk.Listbox(list_frame, height=10, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        self._populate_listbox()

        # 輸入和操作按鈕框架
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.entry_var = tk.StringVar()
        self.entry = ttk.Entry(control_frame, textvariable=self.entry_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(control_frame, text="新增", command=self._add_pattern).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(control_frame, text="修改", command=self._edit_pattern).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(control_frame, text="刪除", command=self._delete_pattern).pack(
            side=tk.LEFT
        )

        # 保存和取消按鈕
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="保存", command=self._save_exclude_patterns).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(
            side=tk.RIGHT
        )

        self.dialog.wait_window()  # 等待對話框關閉

    def _populate_listbox(self):
        """填充列表框"""
        self.listbox.delete(0, tk.END)
        for pattern in self.exclude_patterns:
            self.listbox.insert(tk.END, pattern)

    def _add_pattern(self):
        """新增排除模式"""
        pattern = self.entry_var.get().strip()
        if pattern and pattern not in self.exclude_patterns:
            self.exclude_patterns.append(pattern)
            self._populate_listbox()
            self.entry_var.set("")  # 清空輸入框
        elif pattern in self.exclude_patterns:
            messagebox.showwarning("警告", "該模式已存在。")

    def _edit_pattern(self):
        """修改選定的排除模式"""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "請選擇一個要修改的模式。")
            return

        index = selected_indices[0]
        old_pattern = self.exclude_patterns[index]
        new_pattern = self.entry_var.get().strip()

        if not new_pattern:
            messagebox.showwarning("警告", "新模式不能為空。")
            return

        if new_pattern == old_pattern:
            messagebox.showinfo("提示", "模式未更改。")
            return

        if new_pattern in self.exclude_patterns:
            messagebox.showwarning("警告", "新模式已存在。")
            return

        self.exclude_patterns[index] = new_pattern
        self._populate_listbox()
        self.entry_var.set("")  # 清空輸入框

    def _delete_pattern(self):
        """刪除選定的排除模式"""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("警告", "請選擇一個要刪除的模式。")
            return

        index = selected_indices[0]
        pattern_to_delete = self.exclude_patterns[index]

        if messagebox.askyesno(
            "確認刪除", f"確定要刪除模式 '{pattern_to_delete}' 嗎？"
        ):
            del self.exclude_patterns[index]
            self._populate_listbox()
            self.entry_var.set("")  # 清空輸入框
