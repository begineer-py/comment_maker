import logging
import sys

def setup_logging(log_file):
    """設定日誌記錄器，將日誌輸出到控制台和文件。"""
    # 獲取根記錄器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 如果已經有處理器，先移除它們，防止重複記錄
    if logger.hasHandlers():
        logger.handlers.clear()

    # 創建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 創建文件處理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # 創建控制台處理器
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    # 將處理器添加到記錄器
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    print(f"[INFO] 日誌已設定。日誌檔案位於: {log_file}")
