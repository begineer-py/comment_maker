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
## 修復了html編碼 和速率問題
# HTML文件編碼問題解決方案

## 問題描述

在使用Gemini代碼註釋器處理HTML文件時，遇到了編碼問題，導致生成的註釋文件內容顯示為亂碼或無法正確讀取。

## 原因分析

1. **編碼檢測問題**：原始腳本在讀取文件時沒有正確檢測HTML文件的編碼，特別是對於包含中文等非ASCII字符的文件。
2. **保存編碼問題**：在保存註釋後的文件時，沒有使用正確的編碼，導致中文字符無法正確顯示。
3. **HTML特殊處理**：HTML文件需要特殊處理，包括添加適當的編碼聲明和確保使用UTF-8編碼保存。
4. **API配額限制**：在測試過程中，還遇到了Gemini API的配額限制問題，需要增強重試機制。

## 解決方案

### 1. 改進文件讀取機制

- 對於HTML文件，優先嘗試UTF-8編碼
- 增加多種編碼嘗試：utf-8, cp950, big5, gbk, latin-1
- 添加二進制讀取模式，處理帶BOM的UTF-8文件
- 增強錯誤處理和日誌輸出

```python
# 對於HTML文件，優先嘗試UTF-8編碼
if file_ext.lower() in ['.html', '.htm']:
    print(f"[INFO] 檢測到HTML文件，優先嘗試UTF-8編碼")
    encodings_to_try = ['utf-8'] + encodings_to_try

# 嘗試檢測BOM並解碼
if binary_data.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
    code = binary_data[3:].decode('utf-8')
    print(f"[INFO] 檢測到UTF-8 BOM，成功解碼")
    successful_encoding = 'utf-8-sig'  # 使用-sig表示帶BOM的UTF-8
```

### 2. 改進文件保存機制

- 對於HTML文件，強制使用UTF-8編碼保存
- 檢查註釋後的代碼是否可以使用檢測到的編碼進行編碼
- 添加適當的編碼聲明到HTML文件
- 增強錯誤處理，提供多種保存方式的回退機制

```python
# 對於HTML文件，強制使用UTF-8編碼保存
if file_ext.lower() in ['.html', '.htm']:
    print(f"[INFO] HTML文件將使用UTF-8編碼保存")
    successful_encoding = 'utf-8'

# 對於HTML文件，添加適當的編碼聲明
if file_ext.lower() in ['.html', '.htm'] and '<meta charset=' not in commented_code.lower():
    # 檢查是否有head標籤
    if '<head>' in commented_code:
        commented_code = commented_code.replace('<head>', '<head>\n    <meta charset="UTF-8">')
        print(f"[INFO] 已添加UTF-8編碼聲明到HTML文件")
```

### 3. 增強API配額限制處理

- 添加更長的重試等待時間
- 針對不同類型的錯誤使用不同的重試策略
- 增加日誌輸出，方便調試

```python
# 如果是配額限制問題，等待更長時間後重試
if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg:
    wait_time = base_wait_time * (2 ** attempt) + random.uniform(0, 5)
    print(f"[WARNING] 檢測到API配額限制，等待 {wait_time:.2f} 秒後重試...")
    time.sleep(wait_time)
    continue
```

### 4. 測試腳本

創建了一個獨立的測試腳本 `test_encoding.py`，用於測試HTML文件的編碼處理，不依賴於Gemini API。這個腳本可以：

- 測試不同編碼的HTML文件的讀取
- 測試添加註釋後的保存
- 提供詳細的調試信息
- 驗證保存的文件內容

## 結論

通過以上改進，我們成功解決了HTML文件的編碼問題，特別是對於包含中文等非ASCII字符的文件。現在，Gemini代碼註釋器可以正確處理各種編碼的HTML文件，並生成正確的註釋。

同時，我們也增強了API配額限制的處理能力，使腳本在遇到API限制時能夠更加智能地重試，提高了腳本的穩定性和可靠性。