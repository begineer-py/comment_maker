import logging
from pathlib import Path

class FileProcessor:
    """
    負責處理單一文件：讀取、呼叫API以取得註解，並寫入結果。
    """

    def __init__(self, api_client):
        """
        初始化檔案處理器。

        Args:
            api_client: 用於與 Gemini API 通訊的客戶端實例。
        """
        self.api_client = api_client

    def process(self, src_path: Path, dest_path: Path):
        """
        處理單一文件。

        Args:
            src_path (Path): 來源檔案的路徑。
            dest_path (Path): 目標檔案的路徑。

        Returns:
            bool: 如果處理成功則返回 True，否則返回 False。
        """
        try:
            logging.info(f"正在處理文件: {src_path}")
            code_content = src_path.read_text(encoding='utf-8')

            # 如果文件為空，直接複製並跳過
            if not code_content.strip():
                logging.info(f"文件 {src_path} 為空，直接複製。")
                # 確保目標目錄存在
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_text("", encoding='utf-8')
                return True

            # 呼叫 API 產生註解
            commented_code = self.api_client.generate_comments_for_code(
                code=code_content, file_path=str(src_path)
            )

            if commented_code:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                dest_path.write_text(commented_code, encoding='utf-8')
                logging.info(f"成功處理並儲存文件到: {dest_path}")
                return True
            else:
                logging.error(f"從 API 未能獲取文件 {src_path} 的註解。")
                return False

        except Exception as e:
            logging.error(f"處理文件 {src_path} 時發生錯誤: {e}")
            return False
