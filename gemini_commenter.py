import os
import glob
import re
import argparse
import sys
import time  # 导入time模块用于请求延迟
import random  # 导入random模块用于随机延迟
from dotenv import load_dotenv
import google.generativeai as genai

# 设置控制台编码
try:
    # 尝试设置控制台编码为UTF-8
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # 设置为UTF-8
except:
    pass

# 加载环境变量
load_dotenv()

def get_api_key_from_environment():
    """从环境变量中获取API密钥，优先级：系统环境变量 > .env文件"""
    # 首先尝试从系统环境变量获取
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # 如果系统环境变量中没有，则从.env文件获取
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        
    # 记录API密钥来源
    if api_key:
        if "GEMINI_API_KEY" in os.environ:
            print("[INFO] API key found in system environment variables")
        else:
            print("[INFO] API key found in .env file")
    
    return api_key

# 获取API密钥
GEMINI_API_KEY = get_api_key_from_environment()
if not GEMINI_API_KEY:
    print("[ERROR] GEMINI_API_KEY not found")
    print("[INFO] Please set your Gemini API key in .env file:")
    print("GEMINI_API_KEY=your_api_key_here")
    print("[INFO] Or set system environment variable GEMINI_API_KEY")
    sys.exit(1)

if GEMINI_API_KEY == "your_gemini_api_key_here":
    print("[ERROR] Please replace the placeholder with your actual Gemini API key")
    print("[INFO] Visit https://ai.google.dev/ to get your API key")
    sys.exit(1)

try:
    # 配置Gemini API
    genai.configure(api_key=GEMINI_API_KEY)

    # 尝试不同的模型名称
    models_to_try = ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.0-pro']
    model = None
    
    for model_name in models_to_try:
        try:
            print(f"[INFO] Trying to use {model_name} model...")
            model = genai.GenerativeModel(model_name)
            # 测试API连接
            response = model.generate_content("Hello")
            print(f"[INFO] Successfully connected using {model_name} model")
            break  # 如果成功，跳出循环
        except Exception as model_error:
            print(f"[INFO] Failed to use {model_name} model: {model_error}")
            continue  # 尝试下一个模型
    
    # 检查是否成功连接到任何模型
    if model is None:
        print("[ERROR] Failed to connect to any Gemini model. Please check your API key and network.")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] Error configuring Gemini API: {e}")
    print("[INFO] Please make sure your API key is valid and your network can connect to Google services")
    sys.exit(1)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='使用Gemini API为Python文件添加逐行注释')
    parser.add_argument('--folder', type=str, default='.',
                        help='要处理的文件夹路径 (默认: 当前文件夹)')
    parser.add_argument('--output', type=str, default='commented',
                        help='输出文件夹路径 (默认: ./commented)')
    parser.add_argument('--recursive', action='store_true',
                        help='是否递归处理子文件夹')
    parser.add_argument('--api-key', type=str,
                        help='Gemini API密钥 (可选，优先使用环境变量)')
    parser.add_argument('--filter', type=str, default='*.py',
                        help='文件过滤器 (默认: *.py)')
    parser.add_argument('--delay', type=float, default=6.0,
                        help='API请求之间的基础延迟时间(秒) (默认: 6.0秒)')
    parser.add_argument('--max-backoff', type=float, default=64.0,
                        help='最大退避延迟时间(秒) (默认: 64.0秒)')
    parser.add_argument('--comment-style', type=str, choices=['line_start', 'line_end'], default='line_end',
                        help='注释风格: line_start (行前注释) 或 line_end (行尾注释) (默认: line_end)')
    return parser.parse_args()

def get_python_files(folder_path, recursive=False, file_filter='*.py'):
    """获取指定文件夹中的所有Python文件"""
    pattern = os.path.join(folder_path, '**', file_filter) if recursive else os.path.join(folder_path, file_filter)
    return glob.glob(pattern, recursive=recursive)

def generate_comments_for_code(code, comment_style='line_end'):
    """使用Gemini API为代码生成逐行注释"""
    if comment_style == 'line_end':
        prompt = f"""
        请为以下Python代码添加中文注释。
        
        重要规则：
        1. 只使用行尾注释，即在代码行后面添加 # 后跟注释内容
        2. 不要添加行前注释，避免缩进错误
        3. 不要修改原始代码的任何部分，包括空行和缩进
        4. 对于已有注释的行，保持原样不变
        5. 注释应简洁明了地解释该行代码的功能
        6. 空行不需要添加注释
        
        示例：
        ```python
        def hello(name):  # 定义一个打招呼的函数，接收name参数
            greeting = "Hello, " + name  # 创建问候语字符串
            return greeting  # 返回问候语
        ```
        
        代码:
        ```python
        {code}
        ```
        
        请返回带有行尾注释的完整代码。
        """
    else:  # line_start
        prompt = f"""
        请为以下Python代码添加逐行中文注释。
        
        重要规则：
        1. 在每行代码前添加注释，使用 # 开头
        2. 保持与代码相同的缩进级别，确保注释和代码对齐
        3. 不要修改原始代码的任何部分
        4. 对于已有注释的行，保持原样不变
        5. 注释应简洁明了地解释该行代码的功能
        6. 空行不需要添加注释
        
        示例：
        ```python
        # 定义一个打招呼的函数，接收name参数
        def hello(name):
            # 创建问候语字符串
            greeting = "Hello, " + name
            # 返回问候语
            return greeting
        ```
        
        代码:
        ```python
        {code}
        ```
        
        请返回带有行前注释的完整代码。
        """
    
    try:
        # 实现指数退避算法
        max_retries = 5
        base_delay = 1  # 基础延迟时间(秒)
        max_backoff = 64  # 最大退避时间(秒)
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt)
                
                # 检查响应是否为空
                if not response or not hasattr(response, 'text') or not response.text:
                    print(f"[WARNING] API返回空响应 (attempt {attempt+1}/{max_retries})")
                    if attempt < max_retries - 1:
                        wait_time = min((2 ** attempt) + random.random(), max_backoff)
                        print(f"[INFO] 等待 {wait_time:.2f} 秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("[ERROR] 多次尝试后API仍返回空响应，返回原始代码")
                        return code
                
                commented_code = response.text
                
                # 提取代码块
                code_pattern = r"```python\n(.*?)\n```"
                match = re.search(code_pattern, commented_code, re.DOTALL)
                if match:
                    commented_code = match.group(1)
                
                # 确保返回的不是None
                if commented_code is None:
                    print("[WARNING] 提取的代码为None，返回原始代码")
                    return code
                
                return commented_code
            except Exception as retry_error:
                if "429" in str(retry_error) or "Too many requests" in str(retry_error):
                    # 计算指数退避时间
                    wait_time = min((2 ** attempt) + random.random(), max_backoff)
                    print(f"[WARNING] API rate limit exceeded (attempt {attempt+1}/{max_retries}): {retry_error}")
                    print(f"[INFO] Backing off for {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                elif attempt < max_retries - 1:
                    # 其他错误也使用退避，但使用不同的消息
                    wait_time = min((2 ** attempt) + random.random(), max_backoff)
                    print(f"[WARNING] API request failed (attempt {attempt+1}/{max_retries}): {retry_error}")
                    print(f"[INFO] Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                else:
                    raise  # 重试次数用完，抛出异常
    except Exception as e:
        print(f"[ERROR] Error generating comments: {e}")
        return code  # 出错时返回原始代码

def process_file(file_path, output_folder, delay=6.0, comment_style='line_end'):
    """处理单个Python文件，添加注释并保存到输出文件夹"""
    try:
        print(f"[INFO] Processing: {file_path}")
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 生成注释
        commented_code = generate_comments_for_code(code, comment_style)
        
        # 确保commented_code不是None
        if commented_code is None:
            print(f"[ERROR] 生成的注释代码为None，跳过保存: {file_path}")
            return False
        
        # 创建输出文件夹
        os.makedirs(output_folder, exist_ok=True)
        
        # 确定输出文件路径
        rel_path = os.path.relpath(file_path, os.path.dirname(output_folder))
        output_path = os.path.join(output_folder, rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 保存注释后的代码
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(commented_code)
            print(f"[INFO] Completed: {file_path} -> {output_path}")
        except TypeError as te:
            print(f"[ERROR] 写入文件时类型错误: {te}")
            print(f"[INFO] 尝试将None转换为空字符串并保存原始代码")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(code)  # 保存原始代码
            print(f"[INFO] 已保存原始代码: {output_path}")
            return False
        
        # 添加随机延迟，避免API请求过于规律
        actual_delay = delay + random.uniform(0, 2)
        print(f"[INFO] Waiting for {actual_delay:.2f} seconds before next request...")
        time.sleep(actual_delay)
        
        return True
    except Exception as e:
        print(f"[ERROR] Error processing file {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    args = parse_arguments()
    
    # 如果命令行提供了API密钥，则使用命令行提供的API密钥
    global GEMINI_API_KEY
    if args.api_key:
        GEMINI_API_KEY = args.api_key
        print("[INFO] Using API key provided in command line")
        # 重新配置API
        genai.configure(api_key=GEMINI_API_KEY)
    
    # 获取Python文件列表
    python_files = get_python_files(args.folder, args.recursive, args.filter)
    
    if not python_files:
        print(f"[INFO] No files matching {args.filter} found in {args.folder}")
        return
    
    print(f"[INFO] Found {len(python_files)} files")
    print(f"[INFO] Rate limiting: Using {args.delay} seconds base delay between requests with exponential backoff")
    print(f"[INFO] Comment style: {'Line end comments' if args.comment_style == 'line_end' else 'Line start comments'}")
    
    # 处理每个文件
    success_count = 0
    total_count = 0
    
    for file_path in python_files:
        # 跳过输出文件夹中的文件
        if os.path.abspath(args.output) in os.path.abspath(file_path):
            continue
            
        # 跳过当前脚本
        if os.path.samefile(file_path, __file__):
            continue
        
        total_count += 1
        current_file_num = total_count
        total_files = len(python_files)
        print(f"[INFO] Processing file {current_file_num}/{total_files}: {file_path}")
            
        if process_file(file_path, args.output, args.delay, args.comment_style):
            success_count += 1
            print(f"[INFO] Progress: {success_count}/{total_count} files completed successfully")
    
    print(f"[INFO] Processing completed: {success_count}/{total_count} files successfully commented")

if __name__ == "__main__":
    main() 