import os
import glob
import re
import argparse
import sys
import time
import random
import google.generativeai as genai

# 導入提示詞模板

from config.config import Config
from config.config import PromptConfig
from file_hander import send_code
from file_hander.send_code import SendCode

# 導入API金鑰管理模組
from api_key_setting.api_key_manager import ensure_api_key
from api_key_setting.test_api_connect import test_api_connection

# 設置控制台編碼
try:
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # 設置為UTF-8
except Exception as e:
    print(f"[WARNING] 設置控制台編碼失敗: {e}")


# 導入訊息打印
def setup_gemini_api(api_key, model_name=Config.DEFAULT_MODEL_NAME, Nayproxy=False):
    """設置Gemini API並返回SendCode實例"""
    if Nayproxy:
        print("[INFO] Nayproxy 已啟用，跳過API金鑰檢查和連接測試。")
        # 直接返回配置好的SendCode實例
        return SendCode(model=model_name, Nayproxy=True)

    # 如果API金鑰為空，嘗試重新獲取
    if not api_key:
        print("[WARNING] API金鑰未提供")
        api_key = ensure_api_key()  # 使用API金鑰管理模組獲取API金鑰

        # 如果仍然為空，則退出
        if not api_key:
            print("[ERROR] 無法獲取有效的API金鑰，程序將退出")
            print("[INFO] 請確保您有一個有效的Gemini API金鑰")
            print("[INFO] 您可以設置系統環境變數: GEMINI_API_KEY=your_api_key_here")
            sys.exit(1)

    # 測試API連接，添加重試機制
    max_retries = 3
    base_wait_time = 10  # 基礎等待時間（秒）

    for attempt in range(max_retries):
        success, error_msg = test_api_connection(api_key, model_name)
        if success:
            break

        print(f"[ERROR] 連接到 {model_name} 模型時出錯: {error_msg}")

        # 如果是API金鑰問題，嘗試重新獲取
        if "API金鑰無效" in error_msg or "未授權" in error_msg:
            print("[INFO] 嘗試重新獲取API金鑰...")
            api_key = ensure_api_key()
            if api_key:
                print("[INFO] 使用新的API金鑰重試...")
                continue

        # 如果是配額限制問題，等待更長時間後重試
        if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
            wait_time = base_wait_time * (2**attempt) + random.uniform(0, 5)
            print(f"[WARNING] 檢測到API配額限制，等待 {wait_time:.2f} 秒後重試...")
            time.sleep(wait_time)
            continue

        # 如果是最後一次嘗試且仍然失敗，則退出
        if attempt == max_retries - 1:
            print(f"[ERROR] 連接到 {model_name} 模型失敗: {error_msg}")
            print("[INFO] 請稍後再試或檢查您的API金鑰")
            sys.exit(1)

    # 返回配置好的SendCode實例
    print(f"[INFO] 使用 {model_name} 模型...")
    return SendCode(api_key=api_key, model=model_name, Nayproxy=False)


def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="使用Gemini AI為代碼文件添加中文註釋")
    parser.add_argument(
        "--folder", "-f", type=str, default=".", help="包含代碼文件的文件夾路徑"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="commented", help="輸出文件夾路徑"
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="是否遞歸處理子文件夾"
    )
    parser.add_argument(
        "--filter", type=str, default="*.py", help="文件過濾器，如: *.py,*.js,*.java"
    )
    parser.add_argument(
        "--delay", "-d", type=float, default=6.0, help="API請求之間的延遲(秒)"
    )
    parser.add_argument(
        "--max-backoff", type=float, default=64.0, help="最大退避時間(秒)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Gemini模型名稱，如: gemini-2.5-flash",
    )
    parser.add_argument(
        "--api-key", type=str, help="Gemini API金鑰，優先級高於環境變數"
    )
    parser.add_argument("--nayproxy", action="store_true", help="是否使用Nayproxy代理")

    return parser.parse_args()


def get_code_files(folder_path, recursive=False, file_filter="*.py"):
    """獲取指定文件夾中的所有代碼文件

    Args:
        folder_path: 文件夾路徑
        recursive: 是否遞歸處理子文件夾
        file_filter: 文件過濾器，支持多個過濾器，用逗號分隔

    Returns:
        list: 符合條件的文件路徑列表
    """
    all_files = []

    # 處理多個文件過濾器
    filters = [f.strip() for f in file_filter.split(",")]

    for filter_pattern in filters:
        pattern = (
            os.path.join(folder_path, "**", filter_pattern)
            if recursive
            else os.path.join(folder_path, filter_pattern)
        )
        files = glob.glob(pattern, recursive=recursive)
        all_files.extend(files)

    return sorted(list(set(all_files)))  # 去重並排序


def get_file_extension(file_path):
    """獲取文件擴展名

    Args:
        file_path: 文件路徑

    Returns:
        str: 文件擴展名（包含點，如.py）
    """
    return os.path.splitext(file_path)[1].lower()


def process_file(
    model,
    file_path,
    input_folder,
    output_folder,
    delay=6.0,
    max_backoff=64.0,
):
    """處理單個代碼文件，添加註釋並保存到輸出文件夾

    Args:
        model: Gemini模型實例
        file_path: 文件路徑
        input_folder: 源文件夾路徑
        output_folder: 輸出文件夾
        delay: 請求延遲時間
        max_backoff: 最大退避時間

    Returns:
        bool: 處理是否成功
    """
    try:
        # 讀取文件內容
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        # 如果文件為空，直接跳過
        if not code.strip():
            print(f"[INFO] 文件為空，跳過: {file_path}")
            return True

        # 獲取文件擴展名
        file_extension = get_file_extension(file_path)

        # 獲取文件名
        file_name = os.path.basename(file_path)

        # 'model' 參數本身就是配置好的 SendCode 實例，直接使用即可
        # 生成註釋
        commented_code = model.generate_comments_for_code(
            code,
            file_path,
        )

        # 如果返回的代碼為空或與原始代碼相同，則視為處理失敗
        if not commented_code or commented_code == code:
            print(f"[WARNING] 未能為文件生成註釋: {file_path}")
            return False

        # 計算相對路徑並構建目標路徑
        relative_path = os.path.relpath(file_path, input_folder)
        output_path = os.path.join(output_folder, relative_path)

        # 確保輸出目標文件夾存在
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        # 保存到輸出文件夾
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(commented_code)

        print(f"[INFO] 完成: {file_path} -> {output_path}")

        # 添加隨機延遲，避免API請求過於規律
        actual_delay = delay + random.uniform(0, 2)
        print(f"[INFO] 等待 {actual_delay:.2f} 秒後進行下一個請求...")
        time.sleep(actual_delay)

        return True
    except Exception as e:
        print(f"[ERROR] 處理文件 {file_path} 時出錯: {e}")
        import traceback

        traceback.print_exc()
        return False


def process_folder(
    folder,
    output_folder,
    recursive=False,
    file_filter=Config.DEFAULT_FILE_FILTER,
    model=None,
    delay=Config.DEFAULT_REQUEST_DELAY,
    max_backoff=Config.DEFAULT_MAX_BACKOFF,
):
    """處理文件夾中的所有代碼文件

    Args:
        folder: 源文件夾路徑
        output_folder: 輸出文件夾路徑
        recursive: 是否遞歸處理子文件夾
        file_filter: 文件過濾器，如: *.py,*.js,*.java
        model: Gemini模型實例
        delay: 請求延遲時間
        max_backoff: 最大退避時間

    Returns:
        tuple: (成功處理的文件數, 總文件數)
    """
    # 獲取代碼文件列表
    code_files = get_code_files(folder, recursive, file_filter)

    if not code_files:
        print(f"[INFO] 未找到匹配 {file_filter} 的文件在 {folder} 中")
        return (0, 0)

    print(f"[INFO] 找到 {len(code_files)} 個文件")
    print(f"[INFO] 速率限制: 使用 {delay} 秒基礎延遲和指數退避算法")
    print(f"[INFO] 註釋風格: 行後註釋")

    # 處理每個文件
    success_count = 0
    total_count = 0

    for file_path in code_files:
        # 跳過輸出文件夾中的文件
        if os.path.abspath(output_folder) in os.path.abspath(file_path):
            continue

        # 跳過當前腳本和API金鑰管理模組
        if (
            os.path.samefile(file_path, __file__)
            or os.path.basename(file_path) == "api_key_manager.py"
        ):
            continue

        total_count += 1
        current_file_num = total_count
        total_files = len(code_files)

        # 獲取文件擴展名
        file_ext = get_file_extension(file_path)
        print(
            f"[INFO] 處理文件 {current_file_num}/{total_files}: {file_path} (擴展名: {file_ext})"
        )

        if process_file(model, file_path, folder, output_folder, delay, max_backoff):
            success_count += 1
            print(f"[INFO] 進度: {success_count}/{total_count} 個文件成功處理")

    print(f"[INFO] 處理完成: {success_count}/{total_count} 個文件成功添加註釋")
    # 添加GUI友好的輸出格式，確保GUI能夠正確解析處理結果
    print(
        f"Processing completed: {success_count}/{total_count} files successfully commented"
    )
    return (success_count, total_count)


def main():
    """主函數"""
    # 解析命令行參數
    args = parse_args()

    # 獲取API金鑰 - 優先使用命令行參數
    api_key = args.api_key
    if not api_key:
        api_key = ensure_api_key()

    # 如果API金鑰為空，則退出
    if not api_key:
        print("[ERROR] 未找到有效的API金鑰，程序將退出")
        print("[INFO] 請確保您有一個有效的Gemini API金鑰")
        print("[INFO] 您可以設置系統環境變數: GEMINI_API_KEY=your_api_key_here")
        print("[INFO] 或者使用--api-key參數直接傳遞API金鑰")
        sys.exit(1)

    # 打印API金鑰信息（部分隱藏）
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"[INFO] 使用API金鑰: {masked_key} (長度: {len(api_key)})")

    # 設置Gemini API
    model = setup_gemini_api(api_key, args.model, args.nayproxy)

    # 處理文件夾
    process_folder(
        args.folder,
        args.output,
        args.recursive,
        args.filter,
        model,
        args.delay,
        args.max_backoff,
    )


if __name__ == "__main__":
    main()
