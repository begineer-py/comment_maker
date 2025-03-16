#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
自動推送到GitHub的腳本
用於將代碼自動推送到GitHub倉庫
"""

import os
import sys
import subprocess
import datetime
import time
import platform
import argparse

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
            encoding="utf-8",
            errors="replace"
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

def check_git_installed():
    """檢查Git是否已安裝"""
    success, _ = run_command(["git", "--version"], "Git未安裝")
    return success

def check_git_repo():
    """檢查當前目錄是否為Git倉庫"""
    return os.path.isdir(".git")

def init_git_repo():
    """初始化Git倉庫"""
    if not check_git_repo():
        print_colored("初始化Git倉庫...", "yellow")
        success, _ = run_command(["git", "init"], "無法初始化Git倉庫")
        if not success:
            return False
        
        print_colored("添加遠程倉庫...", "yellow")
        success, _ = run_command(["git", "remote", "add", "origin", GITHUB_REPO], "無法添加遠程倉庫")
        return success
    
    return True

def check_remote_exists():
    """檢查遠程倉庫是否已配置"""
    success, output = run_command(["git", "remote", "-v"], "無法獲取遠程倉庫信息")
    if not success:
        return False
    
    return "origin" in output

def add_remote():
    """添加遠程倉庫"""
    if not check_remote_exists():
        print_colored("添加遠程倉庫...", "yellow")
        success, _ = run_command(["git", "remote", "add", "origin", GITHUB_REPO], "無法添加遠程倉庫")
        return success
    
    return True

def check_changes():
    """檢查是否有未提交的更改
    
    Returns:
        bool: 是否有更改
    """
    success, output = run_command(["git", "status", "--porcelain"], "無法檢查Git狀態")
    if not success:
        return False
    
    return bool(output.strip())

def add_all_changes():
    """添加所有更改到暫存區"""
    print_colored("添加所有更改到暫存區...", "yellow")
    success, _ = run_command(["git", "add", "."], "無法添加更改")
    return success

def commit_changes():
    """提交更改"""
    # 使用當前日期和時間作為提交信息
    commit_message = f"自動提交 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    print_colored(f"提交更改: {commit_message}", "yellow")
    
    success, _ = run_command(["git", "commit", "-m", commit_message], "無法提交更改")
    return success

def push_to_github(force=False):
    """推送到GitHub
    
    Args:
        force: 是否使用強制推送
        
    Returns:
        bool: 是否成功
    """
    print_colored("推送到GitHub...", "yellow")
    
    if force:
        print_colored("使用強制推送，將完全覆蓋遠端分支...", "yellow")
        # 使用--force-with-lease更安全，但如果需要完全覆蓋，可以使用-f
        success, output = run_command(["git", "push", "-u", "origin", "main", "-f"], "無法推送到GitHub")
    else:
        success, output = run_command(["git", "push", "-u", "origin", "main"], "無法推送到GitHub")
    
    # 如果推送失敗，可能是因為分支名稱不是main
    if not success and "main" in output:
        print_colored("嘗試使用master分支...", "yellow")
        if force:
            success, _ = run_command(["git", "push", "-u", "origin", "master", "-f"], "無法推送到GitHub")
        else:
            success, _ = run_command(["git", "push", "-u", "origin", "master"], "無法推送到GitHub")
    
    return success

def main():
    """主函數"""
    print_colored("=" * 50, "blue")
    print_colored("自動推送到GitHub腳本", "blue")
    print_colored("=" * 50, "blue")
    
    # 解析命令行參數
    parser = argparse.ArgumentParser(description="自動推送到GitHub的腳本")
    parser.add_argument("--force", "-F", action="store_true", help="使用強制推送")
    args = parser.parse_args()
    
    # 檢查Git是否已安裝
    if not check_git_installed():
        print_colored("請先安裝Git", "red")
        return False
    
    # 初始化Git倉庫（如果需要）
    if not init_git_repo():
        print_colored("無法初始化Git倉庫", "red")
        return False
    
    # 添加遠程倉庫（如果需要）
    if not add_remote():
        print_colored("無法添加遠程倉庫", "red")
        return False
    
    # 檢查是否有更改
    if not check_changes():
        print_colored("沒有需要提交的更改", "green")
        return True
    
    # 添加所有更改
    if not add_all_changes():
        print_colored("無法添加更改", "red")
        return False
    
    # 提交更改
    if not commit_changes():
        print_colored("無法提交更改", "red")
        return False
    
    # 推送到GitHub
    if not push_to_github(force=args.force):
        print_colored("無法推送到GitHub", "red")
        return False
    
    print_colored("=" * 50, "green")
    print_colored("成功推送到GitHub！", "green")
    print_colored("=" * 50, "green")
    
    return True

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