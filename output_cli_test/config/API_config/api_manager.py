#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API金鑰管理模組
負責Gemini API金鑰的檢查、獲取和保存
從環境變數中讀取API金鑰
"""

import os
import sys
import subprocess
import re

# 環境變數名稱
from config.config import Config

# Use Config.Config.API_KEY_ENV_NAME instead of local definition
# Config.API_KEY_ENV_NAME = "GEMINI_API_KEY" # Original line, now commented out

# 不再使用硬編碼的默認API密鑰
print(f"[INFO] API金鑰將從環境變數 {Config.API_KEY_ENV_NAME} 中讀取")


def get_api_key():
    """從系統環境變數中獲取API金鑰

    Returns:
        str: API金鑰，如果未找到則返回None
    """
    # 打印所有環境變數（詳細版本）
    print("\n" + "=" * 50)
    print("[DEBUG] 當前所有環境變數 (詳細):")
    for key, value in sorted(os.environ.items()):
        if "API" in key or "KEY" in key or "TOKEN" in key or "SECRET" in key:
            masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            print(f"  - {key}: {masked_value} (長度: {len(value)})")
        else:
            # 只打印關鍵環境變數，避免輸出過多
            if "PATH" in key or "PYTHON" in key or "HOME" in key or "USER" in key:
                print(f"  - {key}: {value}")
    print("=" * 50)

    # 檢查環境變數
    api_key = os.environ.get(Config.API_KEY_ENV_NAME)

    # 如果環境變數中沒有API金鑰，返回None並提示用戶
    if not api_key:
        print(f"[WARNING] 未在環境變數中找到API金鑰 {Config.API_KEY_ENV_NAME}")
        print(f"[INFO] 請設置環境變數: {Config.API_KEY_ENV_NAME}=your_api_key_here")
        return None

    # 打印部分API金鑰信息，保護隱私
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"[INFO] API金鑰: {masked_key} (長度: {len(api_key)})")

    return api_key


def is_valid_api_key(api_key):
    """檢查API金鑰是否有效

    Args:
        api_key: 要檢查的API金鑰

    Returns:
        bool: 如果API金鑰有效則返回True，否則返回False
    """
    if (
        not api_key
        or api_key == "your_gemini_api_key_here"
        or api_key == "your-api-key"
    ):
        return False

    # 簡單檢查API金鑰是否為空或默認值
    return len(api_key.strip()) > 0


def save_api_key(api_key):
    """保存API金鑰到系統環境變數

    Args:
        api_key: 要保存的API金鑰

    Returns:
        bool: 如果保存成功則返回True，否則返回False
    """
    if not api_key:
        print("[ERROR] API金鑰不能為空")
        return False

    try:
        # 設置當前進程的環境變數
        os.environ[Config.API_KEY_ENV_NAME] = api_key

        print(f"[INFO] API金鑰已設置為當前環境變數 {Config.API_KEY_ENV_NAME}")

        # 驗證是否設置成功
        if os.environ.get(Config.API_KEY_ENV_NAME) == api_key:
            print(f"[INFO] 驗證成功: 環境變數已正確設置")
        else:
            print(f"[WARNING] 驗證失敗: 環境變數設置可能不成功")

        # 提示用戶如何永久保存環境變數
        print(f"[INFO] 注意：此設置僅對當前程序有效")
        print(f"[INFO] 要永久保存環境變數，請按照以下步驟操作：")
        if sys.platform == "win32":
            print(
                f"[INFO] Windows: 系統屬性 -> 環境變數 -> 新建，變數名：{Config.API_KEY_ENV_NAME}，變數值：{api_key}"
            )
            print(
                f"[INFO] 或者在PowerShell中運行: [System.Environment]::SetEnvironmentVariable('{Config.API_KEY_ENV_NAME}', '{api_key}', 'User')"
            )
        else:
            print(
                f"[INFO] Linux/macOS: 在~/.bashrc或~/.zshrc中添加：export {Config.API_KEY_ENV_NAME}={api_key}"
            )

        return True

    except Exception as e:
        print(f"[ERROR] 保存API金鑰時出錯: {e}")
        return False


def save_api_key_permanently(api_key):
    """永久保存API金鑰到系統環境變數

    Args:
        api_key: 要保存的API金鑰

    Returns:
        tuple: (bool, str) - 是否保存成功，錯誤信息（如果有）
    """
    if not api_key:
        return False, "API金鑰不能為空"

    try:
        # 首先設置當前進程的環境變數
        os.environ[Config.API_KEY_ENV_NAME] = api_key

        # 根據不同的操作系統執行不同的命令
        if sys.platform == "win32":
            # Windows - 使用PowerShell設置用戶級環境變數
            try:
                # 構建PowerShell命令
                ps_command = f'[System.Environment]::SetEnvironmentVariable("{Config.API_KEY_ENV_NAME}", "{api_key}", "User")'

                # 執行PowerShell命令
                print(f"[INFO] 執行PowerShell命令設置環境變數...")
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                # 檢查命令執行結果
                if result.returncode == 0:
                    print(f"[INFO] 成功設置系統環境變數 {Config.API_KEY_ENV_NAME}")
                    return True, "API金鑰已成功永久保存到系統環境變數"
                else:
                    error_msg = f"PowerShell命令執行失敗: {result.stderr}"
                    print(f"[ERROR] {error_msg}")
                    return False, error_msg

            except Exception as e:
                error_msg = f"執行PowerShell命令時出錯: {str(e)}"
                print(f"[ERROR] {error_msg}")
                return False, error_msg

        else:
            # Linux/macOS - 智能檢測並添加到對應的shell配置文件
            try:
                home_dir = os.path.expanduser("~")
                # 獲取當前的shell環境變數
                shell = os.environ.get('SHELL', '')
                config_file = None

                if 'zsh' in shell:
                    config_file = os.path.join(home_dir, ".zshrc")
                    print("[INFO] 檢測到 Zsh shell, 將使用 .zshrc 文件。")
                elif 'bash' in shell:
                    config_file = os.path.join(home_dir, ".bashrc")
                    print("[INFO] 檢測到 Bash shell, 將使用 .bashrc 文件。")
                else:
                    # 如果無法檢測到，提供一個備選方案或默認值
                    config_file = os.path.join(home_dir, ".profile")
                    print(f"[WARNING] 未能明確檢測到 shell 類型 ('{shell}'), 將默認使用 .profile 文件。")

                # 確保文件存在，如果不存在則創建它
                if not os.path.exists(config_file):
                    print(f"[INFO] 配置文件 {config_file} 不存在，將創建新文件。")
                    open(config_file, 'a').close()

                export_line = f'export {Config.API_KEY_ENV_NAME}="{api_key}"'
                
                with open(config_file, "r") as f:
                    content = f.read()

                # 使用正則表達式來查找和替換，更穩健
                env_var_pattern = re.compile(f"^\s*export\s+{re.escape(Config.API_KEY_ENV_NAME)}=.*$", re.MULTILINE)
                
                if env_var_pattern.search(content):
                    # 如果找到了，就替換它
                    print(f"[INFO] 在 {config_file} 中找到現有設置，將其更新。")
                    new_content = env_var_pattern.sub(export_line, content)
                else:
                    # 如果沒找到，就在文件末尾追加
                    print(f"[INFO] 在 {config_file} 中未找到現有設置，將添加新設置。")
                    # 確保在添加前有換行符
                    if content.strip() == '':
                        new_content = f"# Gemini API Key added by script\n{export_line}\n"
                    else:
                        new_content = content.strip() + f"\n\n# Gemini API Key added by script\n{export_line}\n"

                with open(config_file, "w") as f:
                    f.write(new_content)

                config_filename = os.path.basename(config_file)
                print(f"[INFO] 成功將API金鑰寫入到 {config_file}")
                return (
                    True,
                    f"API金鑰已成功寫入到 {config_filename}。\n請重新啟動終端或執行 'source {config_file}' 使其生效。",
                )

            except Exception as e:
                error_msg = f"在Linux/macOS上設置環境變數時出錯: {str(e)}"
                print(f"[ERROR] {error_msg}")
                return False, error_msg

    except Exception as e:
        error_msg = f"保存API金鑰時出錯: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg


def ensure_api_key():
    """確保有有效的API金鑰

    Returns:
        str: API金鑰，如果無法獲取有效的API金鑰則返回None
    """
    # 嘗試獲取API金鑰
    api_key = get_api_key()

    # 檢查API金鑰是否有效
    if not is_valid_api_key(api_key):
        print(f"[ERROR] API金鑰無效或未設置")
        print(f"[INFO] 請設置環境變數: {Config.API_KEY_ENV_NAME}=your_api_key_here")
        return None

    return api_key
