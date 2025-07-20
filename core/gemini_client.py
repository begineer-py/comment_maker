import os
from config.config import Config
from config.config import PromptConfig
import google.generativeai as genai
import requests
import random
import re
import time
import json


class SendCode:
    def __init__(self, api_key=None, model=None, nyaproxy=False):
        self.model_name = model or Config.DEFAULT_MODEL_NAME
        self.max_retries = Config.DEFAULT_MAX_RETRIES
        self.max_backoff = Config.DEFAULT_MAX_BACKOFF
        self.api_key = api_key or Config.DEFAULT_API_KEY
        self.nyaproxy = nyaproxy

        if not self.nyaproxy:
            genai.configure(api_key=self.api_key)
            self.gemini_model = genai.GenerativeModel(self.model_name)

    # 新增的輔助函數，用於處理模型返回的 JSON 響應
    def _extract_commented_code_from_response(self, response_content):
        # 首先移除最外層的 ```json 和 ```
        if response_content.startswith("```json") and response_content.endswith("```"):
            json_string = response_content[len("```json\n") : -3].strip()
        else:
            # 如果不是預期的格式，則直接使用原始內容（可能需要進一步處理或報錯）
            print("[WARNING] 模型返回的內容不是預期的 ```json 格式")
            return response_content

        try:
            # 解析內部 JSON
            parsed_response = json.loads(json_string)
            # 從解析後的 JSON 中提取 'code' 字段
            if "code" in parsed_response:
                return parsed_response["code"]
            else:
                print("[WARNING] 解析後的 JSON 中未找到 'code' 字段")
                return json_string  # 回退到原始 JSON 字符串
        except json.JSONDecodeError as e:
            print(f"[ERROR] 解析模型返回的 JSON 失敗: {e}")
            return json_string  # 解析失敗，回退到原始 JSON 字符串

    def generate_comments_for_code(
        self,
        code,
        file_path,
    ):
        """使用Gemini API為代碼生成逐行註釋

        Args:
            code: 代碼內容
            file_path: 文件路徑

        Returns:
            str: 添加註釋後的代碼
        """
        # 獲取文件名
        file_name = os.path.basename(file_path)

        # 獲取提示詞，並添加文件名信息
        prompt = PromptConfig.get_prompt(code, file_name)

        if not self.nyaproxy:
            try:
                for attempt in range(self.max_retries):
                    try:
                        response = self.gemini_model.generate_content(prompt)

                        # 檢查響應是否為空
                        if (
                            not response
                            or not hasattr(response, "text")
                            or not response.text
                        ):
                            print(
                                f"[WARNING] API返回空響應 (嘗試 {attempt+1}/{self.max_retries})"
                            )
                            if attempt < self.max_retries - 1:
                                wait_time = min(
                                    (2**attempt) + random.random(), self.max_backoff
                                )
                                print(f"[INFO] 等待 {wait_time:.2f} 秒後重試...")
                                time.sleep(wait_time)
                                continue
                            else:
                                print("[ERROR] 多次嘗試後API仍返回空響應，返回原始代碼")
                                return code

                        commented_code = self._extract_commented_code_from_response(
                            response.text
                        )

                        # 檢查註釋後的代碼是否為空
                        if not commented_code or commented_code.strip() == "":
                            print("[WARNING] 生成的註釋代碼為空，重試...")
                            if attempt < self.max_retries - 1:
                                wait_time = min(
                                    (2**attempt) + random.random(), self.max_backoff
                                )
                                print(f"[INFO] 等待 {wait_time:.2f} 秒後重試...")
                                time.sleep(wait_time)
                                continue
                            else:
                                print(
                                    "[ERROR] 多次嘗試後生成的註釋代碼仍為空，返回原始代碼"
                                )
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
                            if attempt < self.max_retries - 1:
                                wait_time = min(
                                    (2**attempt) * 10 + random.uniform(0, 5),
                                    self.max_backoff,
                                )
                                print(
                                    f"[WARNING] 檢測到API配額限制，等待 {wait_time:.2f} 秒後重試..."
                                )
                                time.sleep(wait_time)
                                continue
                            else:
                                print(
                                    "[ERROR] 多次嘗試後仍然遇到API配額限制，返回原始代碼"
                                )
                                return code

                        # 其他錯誤，如果還有重試次數，則等待後重試
                        if attempt < self.max_retries - 1:
                            wait_time = min(
                                (2**attempt) + random.random(), self.max_backoff
                            )
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
        else:
            # 使用nyaproxy 代理
            try:
                print(f"[INFO] 使用nyaproxy 代理")
                response = requests.post(
                    f"http://localhost:{Config.nyaproxy_port}/api/gemini/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=120,
                )
                response.raise_for_status()

                json_response = response.json()
                print(
                    f"[DEBUG] 從 nyaproxy 接收到的原始響應: {json_response}"
                )  # 新增的打印語句

                if "choices" in json_response and len(json_response["choices"]) > 0:
                    raw_content = json_response["choices"][0]["message"]["content"]
                    commented_code = self._extract_commented_code_from_response(
                        raw_content
                    )
                    return commented_code
                else:
                    print(
                        "[ERROR] nyaproxy 返回的響應中沒有 'choices' 或 'message' 字段"
                    )
                    return code

            except requests.exceptions.RequestException as e:
                print(f"[ERROR] 通過 nyaproxy 發送請求時出錯: {e}")
                return code
            except json.JSONDecodeError as e:
                print(f"[ERROR] 解碼 nyaproxy 響應時出錯: {e}")
                return code
