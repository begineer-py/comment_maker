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

# 環境變數名稱
API_KEY_ENV_NAME = "GEMINI_API_KEY"

# 不再使用硬編碼的默認API密鑰
print(f"[INFO] API金鑰將從環境變數 {API_KEY_ENV_NAME} 中讀取")

def get_api_key():
    """從系統環境變數中獲取API金鑰
    
    Returns:
        str: API金鑰，如果未找到則返回None
    """
    # 打印所有環境變數（詳細版本）
    print("\n" + "="*50)
    print("[DEBUG] 當前所有環境變數 (詳細):")
    for key, value in sorted(os.environ.items()):
        if "API" in key or "KEY" in key or "TOKEN" in key or "SECRET" in key:
            masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            print(f"  - {key}: {masked_value} (長度: {len(value)})")
        else:
            # 只打印關鍵環境變數，避免輸出過多
            if "PATH" in key or "PYTHON" in key or "HOME" in key or "USER" in key:
                print(f"  - {key}: {value}")
    print("="*50)
    
    # 檢查環境變數
    api_key = os.environ.get(API_KEY_ENV_NAME)
    
    # 如果環境變數中沒有API金鑰，返回None並提示用戶
    if not api_key:
        print(f"[WARNING] 未在環境變數中找到API金鑰 {API_KEY_ENV_NAME}")
        print(f"[INFO] 請設置環境變數: {API_KEY_ENV_NAME}=your_api_key_here")
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
    if not api_key or api_key == "your_gemini_api_key_here" or api_key == "your-api-key":
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
        os.environ[API_KEY_ENV_NAME] = api_key
        
        print(f"[INFO] API金鑰已設置為當前環境變數 {API_KEY_ENV_NAME}")
        
        # 驗證是否設置成功
        if os.environ.get(API_KEY_ENV_NAME) == api_key:
            print(f"[INFO] 驗證成功: 環境變數已正確設置")
        else:
            print(f"[WARNING] 驗證失敗: 環境變數設置可能不成功")
        
        # 提示用戶如何永久保存環境變數
        print(f"[INFO] 注意：此設置僅對當前程序有效")
        print(f"[INFO] 要永久保存環境變數，請按照以下步驟操作：")
        if sys.platform == 'win32':
            print(f"[INFO] Windows: 系統屬性 -> 環境變數 -> 新建，變數名：{API_KEY_ENV_NAME}，變數值：{api_key}")
            print(f"[INFO] 或者在PowerShell中運行: [System.Environment]::SetEnvironmentVariable('{API_KEY_ENV_NAME}', '{api_key}', 'User')")
        else:
            print(f"[INFO] Linux/macOS: 在~/.bashrc或~/.zshrc中添加：export {API_KEY_ENV_NAME}={api_key}")
        
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
        os.environ[API_KEY_ENV_NAME] = api_key
        
        # 根據不同的操作系統執行不同的命令
        if sys.platform == 'win32':
            # Windows - 使用PowerShell設置用戶級環境變數
            try:
                # 構建PowerShell命令
                ps_command = f'[System.Environment]::SetEnvironmentVariable("{API_KEY_ENV_NAME}", "{api_key}", "User")'
                
                # 執行PowerShell命令
                print(f"[INFO] 執行PowerShell命令設置環境變數...")
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                # 檢查命令執行結果
                if result.returncode == 0:
                    print(f"[INFO] 成功設置系統環境變數 {API_KEY_ENV_NAME}")
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
            # Linux/macOS - 添加到shell配置文件
            try:
                # 確定用戶主目錄
                home_dir = os.path.expanduser("~")
                
                # 檢查常見的shell配置文件
                shell_files = [
                    os.path.join(home_dir, ".bashrc"),
                    os.path.join(home_dir, ".bash_profile"),
                    os.path.join(home_dir, ".zshrc")
                ]
                
                # 找到存在的配置文件
                config_file = None
                for file_path in shell_files:
                    if os.path.exists(file_path):
                        config_file = file_path
                        break
                
                if not config_file:
                    # 如果沒有找到配置文件，默認使用.bashrc
                    config_file = os.path.join(home_dir, ".bashrc")
                    
                # 檢查文件中是否已經有API_KEY_ENV_NAME的設置
                export_line = f'export {API_KEY_ENV_NAME}="{api_key}"'
                has_export = False
                
                if os.path.exists(config_file):
                    with open(config_file, 'r') as f:
                        content = f.read()
                        if f"export {API_KEY_ENV_NAME}=" in content:
                            has_export = True
                
                # 添加或更新環境變數設置
                if has_export:
                    # 使用sed命令更新現有的設置
                    sed_command = f"sed -i 's/export {API_KEY_ENV_NAME}=.*/export {API_KEY_ENV_NAME}=\"{api_key}\"/' {config_file}"
                    result = subprocess.run(sed_command, shell=True, capture_output=True, text=True, check=False)
                    
                    if result.returncode != 0:
                        return False, f"更新環境變數設置失敗: {result.stderr}"
                else:
                    # 添加新的環境變數設置
                    with open(config_file, 'a') as f:
                        f.write(f"\n# Gemini API金鑰\n{export_line}\n")
                
                print(f"[INFO] 成功將API金鑰添加到 {config_file}")
                return True, f"API金鑰已成功添加到 {config_file}，請重新啟動終端或執行 'source {config_file}' 使其生效"
                
            except Exception as e:
                error_msg = f"設置環境變數時出錯: {str(e)}"
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
        print(f"[INFO] 請設置環境變數: {API_KEY_ENV_NAME}=your_api_key_here")
        return None
    
    return api_key

def test_api_connection(api_key=None, model_name="gemini-1.5-pro"):
    """測試API連接
    
    Args:
        api_key: 要測試的API金鑰
        model_name: 要測試的模型名稱
            
    Returns:
        tuple: (bool, str) - 是否連接成功，錯誤信息（如果有）
    """
    if not api_key:
        api_key = ensure_api_key()
        
    if not is_valid_api_key(api_key):
        print(f"[ERROR] API金鑰無效或未設置")
        return False, "API金鑰無效或未設置"
    
    try:
        print(f"[INFO] 正在測試API連接，使用金鑰: {api_key[:4]}...{api_key[-4:]} (長度: {len(api_key)})")
        
        # 導入Google Generative AI庫
        import google.generativeai as genai
        
        # 配置API
        genai.configure(api_key=api_key)
        
        # 創建模型實例
        model = genai.GenerativeModel(model_name)
        
        # 測試API連接
        print(f"[INFO] 發送測試請求到 {model_name} 模型...")
        response = model.generate_content("Hello")
        
        # 檢查響應
        if response and hasattr(response, 'text'):
            print(f"[INFO] 成功連接到 {model_name} 模型，響應: {response.text[:20]}...")
            return True, ""
        else:
            print(f"[ERROR] API返回空響應: {response}")
            return False, "API返回空響應"
                
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] 連接到 {model_name} 模型時出錯: {error_msg}")
        
        # 檢查是否是API金鑰問題
        if "API key" in error_msg or "authentication" in error_msg.lower() or "invalid" in error_msg.lower():
            print(f"[ERROR] API金鑰問題: {error_msg}")
            return False, f"API金鑰無效或未授權: {error_msg}"
        
        return False, error_msg

# 命令行測試
if __name__ == "__main__":
    print("API金鑰管理器測試")
    
    # 獲取API金鑰
    api_key = get_api_key()
    
    if api_key and is_valid_api_key(api_key):
        print(f"API金鑰: {api_key[:4]}...{api_key[-4:]} (長度: {len(api_key)})")
        
        # 測試保存API金鑰
        print("\n測試保存API金鑰到當前進程環境變數:")
        save_api_key(api_key)
        
        # 測試API連接
        print("\n測試API連接:")
        success, error = test_api_connection(api_key)
        if success:
            print("API連接測試成功")
        else:
            print(f"API連接測試失敗: {error}")
    else:
        print("未能獲取有效的API金鑰")
        print(f"請設置環境變數 {API_KEY_ENV_NAME}=your_api_key_here")
        print(f"Windows PowerShell: $env:{API_KEY_ENV_NAME} = 'your_api_key_here'")
        print(f"Windows CMD: set {API_KEY_ENV_NAME}=your_api_key_here")
        print(f"Linux/macOS: export {API_KEY_ENV_NAME}=your_api_key_here") 