from api_key_setting.api_key_manager import ensure_api_key

def test_api_connection(api_key=None, model_name="gemini-2.5-flash"):
    """測試API連接

    Args:
        api_key: 要測試的API金鑰
        model_name: 要測試的模型名稱

    Returns:
        tuple: (bool, str) - 是否連接成功，錯誤信息（如果有）
    """
    if not api_key:
        api_key = ensure_api_key()

    if not api_key:
        print(f"[ERROR] API金鑰無效或未設置")
        return False, "API金鑰無效或未設置"

    try:
        print(
            f"[INFO] 正在測試API連接，使用金鑰: {api_key[:4]}...{api_key[-4:]} (長度: {len(api_key)})"
        )

        # 導入Google Generative AI庫
        import google.generativeai as genai

        # 配置API
        genai.configure(api_key=api_key)

        # 創建模型實例
        model = genai.GenerativeModel(model_name)

        # 測試API連接
        print(f"[INFO] 發送測試請求到 {model_name} 模型...")
        response = model.generate_content("Hello")

        # 檢查響應
        if response and hasattr(response, "text"):
            print(f"[INFO] 成功連接到 {model_name} 模型，響應: {response.text[:20]}...")
            return True, ""
        else:
            print(f"[ERROR] API返回空響應: {response}")
            return False, "API返回空響應"

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] 連接到 {model_name} 模型時出錯: {error_msg}")

        # 檢查是否是API金鑰問題
        if (
            "API key" in error_msg
            or "authentication" in error_msg.lower()
            or "invalid" in error_msg.lower()
        ):
            print(f"[ERROR] API金鑰問題: {error_msg}")
            return False, f"API金鑰無效或未授權: {error_msg}"

        return False, error_msg
