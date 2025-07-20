import os
import yaml
import logging
from exceptions.exceptions import FileLoadError, ConfigFormatError

# 設定日誌（你可以根據自己的需求調整）
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(message)s",
    filename="test.log",
    filemode="w",
)


def exclude_patterns():
    """
    載入並合併排除檔案與資料夾的模式。
    包含 config/exclude.yaml 的設定與 .gitignore 的內容。
    遇到錯誤會拋出具體的異常，而不是回傳 False 或只 print。
    """
    combined_patterns = []

    # --- 處理 config/exclude.yaml (獨立 try 區塊) ---
    exclude_yaml_path = "config/exclude.yaml"
    try:
        with open(exclude_yaml_path, "r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f)

            if (
                isinstance(yaml_config, dict)
                and "exclude" in yaml_config
                and isinstance(yaml_config["exclude"], list)
            ):
                combined_patterns.extend(yaml_config["exclude"])
            else:
                # 格式錯誤，發出警告並拋出 ConfigFormatError
                logging.warning(
                    f"'{exclude_yaml_path}' 檔案格式不符合預期，已忽略其內容。"
                )
                raise ConfigFormatError(
                    f"排除設定檔 '{exclude_yaml_path}' 格式錯誤: 內容不符合預期結構。"
                )

    except FileNotFoundError:
        # 檔案不存在，記錄 info 級別，不拋出致命錯誤，因為可以沒有
        logging.info(f"'{exclude_yaml_path}' 檔案不存在，將不會載入自訂排除規則。")
    except yaml.YAMLError as e:
        # YAML 解析錯誤，拋出 ConfigFormatError
        logging.error(f"解析 '{exclude_yaml_path}' 失敗，請檢查檔案格式！錯誤訊息：{e}")
        raise ConfigFormatError(
            f"排除設定檔 '{exclude_yaml_path}' 解析失敗: {e}"
        ) from e
    except Exception as e:
        # 捕捉其他讀取時的未知錯誤
        logging.error(f"讀取 '{exclude_yaml_path}' 時發生未知錯誤：{e}")
        raise FileLoadError(f"讀取 '{exclude_yaml_path}' 時發生未知錯誤: {e}") from e

    # --- 處理 .gitignore (獨立 try 區塊) ---
    gitignore_path = ".gitignore"
    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("#"):
                    combined_patterns.append(stripped_line)
    except FileNotFoundError:
        # .gitignore 不存在，記錄 info 級別
        logging.info(f"'{gitignore_path}' 檔案不存在，將不會載入 .gitignore 排除規則。")
    except Exception as e:
        # 捕捉其他讀取時的未知錯誤
        logging.error(f"讀取 '{gitignore_path}' 時發生未知錯誤：{e}")
        raise FileLoadError(f"讀取 '{gitignore_path}' 時發生未知錯誤: {e}") from e

    # --- 去除重複的模式 ---
    final_patterns = list(set(combined_patterns))

    return final_patterns


def save_exclude_patterns(patterns):
    """
    將排除模式保存到 config/exclude.yaml。
    """
    exclude_yaml_path = "config/exclude.yaml"
    try:
        with open(exclude_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(
                {"exclude": patterns}, f, allow_unicode=True, default_flow_style=False
            )
        logging.info(f"排除模式已成功保存到 '{exclude_yaml_path}'。")
    except Exception as e:
        logging.error(f"保存排除模式到 '{exclude_yaml_path}' 失敗：{e}")
        raise FileLoadError(f"保存排除模式到 '{exclude_yaml_path}' 失敗: {e}") from e


if __name__ == "__main__":
    print("執行測試")
    # 測試讀取
    patterns = exclude_patterns()
    print("讀取測試完成，模式：", patterns)

    # 測試寫入
    test_patterns = [".venv", ".git", "new_folder/", "*.log"]
    try:
        save_exclude_patterns(test_patterns)
        print("寫入測試完成。")
        # 再次讀取以確認寫入成功
        reloaded_patterns = exclude_patterns()
        print("重新讀取確認，模式：", reloaded_patterns)
        assert sorted(reloaded_patterns) == sorted(
            list(set(test_patterns + [".venv", ".git"]))
        ), "寫入後讀取不一致"
    except Exception as e:
        print(f"寫入測試失敗: {e}")
