import os
from pathlib import Path
import shutil

class FileScanner:
    """負責掃描文件和複製項目結構。"""

    def __init__(self, src_dir, output_path, filters, recursive):
        """初始化掃描器。

        Args:
            src_dir (Path): 來源目錄。
            output_path (Path): 輸出目錄。
            filters (list): 文件過濾器列表 (例如, ['*.py', '*.js'])。
            recursive (bool): 是否遞歸掃描子目錄。
        """
        self.src_dir = src_dir
        self.output_path = output_path
        self.filters = filters
        self.recursive = recursive

    def scan_and_copy(self):
        """執行掃描和複製操作。

        首先，它會將源目錄的結構複製到目標目錄。
        然後，它會掃描源目錄以查找與過濾器匹配的文件。

        Returns:
            list[tuple[Path, Path]]: 一個元組列表，其中每個元組包含
                                     (源文件路徑, 目標文件路徑)。
        """
        self._copy_project_structure()
        return self._scan_files()

    def _copy_project_structure(self):
        """將源目錄結構複製到輸出目錄，忽略文件。"""
        if self.output_path.exists():
            shutil.rmtree(self.output_path)
        shutil.copytree(self.src_dir, self.output_path, ignore=shutil.ignore_patterns('*.*'), dirs_exist_ok=True)

    def _scan_files(self):
        """掃描源目錄以查找匹配的文件。"""
        files_to_process = []
        if self.recursive:
            path_iterator = self.src_dir.rglob('*')
        else:
            path_iterator = self.src_dir.glob('*')

        for path in path_iterator:
            if path.is_file():
                if any(path.match(p) for p in self.filters):
                    # 計算相對路徑以構建目標路徑
                    relative_path = path.relative_to(self.src_dir)
                    destination_path = self.output_path / relative_path
                    files_to_process.append((path, destination_path))
        return files_to_process
