#!/usr/bin/env python # 指定Python解釋器路徑，確保腳本可直接執行
# -*- coding: utf-8 -*- # 指定文件編碼為UTF-8，支持中文

"""
Gemini代碼註釋器GUI啟動腳本
""" # 模塊文檔字符串，說明腳本功能

import sys # 導入sys模塊，用於系統相關操作
import os # 導入os模塊，用於操作系統功能（如文件路徑）
import tkinter as tk # 導入tkinter模塊，用於創建圖形用戶界面，並起別名tk

# 將專案根目錄添加到 Python 路徑中 # 現有註釋，保持不變
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) # 將當前文件所在目錄（項目根目錄）添加到Python模塊搜索路徑，方便導入自定義模塊

from gui.main_window import GeminiCommenterGUI # 從gui.main_window模塊中導入GeminiCommenterGUI類

def main(): # 定義主函數，用於啟動GUI應用
    """主函數""" # 主函數的文檔字符串
    print("=" * 50) # 打印一條分隔線，美化控制台輸出
    print("啟動Gemini代碼註釋器GUI") # 打印啟動信息到控制台
    print("=" * 50) # 打印另一條分隔線
    
    root = tk.Tk() # 創建Tkinter主窗口實例
    app = GeminiCommenterGUI(root) # 創建GeminiCommenterGUI應用實例，將主窗口作為父級
    root.mainloop() # 啟動Tkinter事件循環，使GUI應用保持運行並響應用戶操作

if __name__ == "__main__": # 判斷當前腳本是否作為主程序運行
    main() # 如果是主程序，則調用main函數啟動應用