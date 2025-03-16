#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API設置模塊
處理API密鑰設置和測試相關功能
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# 導入API金鑰管理模組
from api_key_manager import save_api_key, test_api_connection, save_api_key_permanently

class ApiSettingsDialog:
    """API設置對話框類"""
    
    def __init__(self, parent, current_api_key, on_save_callback):
        """初始化API設置對話框
        
        Args:
            parent: 父窗口
            current_api_key: 當前API密鑰
            on_save_callback: 保存API密鑰後的回調函數
        """
        self.parent = parent
        self.current_api_key = current_api_key
        self.on_save_callback = on_save_callback
        self.dialog = None
        self.api_entry = None
        self.show_var = None
        self.test_label = None
        
    def show(self):
        """顯示API設置對話框"""
        # 創建對話框
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("API密鑰設置")
        self.dialog.geometry("500x300")
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
        
        # 創建API密鑰輸入框
        ttk.Label(frame, text="Gemini API密鑰:").pack(anchor=tk.W, pady=(0, 5))
        
        api_frame = ttk.Frame(frame)
        api_frame.pack(fill=tk.X, pady=5)
        
        self.api_entry = ttk.Entry(api_frame)
        self.api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        if self.current_api_key:
            self.api_entry.insert(0, self.current_api_key)
        
        # 創建顯示/隱藏密鑰按鈕
        self.show_var = tk.BooleanVar(value=False)
        self.api_entry.config(show="*")
        
        def toggle_show():
            if self.show_var.get():
                self.api_entry.config(show="")
            else:
                self.api_entry.config(show="*")
        
        ttk.Checkbutton(api_frame, text="顯示", variable=self.show_var, command=toggle_show).pack(side=tk.LEFT, padx=5)
        
        # 添加說明標籤
        ttk.Label(frame, text="請輸入您的Gemini API密鑰。您可以從Google AI Studio獲取免費的API密鑰。", 
                 wraplength=480).pack(fill=tk.X, pady=5)
        
        # 添加注意事項標籤
        note_label = ttk.Label(frame, text="注意：API密鑰將僅保存在當前程序會話中，程序關閉後將失效。\n要永久保存API密鑰，請使用下方的「永久保存」按鈕或設置系統環境變量 GEMINI_API_KEY。", 
                              foreground="red", wraplength=480)
        note_label.pack(fill=tk.X, pady=5)
        
        # 添加測試連接按鈕
        test_frame = ttk.Frame(frame)
        test_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(test_frame, text="測試連接", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        self.test_label = ttk.Label(test_frame, text="", foreground="blue")
        self.test_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 添加按鈕框架
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 添加保存按鈕
        ttk.Button(btn_frame, text="保存到會話", command=self.save_and_close).pack(side=tk.LEFT, padx=5)
        
        # 添加永久保存按鈕
        ttk.Button(btn_frame, text="永久保存", command=self.save_permanently).pack(side=tk.LEFT, padx=5)
        
        # 添加取消按鈕
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 設置焦點
        self.api_entry.focus_set()
        
        # 綁定回車鍵
        self.dialog.bind("<Return>", lambda event: self.save_and_close())
        self.dialog.bind("<Escape>", lambda event: self.dialog.destroy())
        
    def test_connection(self):
        """測試API連接"""
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showerror("錯誤", "API密鑰不能為空", parent=self.dialog)
            return
        
        # 更新測試標籤
        self.test_label.config(text="正在測試連接...", foreground="blue")
        self.dialog.update()
        
        # 在單獨的線程中測試連接
        def run_test():
            success, error_msg = test_api_connection(api_key)
            
            # 更新UI（在主線程中）
            self.dialog.after(0, lambda: self._update_test_result(success, error_msg))
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def _update_test_result(self, success, error_msg):
        """更新測試結果（在主線程中調用）"""
        if success:
            self.test_label.config(text="連接成功！", foreground="green")
        else:
            self.test_label.config(text=f"連接失敗: {error_msg}", foreground="red")
            messagebox.showerror("連接失敗", 
                               f"無法連接到Gemini API: {error_msg}\n\n"
                               "請確保您輸入了正確的API密鑰。\n\n"
                               "Gemini API密鑰通常是一個長字符串。\n"
                               "請從Google AI Studio複製完整的API密鑰。", 
                               parent=self.dialog)
    
    def save_and_close(self):
        """保存API密鑰並關閉對話框"""
        api_key = self.api_entry.get().strip()
        if api_key:
            # 調用回調函數
            self.on_save_callback(api_key)
            self.dialog.destroy()
        else:
            messagebox.showerror("錯誤", "API密鑰不能為空", parent=self.dialog)
    
    def save_permanently(self):
        """永久保存API密鑰"""
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showerror("錯誤", "API密鑰不能為空", parent=self.dialog)
            return
        
        # 顯示確認對話框
        confirm = messagebox.askyesno(
            "確認永久保存", 
            "此操作將嘗試將API密鑰永久保存到系統環境變數中。\n\n"
            "- 在Windows上，將使用PowerShell設置用戶級環境變數\n"
            "- 在Linux/macOS上，將添加到~/.bashrc或~/.zshrc文件\n\n"
            "是否繼續？", 
            parent=self.dialog
        )
        
        if not confirm:
            return
        
        # 嘗試永久保存
        success, message = save_api_key_permanently(api_key)
        
        if success:
            # 調用回調函數
            self.on_save_callback(api_key)
            
            messagebox.showinfo(
                "保存成功", 
                f"API密鑰已成功永久保存！\n\n{message}\n\n"
                "此設置將在所有新打開的程序中生效。", 
                parent=self.dialog
            )
        else:
            messagebox.showerror(
                "保存失敗", 
                f"無法永久保存API密鑰：\n{message}\n\n"
                "請嘗試手動設置系統環境變數。", 
                parent=self.dialog
            ) 