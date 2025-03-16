# Gemini代碼註釋器

使用Google Gemini AI為代碼添加中文註釋的工具。

## 功能特點

- 支持多種程式語言（Python、JavaScript、HTML、CSS等）
- 支持行尾註釋和行前註釋兩種風格
- 支持遞歸處理子文件夾
- 支持文件過濾器，可以指定要處理的文件類型
- 支持API請求延遲和退避算法，避免API限制
- 提供圖形界面和命令行兩種使用方式

## 系統要求

- Python 3.8+
- Google Gemini API密鑰

## 安裝

1. 克隆或下載本倉庫
2. 安裝依賴庫：
   ```
   pip install -r requirements.txt
   ```

## API密鑰設置

本工具需要使用Google Gemini API密鑰。您可以通過以下方式設置API密鑰：

### 方法1：設置系統環境變量（推薦）

- Windows PowerShell:
  ```
  $env:GEMINI_API_KEY = "your_api_key_here"
  ```

- Windows CMD:
  ```
  set GEMINI_API_KEY=your_api_key_here
  ```

- Linux/macOS:
  ```
  export GEMINI_API_KEY=your_api_key_here
  ```

### 方法2：在程序中輸入

如果未設置環境變量，程序會提示您輸入API密鑰。您可以選擇：
- 僅保存到當前會話（程序關閉後失效）
- 永久保存到系統環境變量（需要管理員權限）

## 使用方法

### 圖形界面模式

運行GUI程序：

```
python gemini_commenter_gui.py
```

### 命令行模式

```
python gemini_commenter.py --folder <源文件夾> --output <輸出文件夾> [選項]
```

選項：
- `--folder`, `-f`: 源文件夾路徑（默認：當前目錄）
- `--output`, `-o`: 輸出文件夾路徑（默認：commented）
- `--recursive`, `-r`: 是否遞歸處理子文件夾
- `--filter`: 文件過濾器，如：*.py,*.js,*.html（默認：*.py）
- `--delay`, `-d`: API請求之間的延遲時間（秒）（默認：6.0）
- `--max-backoff`: 最大退避時間（秒）（默認：64.0）
- `--comment-style`: 註釋風格，line_end（行尾註釋）或line_start（行前註釋）（默認：line_end）
- `--model`: Gemini模型名稱（默認：gemini-1.5-pro）
- `--api-key`: 直接指定API密鑰（優先級高於環境變量）

## 項目結構

```
.
├── gemini_commenter.py         # 命令行工具
├── gemini_commenter_gui.py     # 模塊化圖形界面工具
├── api_key_manager.py          # API密鑰管理模塊
├── prompts.py                  # 提示詞模板
├── gui_modules/                # GUI模塊目錄
│   ├── __init__.py             # 模塊初始化文件
│   ├── api_settings.py         # API設置模塊
│   ├── file_processor.py       # 文件處理模塊
│   └── ui_components.py        # UI組件模塊
├── requirements.txt            # 依賴庫列表
└── README.md                   # 說明文檔
```

## 模塊化結構說明

GUI工具採用了模塊化結構，將功能分為多個模塊：

- `api_settings.py`: 處理API密鑰設置和測試相關功能
- `file_processor.py`: 處理文件處理相關功能
- `ui_components.py`: 處理UI相關功能，包括日誌面板、狀態欄、設置面板等

這種模塊化結構使代碼更加清晰、易於維護，並且避免了單個文件過於龐大。

## 獲取API密鑰

您可以從Google AI Studio獲取免費的Gemini API密鑰：
https://aistudio.google.com/

## 注意事項

- API密鑰：您需要有一個有效的Google Gemini API密鑰
- 文件大小：大文件處理可能需要更長時間
- API限制：Gemini API有使用限制，請適當設置延遲時間
- 處理時間：處理時間取決於文件數量、大小和API響應速度

## 許可證

MIT