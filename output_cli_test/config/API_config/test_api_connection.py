import os
import requests
import google.generativeai as genai
from requests.exceptions import RequestException
from config.config import Config


class TestApiConnection:
    def __init__(self, api_key, nyaproxy):
        self.api_key = api_key
        self.nyaproxy = nyaproxy
        self.model_name = Config.DEFAULT_MODEL_NAME

    def test_api_connection(self):
        try:
            if not self.nyaproxy:
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content("Hello, how are you?")
                return True
            else:
                response = requests.post(
                    f"http://localhost:{Config.nyaproxy_port}/api/gemini/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_name,
                        "messages": [
                            {"role": "user", "content": "Hello, how are you?"}
                        ],
                    },
                    timeout=120,
                )
                response.raise_for_status()
                return True
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] 連接失敗 請求無法到達: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] 連接失敗 未知原因: {e}")
            return False
