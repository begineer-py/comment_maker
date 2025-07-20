import logging
import time
from pathlib import Path

from core.file_scanner import FileScanner
from core.file_processor import FileProcessor
from core.gemini_client import SendCode
from config.API_config.test_api_connection import TestApiConnection
from config.log_config import setup_logging

class ProjectOrchestrator:
    """協調整個項目處理流程，包括掃描、處理和進度報告。"""

    def __init__(self, settings, progress_queue=None):
        self.settings = settings
        self.progress_queue = progress_queue
        self.api_client = None

    def run(self):
        """執行主協調流程。"""
        try:
            self._setup_logging()
            self._log("協調器開始運行...")

            if not self._setup_api_client():
                self._log("API 客戶端初始化失敗，終止處理。", is_error=True)
                return

            scanner = FileScanner(
                src_dir=Path(self.settings.get("folder")),
                output_path=Path(self.settings.get("output")),
                filters=[f.strip() for f in self.settings.get("file_filter", "").split(",") if f.strip()],
                recursive=self.settings.get("recursive", False)
            )

            self._log("開始掃描文件和複製項目結構...")
            files_to_process = scanner.scan_and_copy()
            total_files = len(files_to_process)
            self._log(f"掃描完成，共找到 {total_files} 個文件需要處理。")

            processor = FileProcessor(self.api_client)
            processed_files = 0

            for src_path, dest_path in files_to_process:
                if processor.process(src_path, dest_path):
                    # 處理成功
                    pass
                else:
                    # 處理失敗
                    self._log(f"處理文件 {src_path} 失敗。", is_error=True)
                
                processed_files += 1
                progress = int((processed_files / total_files) * 100)
                self._update_progress(progress, f"進度: {processed_files}/{total_files}")
                time.sleep(self.settings.get("delay", 1))

            self._log("所有文件處理完成。")
            self._update_progress(100, "處理完成")

        except Exception as e:
            self._log(f"協調過程中發生未預期的錯誤: {e}", is_error=True)
            self._update_progress(100, f"錯誤: {e}")

    def _setup_logging(self):
        output_path = Path(self.settings.get("output"))
        output_path.mkdir(parents=True, exist_ok=True)
        log_file = output_path / "commenter.log"
        setup_logging(log_file)

    def _setup_api_client(self):
        api_key = self.settings.get("api_key")
        max_retries = 5
        for attempt in range(max_retries):
            try:
                tester = TestApiConnection(
                    api_key=api_key,
                    nyaproxy=self.settings.get("use_nyaproxy", False)
                )
                if tester.test_api_connection():
                    self._log("API 連線成功。")
                    self.api_client = SendCode(
                        api_key=api_key,
                        model=self.settings.get("model_name"),
                        nyaproxy=self.settings.get("use_nyaproxy", False)
                    )
                    return True
            except Exception as e:
                self._log(f"API 連線失敗: {e}", is_error=True)
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self._log(f"將在 {wait_time} 秒後重試...")
                    time.sleep(wait_time)
        self._log("API 連線失敗: 多次重試後仍無法連接到 API。", is_error=True)
        return False

    def _log(self, message, is_error=False):
        if is_error:
            logging.error(message)
        else:
            logging.info(message)
        if self.progress_queue:
            log_level = "ERROR" if is_error else "INFO"
            self.progress_queue.put(f"LOG:{log_level}:{message}")

    def _update_progress(self, progress, message):
        if self.progress_queue:
            self.progress_queue.put(f"PROGRESS:{progress}:{message}")
