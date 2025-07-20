import os


class Config:
    API_KEY_ENV_NAME = "GEMINI_API_KEY"
    DEFAULT_FILE_FILTER = "*.py"
    DEFAULT_REQUEST_DELAY = 6.0
    DEFAULT_MAX_BACKOFF = 64.0
    DEFAULT_MODEL_NAME = "gemini-2.5-flash"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_API_KEY = os.getenv("GEMINI_API_KEY")  # 從環境變數中讀取API金鑰
    nyaproxy_port = 8500


class PromptConfig:
    def get_prompt(code, file_name=None):
        """

        Args:
            code: 代碼內容
            file_name: 文件名

        Returns:
            str: 提示詞
        """
        # 添加文件名信息
        file_info = ""
        if file_name:
            file_info = f"文件名: {file_name}\n"

        return f"""你是一位專業的代碼註釋專家，精通各種程式語言。
    {file_info}
    請為以下代碼的每一行添加簡潔明了的中文註釋。註釋應該放在每行代碼的末尾。
    請根據代碼自動判斷程式語言，並使用該語言的正確註釋符號。
    註釋應該解釋代碼的功能和目的，而不僅僅是翻譯代碼。
    對於空行或者已經有註釋的行，請保持原樣。
    對於較長的代碼行，請確保註釋簡潔，不要使行變得過長。

    請遵循以下格式規則：
    1. 自動識別代碼語言，並使用適當的註釋符號（如Python使用#，JavaScript使用//等）
    2. 在代碼行末尾添加註釋，格式為"代碼 # 註釋"（根據語言使用相應的註釋符號）千萬不要使用'''格式
    3. 保持原始代碼的縮進和格式
    4. 不要修改原始代碼,就算你認爲需要修改 或是無用的代碼
    5. 不要添加額外的解釋或說明，只返回帶註釋的代碼
    6. 對於複雜的函數或類，可以在定義行添加簡短的功能說明
    7. 請以json格式返回 把代碼放在code字段 {{"code": "代碼"}}

    以下是需要添加註釋的代碼：

    ```
    {code}
    ```

    請直接返回帶有行尾註釋的完整代碼，不要有任何額外的解釋。"""
