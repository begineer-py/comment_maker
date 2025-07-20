import sys
import platform
import threading
import tkinter as tk


def show_system_info(info_set):
    """打印系統信息"""
    print("=" * 50)
    print(f"[INFO] 啟動Gemini代碼註釋器GUI")
    print(f"[INFO] Python版本: {sys.version}")
    print(f"[INFO] 操作系統: {platform.system()} {platform.version()}")
    print(
        f"[INFO] 當前線程ID: {threading.get_ident()}, 主線程ID: {threading.main_thread().ident}"
    )
    print(
        f"[INFO] 是否在主線程中: {threading.current_thread() is threading.main_thread()}"
    )
    print("=" * 50)

    # 打印Tkinter信息
    print(f"[INFO] Tkinter版本: {tk.TkVersion}")
    print(f"[INFO] 可用的Tkinter主題: {', '.join(info_set.available_themes)}")
    print(f"[INFO] 使用'{info_set.current_theme}'主題")
    print(
        f"[DEBUG] 初始化GUI: 當前線程ID={threading.get_ident()}, 主線程ID={threading.main_thread().ident}"
    )
    print(
        f"[DEBUG] 是否在主線程中: {threading.current_thread() is threading.main_thread()}"
    )
