# Python代码自动注释工具

这是一个使用Google Gemini API自动为Python文件添加逐行中文注释的工具。

## 功能特点

- 自动扫描指定文件夹中的Python文件
- 使用Gemini AI为每个文件生成逐行中文注释
- 支持递归处理子文件夹
- 保留原始代码结构，只添加注释
- 输出到单独的文件夹，不修改原始文件
- 提供图形用户界面(GUI)
- 自动从环境变量中提取API密钥
- 支持文件过滤，可处理不同类型的文件

## 安装

1. 克隆或下载本仓库
2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
3. 设置Gemini API密钥（以下方式任选其一）：
   - 在`.env`文件中设置：
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     ```
   - 设置系统环境变量`GEMINI_API_KEY`
   - 在GUI界面中输入

## 获取Gemini API密钥

要使用此工具，您需要一个有效的Google Gemini API密钥。以下是获取密钥的步骤：

1. 访问 [Google AI Studio](https://ai.google.dev/)
2. 登录您的Google账户
3. 点击右上角的头像，然后选择"获取API密钥"
4. 创建一个新的API密钥或使用现有的密钥
5. 复制API密钥
6. 将密钥设置为环境变量或保存到`.env`文件中

## API密钥优先级

工具按以下优先级查找API密钥：

1. GUI界面中手动输入的密钥
2. 系统环境变量 `GEMINI_API_KEY`
3. `.env` 文件中的 `GEMINI_API_KEY`

## 使用方法

### 图形用户界面(GUI)

启动GUI界面（以下方式任选其一）：

```bash
# 方式1：直接启动GUI
python gemini_commenter_gui.py

# 方式2：使用启动脚本（推荐）
python start_gui.py
```

也可以直接双击`start_gui.py`文件启动GUI界面。

GUI界面提供以下功能：
- 设置Gemini API密钥（自动从环境变量加载）
- 选择源文件夹和输出文件夹
- 选择是否递归处理子文件夹
- 设置文件过滤器（默认：*.py）
- 实时显示处理进度和日志
- 一键打开输出文件夹
- 主题切换（暗色/亮色）

### 命令行界面（高级用户）

如果您更喜欢使用命令行，也可以直接使用命令行界面：

```bash
python gemini_commenter.py
```

这将处理当前文件夹中的所有Python文件，并将注释后的文件保存到`./commented`文件夹。

#### 命令行参数

- `--folder`：指定要处理的文件夹路径（默认：当前文件夹）
- `--output`：指定输出文件夹路径（默认：`./commented`）
- `--recursive`：递归处理子文件夹中的Python文件
- `--api-key`：直接提供Gemini API密钥（可选，优先使用环境变量）
- `--filter`：文件过滤器（默认：*.py）

示例：

```bash
# 处理指定文件夹中的所有Python文件
python gemini_commenter.py --folder ./my_project

# 递归处理所有子文件夹
python gemini_commenter.py --recursive

# 指定输出文件夹
python gemini_commenter.py --output ./commented_files

# 直接提供API密钥
python gemini_commenter.py --api-key your_api_key_here

# 处理所有JavaScript文件
python gemini_commenter.py --filter "*.js"
```

## 示例

原始Python文件：

```python
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2])
    
    return fib_sequence
```

添加注释后：

```python
# 定义一个函数，用于生成斐波那契数列
def fibonacci(n):
    # 如果n小于等于0，返回空列表
    if n <= 0:
        return []
    # 如果n等于1，返回只包含0的列表
    elif n == 1:
        return [0]
    # 如果n等于2，返回包含0和1的列表
    elif n == 2:
        return [0, 1]
    
    # 初始化斐波那契数列，包含前两个数字0和1
    fib_sequence = [0, 1]
    # 循环计算剩余的斐波那契数
    for i in range(2, n):
        # 每个数字是前两个数字的和
        fib_sequence.append(fib_sequence[i-1] + fib_sequence[i-2])
    
    # 返回完整的斐波那契数列
    return fib_sequence
```

## 常见问题解决

### API密钥错误

如果您看到以下错误：

```
错误: 配置Gemini API时出错: 400 API key not valid. Please pass a valid API key.
```

请确保：
1. 您已正确设置API密钥（环境变量或.env文件）
2. API密钥是有效的
3. 您的网络可以连接到Google服务

### 文件编码问题

如果处理文件时出现编码错误，请确保您的Python文件使用UTF-8编码。

### GUI界面问题

如果GUI界面无法启动，请确保已安装所有依赖：

```bash
pip install -r requirements.txt
```

## 注意事项

- 需要有效的Gemini API密钥
- 处理大量文件可能会消耗API配额
- 对于非常复杂或特殊的代码，可能需要手动调整生成的注释
- 此工具默认处理Python文件，但也可以通过文件过滤器处理其他类型的文件