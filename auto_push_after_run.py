#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
執行代碼註釋器並自動推送到GitHub的腳本
"""

import os
import sys
import subprocess
import datetime
import platform
import time

# GitHub倉庫URL
GITHUB_REPO = "https://github.com/begineer-py/comment_maker.git"

def print_colored(text, color="green"):
    """打印彩色文本
    
    Args:
        text: 要打印的文本
        color: 顏色（green, red, yellow, blue）
    """
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "end": "\033[0m"
    }
    
    # Windows命令提示符不支持ANSI顏色代碼，除非使用特殊設置
    if platform.system() == "Windows" and "ANSICON" not in os.environ:
        print(text)
    else:
        print(f"{colors.get(color, colors['green'])}{text}{colors['end']}")

def run_command(command, error_message=None):
    """運行命令並返回結果
    
    Args:
        command: 要運行的命令（字符串或列表）
        error_message: 錯誤時顯示的消息
        
    Returns:
        (success, output): 是否成功，輸出內容
    """
    try:
        if isinstance(command, str):
            command_list = command.split()
        else:
            command_list = command
            
        print_colored(f"執行命令: {' '.join(command_list)}", "blue")
        
        # 運行命令並捕獲輸出
        result = subprocess.run(
            command_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        
        if result.returncode != 0:
            if error_message:
                print_colored(f"錯誤: {error_message}", "red")
            print_colored(f"命令失敗: {result.stderr}", "red")
            return False, result.stderr
        
        return True, result.stdout
    except Exception as e:
        if error_message:
            print_colored(f"錯誤: {error_message}", "red")
        print_colored(f"執行命令時出錯: {e}", "red")
        return False, str(e)

def run_gemini_commenter(gui_mode=True, folder=None, output=None, recursive=False, file_filter="*.py", comment_style="line_end"):
    """運行Gemini代碼註釋器
    
    Args:
        gui_mode: 是否使用GUI模式
        folder: 源文件夾路徑
        output: 輸出文件夾路徑
        recursive: 是否遞歸處理子文件夾
        file_filter: 文件過濾器
        comment_style: 註釋風格
        
    Returns:
        bool: 是否成功
    """
    print_colored("=" * 50, "blue")
    print_colored("運行Gemini代碼註釋器", "blue")
    print_colored("=" * 50, "blue")
    
    if gui_mode:
        # 運行GUI版本
        print_colored("運行GUI版本...", "yellow")
        success, _ = run_command(["python", "gemini_commenter_gui.py"], "無法運行GUI版本")
    else:
        # 運行命令行版本
        cmd = ["python", "gemini_commenter.py"]
        
        if folder:
            cmd.extend(["--folder", folder])
        
        if output:
            cmd.extend(["--output", output])
        
        if recursive:
            cmd.append("--recursive")
        
        if file_filter:
            cmd.extend(["--filter", file_filter])
        
        if comment_style:
            cmd.extend(["--comment-style", comment_style])
        
        print_colored(f"運行命令行版本: {' '.join(cmd)}", "yellow")
        success, _ = run_command(cmd, "無法運行命令行版本")
    
    return success

def push_to_github():
    """推送到GitHub
    
    Returns:
        bool: 是否成功
    """
    print_colored("=" * 50, "blue")
    print_colored("推送到GitHub", "blue")
    print_colored("=" * 50, "blue")
    
    # 檢查Git是否已安裝
    success, _ = run_command(["git", "--version"], "Git未安裝")
    if not success:
        print_colored("請先安裝Git", "red")
        return False
    
    # 檢查是否為Git倉庫
    if not os.path.isdir(".git"):
        print_colored("初始化Git倉庫...", "yellow")
        success, _ = run_command(["git", "init"], "無法初始化Git倉庫")
        if not success:
            return False
        
        print_colored("添加遠程倉庫...", "yellow")
        success, _ = run_command(["git", "remote", "add", "origin", GITHUB_REPO], "無法添加遠程倉庫")
        if not success:
            return False
    
    # 檢查遠程倉庫是否已配置
    success, output = run_command(["git", "remote", "-v"], "無法獲取遠程倉庫信息")
    if not success:
        return False
    
    if "origin" not in output:
        print_colored("添加遠程倉庫...", "yellow")
        success, _ = run_command(["git", "remote", "add", "origin", GITHUB_REPO], "無法添加遠程倉庫")
        if not success:
            return False
    
    # 檢查是否有更改
    success, output = run_command(["git", "status", "--porcelain"], "無法檢查Git狀態")
    if not success:
        return False
    
    if not output.strip():
        print_colored("沒有需要提交的更改", "green")
        return True
    
    # 添加所有更改
    print_colored("添加所有更改到暫存區...", "yellow")
    success, _ = run_command(["git", "add", "."], "無法添加更改")
    if not success:
        return False
    
    # 提交更改
    commit_message = f"自動提交 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    print_colored(f"提交更改: {commit_message}", "yellow")
    success, _ = run_command(["git", "commit", "-m", commit_message], "無法提交更改")
    if not success:
        return False
    
    # 推送到GitHub
    print_colored("推送到GitHub...", "yellow")
    success, output = run_command(["git", "push", "-u", "origin", "main"], "無法推送到GitHub")
    
    # 如果推送失敗，可能是因為分支名稱不是main
    if not success and "main" in output:
        print_colored("嘗試使用master分支...", "yellow")
        success, _ = run_command(["git", "push", "-u", "origin", "master"], "無法推送到GitHub")
    
    if success:
        print_colored("=" * 50, "green")
        print_colored("成功推送到GitHub！", "green")
        print_colored("=" * 50, "green")
    
    return success

def main():
    """主函數"""
    print_colored("=" * 50, "blue")
    print_colored("執行代碼註釋器並自動推送到GitHub", "blue")
    print_colored("=" * 50, "blue")
    
    # 解析命令行參數
    import argparse
    parser = argparse.ArgumentParser(description="執行代碼註釋器並自動推送到GitHub")
    parser.add_argument("--no-gui", action="store_true", help="使用命令行版本而不是GUI版本")
    parser.add_argument("--folder", "-f", help="源文件夾路徑")
    parser.add_argument("--output", "-o", help="輸出文件夾路徑")
    parser.add_argument("--recursive", "-r", action="store_true", help="遞歸處理子文件夾")
    parser.add_argument("--filter", default="*.py", help="文件過濾器，如：*.py,*.js,*.html")
    parser.add_argument("--comment-style", choices=["line_end", "line_start"], default="line_end", help="註釋風格")
    parser.add_argument("--no-push", action="store_true", help="不推送到GitHub")
    args = parser.parse_args()
    
    # 運行Gemini代碼註釋器
    success = run_gemini_commenter(
        gui_mode=not args.no_gui,
        folder=args.folder,
        output=args.output,
        recursive=args.recursive,
        file_filter=args.filter,
        comment_style=args.comment_style
    )
    
    if not success:
        print_colored("運行Gemini代碼註釋器失敗", "red")
        return False
    
    # 如果指定了不推送，則直接返回
    if args.no_push:
        print_colored("已跳過推送到GitHub", "yellow")
        return True
    
    # 等待一段時間，確保所有文件都已寫入
    print_colored("等待文件寫入完成...", "yellow")
    time.sleep(2)
    
    # 推送到GitHub
    return push_to_github()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print_colored("\n操作已取消", "yellow")
        sys.exit(1)
    except Exception as e:
        print_colored(f"發生錯誤: {e}", "red")
        sys.exit(1) 