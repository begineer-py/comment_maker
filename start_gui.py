#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gemini代碼註釋器GUI啟動腳本
啟動Gemini代碼註釋器的圖形界面
"""

import os
import sys
import tkinter as tk
from gemini_commenter_gui import GeminiCommenterGUI

def main():
    """主函數"""
    print("=" * 50)
    print("啟動Gemini代碼註釋器GUI")
    print("=" * 50)
    
    # 檢查環境變量
    api_key_env = "GEMINI_API_KEY"
    if api_key_env not in os.environ:
        print(f"警告: 未設置環境變量 {api_key_env}")
        print(f"您可以通過以下方式設置環境變量:")
        if sys.platform == 'win32':
            print(f"  Windows PowerShell: $env:{api_key_env} = \"your-api-key\"")
            print(f"  Windows CMD: set {api_key_env}=your-api-key")
        else:
            print(f"  Linux/macOS: export {api_key_env}=your-api-key")
        print("或者在啟動後通過GUI設置API密鑰")
    
    # 創建根窗口
    root = tk.Tk()
    
    # 創建應用
    app = GeminiCommenterGUI(root)
    
    # 運行主循環
    root.mainloop()

if __name__ == "__main__":
    main() 