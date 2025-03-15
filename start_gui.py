#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动Gemini代码注释器GUI的脚本
"""

import os
import sys
import platform
import threading
import traceback
import subprocess

def check_dependencies():
    """检查必要的依赖是否已安装"""
    required_packages = [
        "tkinter",
        "google-generativeai",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "tkinter":
                import tkinter
            else:
                __import__(package.replace("-", "_"))
            print(f"[INFO] 已安装: {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"[ERROR] 未安装: {package}")
    
    return missing_packages

def install_dependencies(packages):
    """安装缺失的依赖"""
    print(f"[INFO] 正在安装缺失的依赖: {', '.join(packages)}")
    
    # 创建requirements.txt文件
    with open("requirements.txt", "w") as f:
        for package in packages:
            if package != "tkinter":  # tkinter不能通过pip安装
                f.write(f"{package}\n")
    
    # 安装依赖
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[INFO] 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 安装依赖时出错: {e}")
        return False

def main():
    """主函数"""
    try:
        print("\n" + "="*50)
        print(f"[INFO] 启动Gemini代码注释器GUI启动脚本")
        print(f"[INFO] Python版本: {sys.version}")
        print(f"[INFO] 操作系统: {platform.system()} {platform.release()} ({platform.platform()})")
        print(f"[INFO] 当前线程ID: {threading.get_ident()}, 主线程ID: {threading.main_thread().ident}")
        print(f"[INFO] 是否在主线程中: {threading.current_thread() is threading.main_thread()}")
        print(f"[INFO] 当前工作目录: {os.getcwd()}")
        print("="*50 + "\n")
        
        # 检查是否在主线程中运行
        if threading.current_thread() is not threading.main_thread():
            print("[ERROR] GUI必须在主线程中运行")
            return
        
        # 检查依赖
        missing_packages = check_dependencies()
        
        # 如果有缺失的依赖，尝试安装
        if missing_packages:
            if "tkinter" in missing_packages:
                print("[ERROR] 未安装Tkinter。Tkinter是Python的标准库，无法通过pip安装。")
                print("请参考以下链接安装Tkinter:")
                print("- Windows: https://tkdocs.com/tutorial/install.html#installwin")
                print("- macOS: https://tkdocs.com/tutorial/install.html#installmac")
                print("- Linux: https://tkdocs.com/tutorial/install.html#installlinux")
                return
            
            # 尝试安装其他缺失的依赖
            missing_packages = [p for p in missing_packages if p != "tkinter"]
            if missing_packages and not install_dependencies(missing_packages):
                print("[ERROR] 无法安装缺失的依赖，请手动安装")
                return
        
        # 导入GUI模块
        try:
            print("[INFO] 导入GUI模块")
            from gemini_commenter_gui import main as gui_main
            print("[INFO] 成功导入GUI模块")
        except ImportError as e:
            print(f"[ERROR] 导入GUI模块时出错: {e}")
            traceback.print_exc()
            return
        
        # 启动GUI
        print("[INFO] 启动GUI")
        gui_main()
        print("[INFO] GUI已关闭")
        
    except Exception as e:
        print(f"[ERROR] 启动GUI时出错: {e}")
        traceback.print_exc()
        
        # 尝试显示错误对话框
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("错误", f"启动GUI时出错: {str(e)}")
        except:
            print("[ERROR] 无法显示错误对话框")

if __name__ == "__main__":
    main() 