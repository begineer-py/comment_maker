# Gemini 程式碼註釋工具

一個利用 Google Gemini AI 為程式碼自動添加中文註釋的工具。

## 功能特點

- 支援多種程式語言（如 Python, JavaScript, HTML, CSS 等）
- 支援行尾註釋風格
- 支援遞迴處理子資料夾
- 支援檔案過濾器，可指定要處理的檔案類型
- 支援 API 請求延遲與退避演算法，有效避免 API 限制
- 提供圖形化使用者介面 (GUI) 和命令列介面 (CLI) 兩種使用方式

## 系統要求

- Python 3.8 或更高版本
- Google Gemini API 金鑰

## 安裝

1. 克隆或下載此專案儲存庫。
2. 安裝所需的依賴套件：
   ```bash
   pip install -r requirements.txt
   ```

### 3. 建立並啟用 Python 虛擬環境 (建議)

為避免依賴衝突，強烈建議為此專案建立一個獨立的 Python 虛擬環境。

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

或透過 VS Code 右下角的功能建立。
當您完成專案使用後，可透過以下命令退出虛擬環境：

```bash
deactivate
```

## API 金鑰設定

本工具需要 Google Gemini API 金鑰。您可以透過以下方式設定 API 金鑰：

### 方法一：設定系統環境變數 (推薦)

- Windows PowerShell:

  ```powershell
  $env:GEMINI_API_KEY = "your_api_key_here"
  ```

- Windows CMD:

  ```cmd
  set GEMINI_API_KEY=your_api_key_here
  ```

- Linux/macOS:
  ```bash
  export GEMINI_API_KEY=your_api_key_here
  ```

### 方法二：在程式執行時輸入

如果未設定環境變數，程式會提示您輸入 API 金鑰。您可以選擇：

- 僅儲存至當前會話 (程式關閉後失效)
- 永久儲存至系統環境變數 (可能需要管理員權限)

## 使用方法

### 圖形化使用者介面 (GUI) 模式

執行 GUI 程式 (推薦)：

```bash
python start_gui.py
```

或直接執行主 GUI 模組：```bash
範例
python gemini_commenter.py --folder /home/hacker/Desktop/comm

```bash
python gemini_commenter_gui.py
```

### 方法三：透過 NyaProxy 使用

請先修改 config.yaml 中的 api_key。
執行 Docker 部署 NyaProxy：

```bash
docker run -d \
  -p 8500:8080 \
  -v ${PWD}/config.yaml:/app/config.yaml \
  -v nya-proxy-logs:/app/logs \
  k3scat/nya-proxy:latest
```

請確保 8500 埠號未與其他服務衝突。
然後執行：

```bash
python gemini_commenter.py --folder <來源資料夾> --output <輸出資料夾> [選項]
```

範例：

```bash
python gemini_commenter.py --folder /home/hacker/Desktop/comment_maker/test --output /home/hacker/Desktop/comment_maker/output --filter *.py,*.html --delay 6.0 --max-backoff 64.0 --model gemini-2.5-flash --api-key ?? --nyaproxy --recursive
```

選項：

- `--folder, -f`：來源資料夾路徑 (預設：當前目錄)
- `--output, -o`：輸出資料夾路徑 (預設：commented)
- `--recursive, -r`：是否遞迴處理子資料夾
- `--filter`：檔案過濾器，例如：`*.py,*.js,*.html` (預設：`*.py`)
- `--delay, -d`：API 請求之間的延遲時間 (秒) (預設：6.0)
- `--max-backoff`：最大退避時間 (秒) (預設：64.0)
- `--comment-style`：註釋風格，目前僅支援 `line_end` (行尾註釋) (預設：`line_end`)
- `--model`：Gemini 模型名稱 (預設：`gemini-2.5-flash`)
- `--api-key`：直接指定 API 金鑰 (優先級高於環境變數)
- `--nyaproxy`：是否使用 NyaProxy (若不使用則無需添加此參數)

## 專案結構

```
.
├── .gitignore                  # Git 忽略檔案
├── api_key_setting/            # API 金鑰設定相關模組目錄
│   ├── api_key_manager.py      # API 金鑰管理模組
│   └── api_settings.py         # API 設定模組
├── auto_push_after_run.py      # 自動提交至 GitHub 的腳本
├── config.yaml                 # 設定檔
├── file_hander/                # 檔案處理相關模組目錄
│   └── file_processor.py       # 檔案處理模組
├── gemini_commenter.py         # 命令列工具
├── gemini_commenter_gui.py     # 模組化圖形化使用者介面工具
├── gui_modules/                # GUI 模組目錄
│   ├── __init__.py             # 模組初始化檔案
│   └── ui_components.py        # UI 元件模組
├── LICENSE.txt                 # 許可證檔案
├── prompts.py                  # 提示詞模板
├── README.md                   # 說明文件
├── requirements.txt            # 依賴套件列表
├── start_gui.py                # GUI 啟動腳本
└── nyaproxy/                   # NyaProxy 相關檔案目錄
```

## 模組化結構說明

GUI 工具採用模組化結構，將功能劃分為多個模組：

- `api_key_setting/api_settings.py`：處理 API 金鑰設定與測試相關功能
- `file_hander/file_processor.py`：處理檔案處理相關功能
- `gui_modules/ui_components.py`：處理 UI 相關功能，包含日誌面板、狀態列、設定面板等

這種模組化結構使程式碼更清晰、易於維護，並避免了單一檔案過於龐大。

## 取得 API 金鑰

您可以從 Google AI Studio 取得免費的 Gemini API 金鑰：
https://aistudio.google.com/

## 注意事項

- **API 金鑰**：您需要一個或多個有效的 Google Gemini API 金鑰，並透過環境變數 `GEMINI_API_KEY` 設定，或修改 `config.yaml`。
- **檔案大小**：處理大型檔案可能需要較長時間。
- **API 限制**：Gemini API 有使用限制，請適當設定延遲時間以避免觸發限制。
- **處理時間**：處理時間取決於檔案數量、大小和 API 回應速度。
- **多 API 金鑰輪詢 (透過 NyaProxy)**：為了解決 Google Gemini API 頻繁的額度限制問題，本專案支援透過 NyaProxy 進行多個 API 金鑰的輪詢使用。詳情請參閱 NyaProxy 專案連結。

## 許可證

MIT

## NyaProxy 專案連結

https://github.com/Nya-Foundation/NyaProxy

## 更新日誌

由於行前註釋容易導致縮排問題，本專案已移除行前註釋功能，請使用行尾註釋功能。
此外，先前的 Pro 模型目前似乎不再提供免費方案，已改為支援 Flash 模型。
先前遞迴處理子資料夾的功能設計有誤，現已修正。
此版本已通過完整測試，可安心使用。
