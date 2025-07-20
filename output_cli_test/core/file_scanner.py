import shutil
import fnmatch
from config.exclude_file import exclude_patterns
import logging
import os


class FileScanner:
    """負責掃描文件和複製項目結構，並處理排除規則。"""

    def __init__(self, src_dir, output_path, filters, recursive, exclude_patterns=None):
        """初始化掃描器。

        Args:
            src_dir (Path): 來源目錄。
            output_path (Path): 輸出目錄。
            filters (list): 文件包含過濾器列表 (例如, ['*.py', '*.js'])。
            recursive (bool): 是否遞歸掃描子目錄。
            exclude_patterns (list, optional): 要排除的模式列表。如果為 None，則從 config/exclude_file.py 載入。
        """
        self.src_dir = src_dir
        self.output_path = output_path
        self.filters = filters
        self.recursive = recursive
        self.excludes = exclude_patterns if exclude_patterns is not None else []
        if not self.excludes:  # 如果傳入的為空或 None，則從文件載入
            from config.exclude_file import exclude_patterns as load_exclude_patterns

            self.excludes = load_exclude_patterns()

    def scan_and_copy(self):
        """執行掃描和複製操作。"""
        self._copy_project_structure()
        return self._scan_files()

    def _copy_project_structure(self):
        """將源目錄結構複製到輸出目錄，同時考慮排除規則。"""
        if self.output_path.exists():
            shutil.rmtree(self.output_path)

        # 如果有排除規則，則創建一個忽略模式
        ignore_patterns = (
            shutil.ignore_patterns(*self.excludes) if self.excludes else None
        )
        shutil.copytree(
            self.src_dir, self.output_path, ignore=ignore_patterns, dirs_exist_ok=True
        )

    def _scan_files(self):
        """掃描源目錄以查找匹配的文件，同時考慮排除規則。"""
        files_to_process = []
        path_iterator = (
            self.src_dir.rglob("*") if self.recursive else self.src_dir.glob("*")
        )

        for path in path_iterator:
            # 檢查路徑是否應被排除
            is_excluded = False
            relative_path = path.relative_to(self.src_dir)
            relative_path_str = str(relative_path)

            logging.info(f"檢查路徑: {relative_path_str}")

            for pattern in self.excludes:
                # 處理以 '/' 結尾的目錄排除模式 (例如 'temp/')
                if pattern.endswith("/"):
                    # 檢查相對路徑是否以該目錄模式開頭
                    if relative_path_str.startswith(pattern):
                        is_excluded = True
                        break
                    # 檢查路徑的任何部分是否是該目錄名 (例如 'temp' 在 'a/temp/b')
                    if path.is_dir() and pattern[:-1] in relative_path.parts:
                        is_excluded = True
                        break
                # 處理文件或資料夾名模式 (例如 '*.log', 'node_modules')
                else:
                    # 檢查文件名或資料夾名是否匹配
                    if fnmatch.fnmatch(path.name, pattern):
                        is_excluded = True
                        break
                    # 檢查整個相對路徑是否匹配 (例如 'src/temp/file.txt' 對應 'src/temp/*.txt')
                    if fnmatch.fnmatch(relative_path_str, pattern):
                        is_excluded = True
                        break
                    # 新增：檢查路徑的任何部分是否是該目錄名 (例如 '.git' 在 '.git/objects/...')
                    if pattern in relative_path.parts:
                        is_excluded = True
                        break
                    # 新增：檢查相對路徑是否以該模式開頭，用於處理像 '.env' 這樣的頂層文件或目錄
                    if (
                        relative_path_str.startswith(pattern + os.sep)
                        or relative_path_str == pattern
                    ):
                        is_excluded = True
                        break

            if is_excluded:
                logging.info(f"路徑 {relative_path_str} 被排除。")
                continue

            # 如果文件符合包含過濾器，則加入待處理列表
            if path.is_file():
                logging.info(f"處理文件: {relative_path_str}")
                logging.info(f"文件名: '{path.name}', 過濾器: {self.filters}")
                match_found = False
                for p in self.filters:
                    if fnmatch.fnmatch(path.name, p):
                        logging.info(f"文件名 '{path.name}' 匹配過濾器 '{p}'。")
                        match_found = True
                        break
                    else:
                        logging.info(f"文件名 '{path.name}' 不匹配過濾器 '{p}'。")

                if match_found:
                    logging.info(f"文件 {relative_path_str} 符合過濾器並被包含。")
                    relative_path = path.relative_to(self.src_dir)
                    destination_path = self.output_path / relative_path
                    files_to_process.append((path, destination_path))
                else:
                    logging.info(f"文件 {relative_path_str} 不符合過濾器。")
            else:
                logging.info(f"路徑 {relative_path_str} 是目錄，不處理。")

        return files_to_process
