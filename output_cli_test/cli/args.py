import argparse


def parse_args():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="使用Gemini AI為代碼文件添加中文註釋")
    parser.add_argument(
        "--folder", "-f", type=str, default=".", help="包含代碼文件的文件夾路徑"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="commented", help="輸出文件夾路徑"
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true", help="是否遞歸處理子文件夾"
    )
    parser.add_argument(
        "--filter", type=str, default="*.py", help="文件過濾器，如: *.py,*.js,*.java"
    )
    parser.add_argument(
        "--delay", "-d", type=float, default=6.0, help="API請求之間的延遲(秒)"
    )
    parser.add_argument(
        "--max-backoff", type=float, default=64.0, help="最大退避時間(秒)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Gemini模型名稱，如: gemini-2.5-flash",
    )
    parser.add_argument(
        "--api-key", type=str, help="Gemini API金鑰，優先級高於環境變數"
    )
    parser.add_argument("--nyaproxy", action="store_true", help="是否使用nyaproxy代理")
    return parser.parse_args()
