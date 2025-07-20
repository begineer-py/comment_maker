#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gemini代碼註釋器GUI啟動腳本
"""

import sys
import os
import tkinter as tk

# 將專案根目錄添加到 Python 路徑中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main_window import GeminiCommenterGUI

def main():
    """主函數"""
    print("=" * 50)
    print("啟動Gemini代碼註釋器GUI")
    print("=" * 50)
    
    root = tk.Tk()
    app = GeminiCommenterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
