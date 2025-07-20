class FileLoadError(Exception):
    """檔案載入或讀取時發生錯誤。"""

    pass


class ConfigFormatError(Exception):
    """設定檔格式不符合預期。"""

    pass
