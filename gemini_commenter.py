import os
import glob
import re
import argparse
import sys
import time
import random
import google.generativeai as genai

# 導入提示詞模板
from prompts import get_prompt_for_style

# 導入API金鑰管理模組
from api_key_manager import ensure_api_key, test_api_connection

# 設置控制台編碼
try:
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # 設置為UTF-8
except Exception as e:
    print(f"[WARNING] 設置控制台編碼失敗: {e}")


def setup_gemini_api(api_key, model_name="gemini-2.5-flash"):
    """設置Gemini API並返回模型實例"""
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

    # 配置Gemini API
    genai.configure(api_key=api_key)

    # 創建模型實例
    print(f"[INFO] 使用 {model_name} 模型...")
    model = genai.GenerativeModel(model_name)
    return model


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
        "--comment-style",
        type=str,
        choices=["line_end", "line_start"],
        default="line_end",
        help="註釋風格: line_end(行尾註釋)或line_start(行前註釋)",
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


def generate_comments_for_code(
    model, code, file_path, comment_style="line_end", max_retries=5, max_backoff=64
):
    """使用Gemini API為代碼生成逐行註釋

    Args:
        model: Gemini模型實例
        code: 代碼內容
        file_path: 文件路徑
        comment_style: 註釋風格
        max_retries: 最大重試次數
        max_backoff: 最大退避時間

    Returns:
        str: 添加註釋後的代碼
    """
    # 獲取文件名
    file_name = os.path.basename(file_path)
    file_ext = get_file_extension(file_path)

    # 獲取對應風格的提示詞，並添加文件名信息
    prompt = get_prompt_for_style(code, comment_style, file_name)

    try:
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)

                # 檢查響應是否為空
                if not response or not hasattr(response, "text") or not response.text:
                    print(f"[WARNING] API返回空響應 (嘗試 {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        wait_time = min((2**attempt) + random.random(), max_backoff)
                        print(f"[INFO] 等待 {wait_time:.2f} 秒後重試...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("[ERROR] 多次嘗試後API仍返回空響應，返回原始代碼")
                        return code

                commented_code = response.text

                # 提取代碼塊 - 使用通用正則表達式
                code_pattern = r"```.*?\n(.*?)\n```"
                match = re.search(code_pattern, commented_code, re.DOTALL)
                if match:
                    commented_code = match.group(1)
                else:
                    # 如果沒有找到代碼塊，嘗試使用整個響應
                    print("[WARNING] 未找到代碼塊，使用整個響應")

                # 檢查註釋後的代碼是否為空
                if not commented_code or commented_code.strip() == "":
                    print("[WARNING] 生成的註釋代碼為空，重試...")
                    if attempt < max_retries - 1:
                        wait_time = min((2**attempt) + random.random(), max_backoff)
                        print(f"[INFO] 等待 {wait_time:.2f} 秒後重試...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("[ERROR] 多次嘗試後生成的註釋代碼仍為空，返回原始代碼")
                        return code

                return commented_code

            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR] 生成註釋時出錯: {error_msg}")

                # 處理API配額限制錯誤
                if (
                    "429" in error_msg
                    or "quota" in error_msg
                    or "exhausted" in error_msg
                    or "rate limit" in error_msg.lower()
                ):
                    if attempt < max_retries - 1:
                        wait_time = min(
                            (2**attempt) * 10 + random.uniform(0, 5), max_backoff
                        )
                        print(
                            f"[WARNING] 檢測到API配額限制，等待 {wait_time:.2f} 秒後重試..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        print("[ERROR] 多次嘗試後仍然遇到API配額限制，返回原始代碼")
                        return code

                # 其他錯誤，如果還有重試次數，則等待後重試
                if attempt < max_retries - 1:
                    wait_time = min((2**attempt) + random.random(), max_backoff)
                    print(f"[INFO] 等待 {wait_time:.2f} 秒後重試...")
                    time.sleep(wait_time)
                else:
                    print("[ERROR] 多次嘗試後仍然出錯，返回原始代碼")
                    return code

        # 如果所有嘗試都失敗，返回原始代碼
        return code
    except Exception as e:
        print(f"[ERROR] 生成註釋時出錯: {e}")
        return code  # 出錯時返回原始代碼


def process_file(
    model,
    file_path,
    output_folder,
    delay=6.0,
    comment_style="line_end",
    max_backoff=64.0,
):
    """處理單個代碼文件，添加註釋並保存到輸出文件夾

    Args:
        model: Gemini模型實例
        file_path: 文件路徑
        output_folder: 輸出文件夾
        delay: 請求延遲時間
        comment_style: 註釋風格
        max_backoff: 最大退避時間

    Returns:
        bool: 處理是否成功
    """
    try:
        # 獲取文件擴展名
        file_ext = get_file_extension(file_path)
        print(f"[INFO] 處理中: {file_path} (擴展名: {file_ext})")

        # 讀取文件內容 - 增加錯誤處理和多種編碼嘗試
        code = None
        successful_encoding = None
        encodings_to_try = ["utf-8", "cp950", "big5", "gbk", "latin-1"]

        # 對於HTML文件，優先嘗試UTF-8
        if file_ext.lower() in [".html", ".htm"]:
            print(f"[INFO] 檢測到HTML文件，優先嘗試UTF-8編碼")
            encodings_to_try = ["utf-8"] + encodings_to_try

        for encoding in encodings_to_try:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    code = f.read()
                print(f"[INFO] 成功使用 {encoding} 編碼讀取文件")
                successful_encoding = encoding
                break
            except UnicodeDecodeError:
                print(f"[WARNING] 無法使用 {encoding} 編碼讀取文件，嘗試其他編碼...")
            except Exception as e:
                print(f"[ERROR] 讀取文件時出錯 ({encoding}): {e}")

        # 如果所有編碼都失敗，嘗試二進制讀取
        if code is None:
            try:
                print(f"[WARNING] 所有文本編碼嘗試失敗，嘗試二進制讀取...")
                with open(file_path, "rb") as f:
                    binary_data = f.read()
                # 嘗試檢測BOM並解碼
                if binary_data.startswith(b"\xef\xbb\xbf"):  # UTF-8 BOM
                    code = binary_data[3:].decode("utf-8")
                    print(f"[INFO] 檢測到UTF-8 BOM，成功解碼")
                    successful_encoding = "utf-8-sig"  # 使用-sig表示帶BOM的UTF-8
                else:
                    # 最後嘗試使用latin-1（可以解碼任何字節）
                    code = binary_data.decode("latin-1")
                    print(f"[INFO] 使用latin-1編碼成功讀取文件")
                    successful_encoding = "latin-1"
            except Exception as e:
                print(f"[ERROR] 二進制讀取文件失敗: {e}")
                return False

        # 如果仍然無法讀取文件，則退出
        if code is None:
            print(f"[ERROR] 無法讀取文件 {file_path}，跳過處理")
            return False

        # 生成註釋
        commented_code = generate_comments_for_code(
            model,
            code,
            file_path,
            comment_style,
            max_retries=5,
            max_backoff=max_backoff,
        )

        # 確保commented_code不是None
        if commented_code is None:
            print(f"[ERROR] 生成的註釋代碼為None，跳過保存: {file_path}")
            return False

        # 創建輸出文件夾
        os.makedirs(output_folder, exist_ok=True)

        # 確定輸出文件路徑
        rel_path = os.path.relpath(file_path, os.path.dirname(output_folder))
        output_path = os.path.join(output_folder, rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 保存註釋後的代碼 - 使用與讀取相同的編碼
        try:
            # 如果沒有成功的編碼，默認使用utf-8
            if not successful_encoding:
                successful_encoding = "utf-8"

            # 對於HTML文件，強制使用UTF-8編碼保存
            if file_ext.lower() in [".html", ".htm"]:
                print(f"[INFO] HTML文件將使用UTF-8編碼保存")
                successful_encoding = "utf-8"

            # 檢查註釋後的代碼是否可以使用檢測到的編碼進行編碼
            try:
                commented_code.encode(successful_encoding)
            except UnicodeEncodeError:
                print(
                    f"[WARNING] 註釋後的代碼無法使用 {successful_encoding} 編碼，將改用UTF-8"
                )
                successful_encoding = "utf-8"

            print(f"[INFO] 使用 {successful_encoding} 編碼保存文件")

            # 對於HTML文件，添加適當的編碼聲明
            if (
                file_ext.lower() in [".html", ".htm"]
                and "<meta charset=" not in commented_code.lower()
            ):
                # 檢查是否有head標籤
                if "<head>" in commented_code:
                    commented_code = commented_code.replace(
                        "<head>", '<head>\n    <meta charset="UTF-8">'
                    )
                    print(f"[INFO] 已添加UTF-8編碼聲明到HTML文件")

            # 使用檢測到的編碼保存文件
            with open(output_path, "w", encoding=successful_encoding) as f:
                f.write(commented_code)
            print(f"[INFO] 完成: {file_path} -> {output_path}")
        except TypeError as te:
            print(f"[ERROR] 寫入文件時類型錯誤: {te}")
            print(f"[INFO] 嘗試將None轉換為空字符串並保存原始代碼")
            with open(output_path, "w", encoding=successful_encoding) as f:
                f.write(code)  # 保存原始代碼
            print(f"[INFO] 已保存原始代碼: {output_path}")
            return False
        except Exception as e:
            print(f"[ERROR] 保存文件時出錯: {e}")
            print(f"[INFO] 嘗試使用二進制模式保存文件")
            try:
                # 對於HTML文件，確保使用UTF-8編碼
                if file_ext.lower() in [".html", ".htm"]:
                    encoding_to_use = "utf-8"
                else:
                    encoding_to_use = successful_encoding

                with open(output_path, "wb") as f:
                    f.write(commented_code.encode(encoding_to_use, errors="replace"))
                print(f"[INFO] 使用二進制模式成功保存文件 (編碼: {encoding_to_use})")
            except Exception as e2:
                print(f"[ERROR] 二進制保存也失敗: {e2}")
                # 最後嘗試保存原始代碼
                try:
                    with open(output_path, "wb") as f:
                        f.write(code.encode(successful_encoding, errors="replace"))
                    print(f"[INFO] 已保存原始代碼")
                except Exception as e3:
                    print(f"[ERROR] 保存原始代碼也失敗: {e3}")
                    return False

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
    file_filter="*.py",
    model=None,
    delay=6.0,
    max_backoff=64.0,
    comment_style="line_end",
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
        comment_style: 註釋風格

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
    print(
        f"[INFO] 註釋風格: {'行尾註釋' if comment_style == 'line_end' else '行前註釋'}"
    )

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

        if process_file(
            model, file_path, output_folder, delay, comment_style, max_backoff
        ):
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
    model = setup_gemini_api(api_key, args.model)

    # 處理文件夾
    process_folder(
        args.folder,
        args.output,
        args.recursive,
        args.filter,
        model,
        args.delay,
        args.max_backoff,
        args.comment_style,
    )


if __name__ == "__main__":
    main()
