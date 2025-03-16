#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
設置自動推送定時任務
用於設置定期自動推送到GitHub的定時任務
"""

import os
import sys
import platform
import subprocess
import datetime

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

def setup_windows_task():
    """設置Windows計劃任務"""
    print_colored("設置Windows計劃任務...", "yellow")
    
    # 獲取當前腳本的絕對路徑
    current_dir = os.path.abspath(os.path.dirname(__file__))
    auto_push_bat = os.path.join(current_dir, "auto_push.bat")
    
    # 創建計劃任務XML文件
    task_name = "GithubAutoPush"
    xml_path = os.path.join(current_dir, "github_auto_push.xml")
    
    # 獲取當前用戶名
    username = os.environ.get("USERNAME")
    
    # 創建XML內容
    xml_content = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</Date>
    <Author>{username}</Author>
    <Description>自動推送代碼到GitHub</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{auto_push_bat}</Command>
      <WorkingDirectory>{current_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""
    
    # 寫入XML文件
    with open(xml_path, "w", encoding="utf-16") as f:
        f.write(xml_content)
    
    # 創建計劃任務
    success, _ = run_command(["schtasks", "/create", "/tn", task_name, "/xml", xml_path], "無法創建計劃任務")
    
    # 刪除臨時XML文件
    if os.path.exists(xml_path):
        os.remove(xml_path)
    
    if success:
        print_colored("Windows計劃任務設置成功！", "green")
        print_colored(f"任務名稱: {task_name}", "green")
        print_colored("每天將自動運行一次", "green")
    
    return success

def setup_linux_cron():
    """設置Linux crontab"""
    print_colored("設置Linux crontab...", "yellow")
    
    # 獲取當前腳本的絕對路徑
    current_dir = os.path.abspath(os.path.dirname(__file__))
    auto_push_sh = os.path.join(current_dir, "auto_push.sh")
    
    # 確保腳本有執行權限
    os.chmod(auto_push_sh, 0o755)
    
    # 獲取當前的crontab
    success, output = run_command(["crontab", "-l"], "無法獲取當前crontab")
    
    # 如果沒有crontab或出錯，使用空字符串
    if not success:
        current_crontab = ""
    else:
        current_crontab = output
    
    # 創建新的crontab條目（每天凌晨2點運行）
    cron_job = f"0 2 * * * {auto_push_sh} >> {os.path.join(current_dir, 'auto_push.log')} 2>&1\n"
    
    # 檢查是否已經存在相同的條目
    if cron_job in current_crontab:
        print_colored("crontab條目已存在，無需添加", "yellow")
        return True
    
    # 添加新的條目
    new_crontab = current_crontab + cron_job
    
    # 寫入臨時文件
    temp_file = os.path.join(current_dir, "temp_crontab")
    with open(temp_file, "w") as f:
        f.write(new_crontab)
    
    # 設置新的crontab
    success, _ = run_command(["crontab", temp_file], "無法設置crontab")
    
    # 刪除臨時文件
    if os.path.exists(temp_file):
        os.remove(temp_file)
    
    if success:
        print_colored("Linux crontab設置成功！", "green")
        print_colored("每天凌晨2點將自動運行", "green")
    
    return success

def setup_macos_launchd():
    """設置macOS launchd"""
    print_colored("設置macOS launchd...", "yellow")
    
    # 獲取當前腳本的絕對路徑
    current_dir = os.path.abspath(os.path.dirname(__file__))
    auto_push_sh = os.path.join(current_dir, "auto_push.sh")
    
    # 確保腳本有執行權限
    os.chmod(auto_push_sh, 0o755)
    
    # 創建plist文件
    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.github.autopush.plist")
    plist_dir = os.path.dirname(plist_path)
    
    # 確保目錄存在
    if not os.path.exists(plist_dir):
        os.makedirs(plist_dir)
    
    # 創建plist內容
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.github.autopush</string>
    <key>ProgramArguments</key>
    <array>
        <string>{auto_push_sh}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{os.path.join(current_dir, 'auto_push.log')}</string>
    <key>StandardErrorPath</key>
    <string>{os.path.join(current_dir, 'auto_push.log')}</string>
    <key>WorkingDirectory</key>
    <string>{current_dir}</string>
</dict>
</plist>
"""
    
    # 寫入plist文件
    with open(plist_path, "w") as f:
        f.write(plist_content)
    
    # 加載plist
    success, _ = run_command(["launchctl", "load", plist_path], "無法加載launchd配置")
    
    if success:
        print_colored("macOS launchd設置成功！", "green")
        print_colored("每天凌晨2點將自動運行", "green")
    
    return success

def main():
    """主函數"""
    print_colored("=" * 50, "blue")
    print_colored("設置自動推送到GitHub的定時任務", "blue")
    print_colored("=" * 50, "blue")
    
    # 檢測操作系統
    system = platform.system()
    print_colored(f"檢測到操作系統: {system}", "yellow")
    
    if system == "Windows":
        setup_windows_task()
    elif system == "Linux":
        setup_linux_cron()
    elif system == "Darwin":  # macOS
        setup_macos_launchd()
    else:
        print_colored(f"不支持的操作系統: {system}", "red")
        return False
    
    print_colored("=" * 50, "green")
    print_colored("設置完成！", "green")
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