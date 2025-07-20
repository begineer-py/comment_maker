import sys
import os

# 將專案根目錄添加到 Python 路徑中，以確保模組可以被正確找到
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli.main import main

if __name__ == "__main__":
    main()
