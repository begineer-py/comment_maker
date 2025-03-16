#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
強制推送腳本
用於完全覆蓋遠端分支的腳本
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

def force_push_to_github():
    """強制推送到GitHub，完全覆蓋遠端分支
    
    Returns:
        bool: 是否成功
    """
    print_colored("=" * 50, "blue")
    print_colored("強制推送到GitHub", "blue")
    print_colored("=" * 50, "blue")
    
    # 檢查Git是否已安裝
    success, _ = run_command(["git", "--version"], "Git未安裝")
    if not success:
        print_colored("請先安裝Git", "red")
        return False
    
    # 檢查是否為Git倉庫
    if not os.path.isdir(".git"):
        print_colored("錯誤: 當前目錄不是Git倉庫", "red")
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
    
    # 添加所有更改
    print_colored("添加所有更改到暫存區...", "yellow")
    success, _ = run_command(["git", "add", "."], "無法添加更改")
    if not success:
        return False
    
    # 檢查是否有更改
    success, output = run_command(["git", "status", "--porcelain"], "無法檢查Git狀態")
    if not success:
        return False
    
    # 如果有更改，提交它們
    if output.strip():
        # 提交更改
        commit_message = f"強制提交 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        print_colored(f"提交更改: {commit_message}", "yellow")
        success, _ = run_command(["git", "commit", "-m", commit_message], "無法提交更改")
        if not success:
            return False
    else:
        print_colored("沒有新的更改需要提交，將直接強制推送當前狀態...", "yellow")
    
    # 獲取當前分支名稱
    success, branch_output = run_command(["git", "branch", "--show-current"], "無法獲取當前分支")
    if not success:
        # 嘗試使用另一種方式獲取分支名稱
        success, branch_output = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], "無法獲取當前分支")
        if not success:
            # 默認使用main分支
            branch_name = "main"
        else:
            branch_name = branch_output.strip()
    else:
        branch_name = branch_output.strip()
    
    if not branch_name:
        branch_name = "main"  # 如果無法獲取分支名稱，默認使用main
    
    print_colored(f"當前分支: {branch_name}", "yellow")
    
    # 強制推送到GitHub
    print_colored("強制推送到GitHub，將完全覆蓋遠端分支...", "yellow")
    success, output = run_command(["git", "push", "-f", "-u", "origin", branch_name], "無法強制推送到GitHub")
    
    # 如果推送失敗，嘗試使用main或master分支
    if not success:
        if branch_name != "main":
            print_colored("嘗試使用main分支...", "yellow")
            success, output = run_command(["git", "push", "-f", "-u", "origin", "main"], "無法強制推送到GitHub")
        
        if not success and branch_name != "master":
            print_colored("嘗試使用master分支...", "yellow")
            success, _ = run_command(["git", "push", "-f", "-u", "origin", "master"], "無法強制推送到GitHub")
    
    if success:
        print_colored("=" * 50, "green")
        print_colored("成功強制推送到GitHub！", "green")
        print_colored("已完全覆蓋遠端分支", "green")
        print_colored("=" * 50, "green")
    
    return success

def main():
    """主函數"""
    print_colored("=" * 50, "blue")
    print_colored("強制推送腳本", "blue")
    print_colored("=" * 50, "blue")
    
    # 詢問用戶確認
    print_colored("警告: 此操作將完全覆蓋遠端分支，可能導致遠端數據丟失！", "red")
    print_colored("確定要繼續嗎？(y/n)", "yellow")
    
    try:
        response = input().strip().lower()
        if response != 'y' and response != 'yes':
            print_colored("操作已取消", "yellow")
            return True
    except KeyboardInterrupt:
        print_colored("\n操作已取消", "yellow")
        return True
    
    # 執行強制推送
    return force_push_to_github()

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