import os
import sys
import re
import tkinter as tk
from tkinter import filedialog, ttk, messagebox, scrolledtext, Menu
import threading
import subprocess
import queue
from dotenv import load_dotenv
import google.generativeai as genai
import time
import platform

# 加载环境变量
load_dotenv()

class GeminiCommenterGUI:
    def __init__(self, root):
        print(f"[DEBUG] 初始化GUI: 当前线程ID={threading.get_ident()}, 主线程ID={threading.main_thread().ident}")
        print(f"[DEBUG] 是否在主线程中: {threading.current_thread() is threading.main_thread()}")
        
        self.root = root
        self.root.title("Python代码自动注释工具")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # 设置图标（如果有）
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except Exception as e:
            print(f"[WARNING] 设置图标时出错: {e}")
        
        # 设置API密钥 - 优先从系统环境变量获取
        self.api_key = self.get_api_key_from_environment()
        
        # 创建消息队列用于线程间通信
        self.queue = queue.Queue()
        print("[DEBUG] 消息队列已创建")
        
        # 初始化进度值变量
        self._current_progress_value = 0
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_label = ttk.Label(self.main_frame, text="Python代码自动注释工具", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 创建设置框架
        settings_frame = ttk.LabelFrame(self.main_frame, text="设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=10)
        
        # API密钥设置
        api_frame = ttk.Frame(settings_frame)
        api_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(api_frame, text="Gemini API密钥:").pack(side=tk.LEFT, padx=5)
        self.api_entry = ttk.Entry(api_frame, width=50, show="*")
        self.api_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        if self.api_key:
            self.api_entry.insert(0, self.api_key)
        
        ttk.Button(api_frame, text="保存API密钥", command=self.save_api_key).pack(side=tk.LEFT, padx=5)
        
        # 显示/隐藏API密钥
        self.show_api_var = tk.BooleanVar(value=False)
        show_api_check = ttk.Checkbutton(api_frame, text="显示", variable=self.show_api_var, command=self.toggle_api_visibility)
        show_api_check.pack(side=tk.LEFT, padx=5)
        
        # 文件夹选择
        folder_frame = ttk.Frame(settings_frame)
        folder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(folder_frame, text="源文件夹:").pack(side=tk.LEFT, padx=5)
        self.folder_entry = ttk.Entry(folder_frame, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.folder_entry.insert(0, os.getcwd())
        
        ttk.Button(folder_frame, text="浏览...", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        
        # 输出文件夹选择
        output_frame = ttk.Frame(settings_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="输出文件夹:").pack(side=tk.LEFT, padx=5)
        self.output_entry = ttk.Entry(output_frame, width=50)
        self.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.output_entry.insert(0, os.path.join(os.getcwd(), "commented"))
        
        ttk.Button(output_frame, text="浏览...", command=self.browse_output).pack(side=tk.LEFT, padx=5)
        
        # 选项框架
        option_frame = ttk.Frame(settings_frame)
        option_frame.pack(fill=tk.X, pady=5)
        
        # 递归选项
        self.recursive_var = tk.BooleanVar(value=True)
        recursive_check = ttk.Checkbutton(option_frame, text="递归处理子文件夹", variable=self.recursive_var)
        recursive_check.pack(side=tk.LEFT, padx=5)
        
        # 文件过滤选项
        ttk.Label(option_frame, text="文件过滤:").pack(side=tk.LEFT, padx=(20, 5))
        self.filter_var = tk.StringVar(value="*.py")
        filter_entry = ttk.Entry(option_frame, textvariable=self.filter_var, width=15)
        filter_entry.pack(side=tk.LEFT, padx=5)
        
        # 注释风格选项
        comment_style_frame = ttk.Frame(settings_frame)
        comment_style_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(comment_style_frame, text="注释风格:").pack(side=tk.LEFT, padx=5)
        self.comment_style_var = tk.StringVar(value="line_end")
        
        style_frame = ttk.Frame(comment_style_frame)
        style_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Radiobutton(style_frame, text="行尾注释 (# 在代码后)", 
                       variable=self.comment_style_var, value="line_end").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(style_frame, text="行前注释 (# 在代码前)", 
                       variable=self.comment_style_var, value="line_start").pack(side=tk.LEFT, padx=10)
        
        # 添加注释风格说明
        ttk.Label(comment_style_frame, text="推荐使用行尾注释，避免缩进错误", 
                 font=("Arial", 8, "italic")).pack(side=tk.RIGHT, padx=5)
        
        # 添加速率限制设置框架
        rate_limit_frame = ttk.LabelFrame(settings_frame, text="API速率限制", padding="5")
        rate_limit_frame.pack(fill=tk.X, pady=5)
        
        # 请求延迟设置
        delay_frame = ttk.Frame(rate_limit_frame)
        delay_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(delay_frame, text="请求延迟(秒):").pack(side=tk.LEFT, padx=5)
        self.delay_var = tk.StringVar(value="6.0")
        delay_entry = ttk.Entry(delay_frame, textvariable=self.delay_var, width=8)
        delay_entry.pack(side=tk.LEFT, padx=5)
        
        # 最大退避时间设置
        max_backoff_frame = ttk.Frame(rate_limit_frame)
        max_backoff_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(max_backoff_frame, text="最大退避时间(秒):").pack(side=tk.LEFT, padx=5)
        self.max_backoff_var = tk.StringVar(value="64.0")
        max_backoff_entry = ttk.Entry(max_backoff_frame, textvariable=self.max_backoff_var, width=8)
        max_backoff_entry.pack(side=tk.LEFT, padx=5)
        
        # 速率限制说明
        ttk.Label(rate_limit_frame, text="注意: 系统会自动使用指数退避算法处理API限制，避免超出Google API免费限制", 
                 font=("Arial", 8, "italic")).pack(pady=2)
        
        # 操作按钮
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="开始处理", command=self.start_processing, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="停止", command=self.stop_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="打开输出文件夹", command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self.main_frame, text="处理日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # 进度条
        self.progress = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # 处理线程
        self.processing_thread = None
        self.is_processing = False
        
        # 检查API密钥
        self.check_api_key()
        
        # 设置关闭窗口事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动消息处理
        print("[DEBUG] 启动消息队列处理")
        try:
            self.process_queue()
            print("[DEBUG] 消息队列处理已启动")
        except Exception as e:
            print(f"[ERROR] 启动消息队列处理时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = Menu(self.root)
        
        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开源文件夹", command=self.browse_folder)
        file_menu.add_command(label="设置输出文件夹", command=self.browse_output)
        file_menu.add_separator()
        file_menu.add_command(label="打开输出文件夹", command=self.open_output_folder)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 操作菜单
        action_menu = Menu(menubar, tearoff=0)
        action_menu.add_command(label="开始处理", command=self.start_processing)
        action_menu.add_command(label="停止处理", command=self.stop_processing)
        action_menu.add_separator()
        action_menu.add_command(label="清空日志", command=self.clear_log)
        menubar.add_cascade(label="操作", menu=action_menu)
        
        # 设置菜单
        settings_menu = Menu(menubar, tearoff=0)
        settings_menu.add_command(label="设置API密钥", command=self.show_api_settings)
        
        # 主题子菜单
        theme_menu = Menu(settings_menu, tearoff=0)
        self.theme_var = tk.StringVar(value="dark")
        theme_menu.add_radiobutton(label="暗色主题", variable=self.theme_var, value="dark", command=lambda: self.change_theme("dark"))
        theme_menu.add_radiobutton(label="亮色主题", variable=self.theme_var, value="light", command=lambda: self.change_theme("light"))
        settings_menu.add_cascade(label="主题", menu=theme_menu)
        
        menubar.add_cascade(label="设置", menu=settings_menu)
        
        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def get_api_key_from_environment(self):
        """从环境变量中获取API密钥，优先级：系统环境变量 > .env文件"""
        # 首先尝试从系统环境变量获取
        api_key = os.environ.get("GEMINI_API_KEY")
        
        # 如果系统环境变量中没有，则从.env文件获取
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
            
        # 记录API密钥来源
        if api_key:
            if api_key in os.environ:
                print("从系统环境变量获取API密钥")
            else:
                print("从.env文件获取API密钥")
        
        return api_key
    
    def check_api_key(self):
        """检查API密钥是否有效"""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.log("警告: 未设置有效的Gemini API密钥，请在设置中输入您的API密钥")
            messagebox.showwarning("API密钥未设置", "请设置有效的Gemini API密钥才能使用此工具")
        else:
            self.log(f"已从{'系统环境变量' if self.api_key in os.environ else '.env文件'}获取API密钥")
    
    def toggle_api_visibility(self):
        """切换API密钥显示/隐藏"""
        if self.show_api_var.get():
            self.api_entry.config(show="")
        else:
            self.api_entry.config(show="*")
    
    def save_api_key(self):
        """保存API密钥到.env文件和系统环境变量"""
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showerror("错误", "API密钥不能为空")
            return
        
        try:
            # 读取现有.env文件
            env_content = ""
            if os.path.exists(".env"):
                with open(".env", "r", encoding="utf-8") as f:
                    env_content = f.read()
            
            # 更新或添加API密钥
            if "GEMINI_API_KEY=" in env_content:
                env_content = re.sub(r"GEMINI_API_KEY=.*", f"GEMINI_API_KEY={api_key}", env_content)
            else:
                env_content += f"\nGEMINI_API_KEY={api_key}"
            
            # 写入.env文件
            with open(".env", "w", encoding="utf-8") as f:
                f.write(env_content.strip())
            
            # 同时设置当前进程的环境变量
            os.environ["GEMINI_API_KEY"] = api_key
            
            self.api_key = api_key
            messagebox.showinfo("成功", "API密钥已保存到.env文件并设置为当前环境变量")
            self.log("API密钥已更新")
            
            # 重新加载环境变量
            load_dotenv(override=True)
        except Exception as e:
            messagebox.showerror("错误", f"保存API密钥时出错: {e}")
    
    def browse_folder(self):
        """浏览选择源文件夹"""
        folder = filedialog.askdirectory(initialdir=self.folder_entry.get())
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def browse_output(self):
        """浏览选择输出文件夹"""
        folder = filedialog.askdirectory(initialdir=self.output_entry.get())
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
    
    def log(self, message):
        """添加日志消息"""
        # 打印到控制台
        print(f"[LOG] {message}")
        
        # 使用队列安全地从其他线程更新UI
        try:
            self.queue.put(("log", message))
            print(f"[DEBUG] 日志消息已加入队列: {message[:50]}...")
        except Exception as e:
            print(f"[ERROR] 添加日志消息到队列时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def update_status(self, status):
        """更新状态栏"""
        # 打印到控制台
        print(f"[STATUS] {status}")
        
        # 使用队列安全地从其他线程更新UI
        try:
            self.queue.put(("status", status))
            print(f"[DEBUG] 状态更新已加入队列: {status}")
        except Exception as e:
            print(f"[ERROR] 添加状态更新到队列时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def update_progress(self, value):
        """更新进度条"""
        # 打印到控制台
        print(f"[PROGRESS] {value}")
        
        # 使用队列安全地从其他线程更新UI
        try:
            self.queue.put(("progress", value))
            print(f"[DEBUG] 进度更新已加入队列: {value}")
        except Exception as e:
            print(f"[ERROR] 添加进度更新到队列时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def show_message(self, title, message, error=False):
        """显示消息对话框"""
        # 打印到控制台
        print(f"[MESSAGE] {title}: {message} (error={error})")
        
        # 使用队列安全地从其他线程更新UI
        try:
            self.queue.put(("message", (title, message, error)))
            print(f"[DEBUG] 消息对话框请求已加入队列: {title}")
        except Exception as e:
            print(f"[ERROR] 添加消息对话框请求到队列时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def process_queue(self):
        """处理消息队列中的UI更新请求"""
        try:
            # 只在队列不为空时打印调试信息
            if not self.queue.empty():
                print(f"[DEBUG] 检查消息队列: 当前线程ID={threading.get_ident()}, 主线程ID={threading.main_thread().ident}")
                print(f"[DEBUG] 是否在主线程中: {threading.current_thread() is threading.main_thread()}")
            
            while not self.queue.empty():
                try:
                    msg_type, data = self.queue.get(0)
                    
                    # 只对重要消息类型打印详细日志
                    if msg_type in ["message", "processing_done"]:
                        print(f"[DEBUG] 处理消息: {msg_type}")
                    
                    if msg_type == "log":
                        # 更新日志
                        # 不打印每条日志的详细内容，避免重复
                        # 使用after方法确保在主线程中执行
                        def update_log(text=data):
                            try:
                                self.log_text.config(state=tk.NORMAL)
                                self.log_text.insert(tk.END, text + "\n")
                                self.log_text.see(tk.END)
                                self.log_text.config(state=tk.DISABLED)
                            except Exception as e:
                                print(f"[ERROR] 更新日志时出错: {e}")
                        
                        self.root.after(0, update_log)
                    
                    elif msg_type == "status":
                        # 更新状态栏
                        print(f"[DEBUG] 更新状态: {data}")
                        def update_status(status=data):
                            try:
                                self.status_var.set(status)
                            except Exception as e:
                                print(f"[ERROR] 更新状态时出错: {e}")
                        
                        self.root.after(0, update_status)
                    
                    elif msg_type == "progress":
                        # 更新进度条 - 不打印每次进度更新
                        def update_progress(value=data):
                            try:
                                self.progress['value'] = value
                                # 保存当前进度值，供其他线程查询
                                self._current_progress_value = value
                            except Exception as e:
                                print(f"[ERROR] 更新进度时出错: {e}")
                        
                        self.root.after(0, update_progress)
                    
                    elif msg_type == "progress_max":
                        # 设置进度条最大值
                        print(f"[DEBUG] 设置进度条最大值: {data}")
                        def update_progress_max(max_value=data):
                            try:
                                self.progress['maximum'] = max_value
                            except Exception as e:
                                print(f"[ERROR] 设置进度条最大值时出错: {e}")
                        
                        self.root.after(0, update_progress_max)
                    
                    elif msg_type == "get_progress":
                        # 获取当前进度值 - 不打印调试信息
                        def get_current_progress():
                            try:
                                self._current_progress_value = self.progress['value']
                            except Exception as e:
                                print(f"[ERROR] 获取进度值时出错: {e}")
                                self._current_progress_value = 0
                        
                        self.root.after(0, get_current_progress)
                    
                    elif msg_type == "message":
                        # 显示消息对话框
                        title, message, error = data
                        print(f"[DEBUG] 显示消息对话框: title={title}, error={error}")
                        # 创建函数避免lambda闭包问题
                        def show_message_dialog(title=title, message=message, is_error=error):
                            try:
                                if is_error:
                                    messagebox.showerror(title, message)
                                else:
                                    messagebox.showinfo(title, message)
                                print(f"[DEBUG] 消息对话框显示成功: {title}")
                            except Exception as e:
                                print(f"[ERROR] 显示消息对话框时出错: {e}")
                        
                        self.root.after(0, show_message_dialog)
                    
                    elif msg_type == "processing_done":
                        # 处理完成
                        print("[DEBUG] 处理完成")
                        def mark_processing_done():
                            try:
                                self.is_processing = False
                                print("[DEBUG] 标记处理完成成功")
                            except Exception as e:
                                print(f"[ERROR] 标记处理完成时出错: {e}")
                        
                        self.root.after(0, mark_processing_done)
                    
                    # 完成处理此消息
                    self.queue.task_done()
                    
                    # 只对重要消息类型打印完成日志
                    if msg_type in ["message", "processing_done"]:
                        print(f"[DEBUG] 消息 {msg_type} 处理完成")
                except Exception as item_error:
                    print(f"[ERROR] 处理单个消息时出错: {item_error}")
                    import traceback
                    traceback.print_exc()
        
        except Exception as e:
            print(f"[ERROR] 处理消息队列时出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 每100毫秒检查一次队列
        try:
            self.root.after(100, self.process_queue)
            # 不打印每次队列检查的调试信息
        except Exception as e:
            print(f"[ERROR] 安排下一次队列检查时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def start_processing(self):
        """开始处理文件"""
        try:
            print(f"[INFO] 开始处理: 当前线程ID={threading.get_ident()}, 主线程ID={threading.main_thread().ident}")
            
            # 检查是否已经在处理中
            if self.is_processing:
                self.show_message("警告", "已经有处理任务在运行中", True)
                return
            
            # 检查文件夹是否已选择
            folder = self.folder_entry.get().strip()
            if not folder:
                self.show_message("错误", "请先选择一个文件夹", True)
                return
            
            # 检查输出文件夹是否已选择
            output = self.output_entry.get().strip()
            if not output:
                self.show_message("错误", "请先选择一个输出文件夹", True)
                return
            
            # 检查API密钥是否已设置
            api_key = self.api_entry.get().strip()
            if not api_key:
                self.show_message("错误", "请先设置API密钥", True)
                return
            
            # 获取其他参数
            recursive = self.recursive_var.get()
            file_filter = self.filter_var.get()
            comment_style = self.comment_style_var.get()
            
            # 获取速率限制参数 - 在主线程中获取
            try:
                delay = float(self.delay_var.get())
                if delay < 0:
                    delay = 1.0
                    print("[WARNING] 延迟值无效，使用默认值 1.0")
            except Exception as e:
                print(f"[WARNING] 解析延迟值时出错: {e}，使用默认值 1.0")
                delay = 1.0
            
            try:
                max_backoff = float(self.max_backoff_var.get())
                if max_backoff <= 0:
                    max_backoff = 60.0
                    print("[WARNING] 最大回退时间值无效，使用默认值 60.0")
            except Exception as e:
                print(f"[WARNING] 解析最大回退时间值时出错: {e}，使用默认值 60.0")
                max_backoff = 60.0
            
            # 清空日志
            self.clear_log()
            
            # 重置进度条
            self.progress['value'] = 0
            
            # 标记为处理中
            self.is_processing = True
            
            # 更新状态
            self.update_status("正在准备处理...")
            
            # 记录处理参数
            self.log(f"开始处理文件夹: {folder}")
            self.log(f"输出到: {output}")
            self.log(f"递归处理: {'是' if recursive else '否'}")
            self.log(f"文件过滤: {file_filter}")
            self.log(f"注释风格: {'行尾注释' if comment_style == 'line_end' else '行前注释'}")
            self.log(f"请求延迟: {delay}秒")
            self.log(f"最大退避时间: {max_backoff}秒")
            self.log("使用指数退避算法处理API限制")
            
            # 在新线程中启动处理
            print(f"[INFO] 启动处理线程，参数: delay={delay}, max_backoff={max_backoff}, comment_style={comment_style}")
            threading.Thread(
                target=self.process_files,
                args=(folder, output, recursive, api_key, file_filter, delay, max_backoff, comment_style),
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"[ERROR] 启动处理时出错: {e}")
            import traceback
            traceback.print_exc()
            self.show_message("错误", f"启动处理时出错: {str(e)}", True)
            self.is_processing = False
    
    def process_files(self, folder, output, recursive, api_key, file_filter="*.py", delay=6.0, max_backoff=64.0, comment_style="line_end"):
        """处理选定的文件夹中的文件（在单独的线程中运行）"""
        print(f"[INFO] 开始处理文件: 当前线程ID={threading.get_ident()}, 主线程ID={threading.main_thread().ident}")
        print(f"[INFO] 是否在主线程中: {threading.current_thread() is threading.main_thread()}")
        
        try:
            # 确保我们有有效的延迟和最大回退时间值
            if delay is None or delay < 0:
                print("[WARNING] 延迟值无效，使用默认值 1.0")
                delay = 1.0
            
            if max_backoff is None or max_backoff <= 0:
                print("[WARNING] 最大回退时间值无效，使用默认值 60.0")
                max_backoff = 60.0
                
            print(f"[INFO] 使用延迟={delay}秒, 最大回退时间={max_backoff}秒, 注释风格={comment_style}")
            
            # 构建命令
            command = [
                "python", 
                "gemini_commenter.py",
                "--folder", folder,
                "--output", output,
                "--delay", str(delay),
                "--max-backoff", str(max_backoff)
            ]
            
            # 添加递归参数
            if recursive:
                command.append("--recursive")
                
            # 添加文件过滤参数
            if file_filter and file_filter != "*.py":
                command.extend(["--filter", file_filter])
                
            # 添加注释风格参数
            command.extend(["--comment-style", comment_style])
            
            print(f"[INFO] 执行命令: {' '.join(command)}")
            
            # 设置环境变量
            env = os.environ.copy()
            env["GEMINI_API_KEY"] = api_key
            
            # 运行命令并处理输出
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            # 使用计数器而不是直接访问进度条
            processed_count = 0
            total_files = 0
            
            # 读取输出
            for line in process.stdout:
                line = line.strip()
                # 只记录重要的输出行
                if "ERROR" in line or "WARNING" in line or "Processing" in line or "Completed" in line or "Successfully" in line:
                    print(f"[OUTPUT] {line}")
                
                # 添加到日志
                self.queue.put(("log", line))
                
                # 检查是否找到了文件总数 - 同时支持中英文
                if ("Found" in line and "files" in line) or ("找到" in line and "个Python文件" in line) or ("找到" in line and "个文件" in line):
                    try:
                        # 尝试从不同格式的输出中提取文件数量
                        if "Found" in line and "files" in line:
                            # 英文格式: "Found 2 files"
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == "Found" and i+1 < len(parts):
                                    try:
                                        total_files = int(parts[i+1])
                                        break
                                    except:
                                        pass
                        else:
                            # 中文格式: "找到 2 个Python文件" 或 "找到 2 个文件"
                            total_files = int(line.split("找到")[1].split("个")[0].strip())
                        
                        if total_files > 0:
                            self.queue.put(("progress_max", total_files))
                            self.queue.put(("status", f"处理 {total_files} 个文件..."))
                            print(f"[INFO] 设置总文件数: {total_files}")
                    except Exception as e:
                        print(f"[ERROR] 解析文件总数时出错: {e}")
                
                # 检查是否处理了新文件 - 同时支持中英文
                elif ("Completed" in line and "->" in line) or ("已完成" in line) or ("Processing completed" in line and "successfully" in line):
                    # 如果是处理完成的总结行，提取总数
                    if "Processing completed" in line and "successfully" in line:
                        try:
                            # 格式: "Processing completed: 2/2 files successfully commented"
                            parts = line.split(":")
                            if len(parts) > 1:
                                fraction = parts[1].split("files")[0].strip()
                                success, total = fraction.split("/")
                                processed_count = int(success.strip())
                                if total_files == 0:  # 如果之前没有设置总数
                                    total_files = int(total.strip())
                                    self.queue.put(("progress_max", total_files))
                        except Exception as e:
                            print(f"[ERROR] 解析处理完成信息时出错: {e}")
                    else:
                        # 单个文件处理完成
                        processed_count += 1
                        
                    # 更新进度
                    self.queue.put(("progress", processed_count))
                    if total_files > 0:
                        self.queue.put(("status", f"已处理 {processed_count}/{total_files} 个文件"))
                    else:
                        self.queue.put(("status", f"已处理 {processed_count} 个文件"))
                    print(f"[INFO] 更新处理计数: {processed_count}/{total_files}")
            
            # 等待进程完成
            return_code = process.wait()
            
            # 处理完成
            if return_code == 0:
                if total_files > 0:
                    self.queue.put(("status", f"成功处理了 {processed_count}/{total_files} 个文件"))
                    self.queue.put(("message", ("处理完成", f"成功处理了 {processed_count}/{total_files} 个文件", False)))
                else:
                    self.queue.put(("status", f"成功处理了 {processed_count} 个文件"))
                    self.queue.put(("message", ("处理完成", f"成功处理了 {processed_count} 个文件", False)))
            else:
                self.queue.put(("status", f"处理完成，但有错误 (返回码: {return_code})"))
                self.queue.put(("message", ("处理错误", f"处理完成，但有错误 (返回码: {return_code})", True)))
            
        except Exception as e:
            print(f"[ERROR] 处理文件时出错: {e}")
            import traceback
            traceback.print_exc()
            self.queue.put(("status", "处理时出错"))
            self.queue.put(("message", ("处理错误", f"处理文件时出错: {str(e)}", True)))
        
        finally:
            # 通知主线程处理已完成
            print("[INFO] 文件处理完成")
            self.queue.put(("processing_done", None))
    
    def stop_processing(self):
        """停止处理"""
        if not self.is_processing:
            return
        
        # 使用队列更新状态，避免线程问题
        self.queue.put(("status", "已停止"))
        self.log("处理已停止")
        self.queue.put(("message", ("已停止", "处理已停止", False)))
        self.is_processing = False
    
    def open_output_folder(self):
        """打开输出文件夹"""
        # 获取输出文件夹路径
        output_folder = self.output_entry.get().strip()
        
        # 使用队列处理，避免线程问题
        def handle_open_folder():
            if not output_folder:
                messagebox.showerror("错误", "未设置输出文件夹")
                return
                
            if not os.path.exists(output_folder):
                try:
                    os.makedirs(output_folder)
                    self.log(f"已创建输出文件夹: {output_folder}")
                except Exception as e:
                    messagebox.showerror("错误", f"创建输出文件夹时出错: {e}")
                    return
            
            # 根据操作系统打开文件夹
            try:
                if sys.platform == 'win32':
                    os.startfile(output_folder)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', output_folder])
                else:  # Linux
                    subprocess.run(['xdg-open', output_folder])
            except Exception as e:
                messagebox.showerror("错误", f"打开输出文件夹时出错: {e}")
        
        # 确保在主线程中执行
        self.root.after_idle(handle_open_folder)
    
    def show_api_settings(self):
        """显示API设置对话框"""
        # 确保在主线程中执行
        def show_dialog():
            dialog = tk.Toplevel(self.root)
            dialog.title("API密钥设置")
            dialog.geometry("500x200")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            dialog.grab_set()
            
            frame = ttk.Frame(dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="请输入您的Gemini API密钥:", font=("Arial", 12)).pack(pady=(0, 10))
            
            api_frame = ttk.Frame(frame)
            api_frame.pack(fill=tk.X, pady=5)
            
            api_entry = ttk.Entry(api_frame, width=50, show="*")
            api_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            if self.api_key:
                api_entry.insert(0, self.api_key)
            
            show_var = tk.BooleanVar(value=False)
            
            def toggle_show():
                if show_var.get():
                    api_entry.config(show="")
                else:
                    api_entry.config(show="*")
            
            ttk.Checkbutton(api_frame, text="显示", variable=show_var, command=toggle_show).pack(side=tk.LEFT, padx=5)
            
            ttk.Label(frame, text="获取API密钥: https://ai.google.dev/", foreground="blue").pack(pady=10)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=10)
            
            def save_and_close():
                api_key = api_entry.get().strip()
                if api_key:
                    self.api_entry.delete(0, tk.END)
                    self.api_entry.insert(0, api_key)
                    self.save_api_key()
                    dialog.destroy()
                else:
                    messagebox.showerror("错误", "API密钥不能为空", parent=dialog)
            
            ttk.Button(btn_frame, text="保存", command=save_and_close).pack(side=tk.RIGHT, padx=5)
            ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 在主线程中执行
        self.root.after_idle(show_dialog)
    
    def change_theme(self, theme):
        """切换主题"""
        try:
            import sv_ttk
            sv_ttk.set_theme(theme)
            self.log(f"已切换到{theme}主题")
        except Exception as e:
            self.log(f"切换主题时出错: {e}")
    
    def show_help(self):
        """显示帮助信息"""
        # 确保在主线程中执行
        def show_help_window():
            help_text = """
Python代码自动注释工具使用说明

基本功能:
- 使用Google Gemini API为Python代码添加中文注释
- 支持批量处理整个文件夹中的Python文件
- 可以递归处理子文件夹
- 保留原始代码格式和结构

使用步骤:
1. 设置有效的Gemini API密钥
2. 选择包含Python文件的源文件夹
3. 指定输出文件夹
4. 设置是否递归处理子文件夹
5. 设置文件过滤器(默认为*.py)
6. 设置API速率限制参数(避免超出免费限额)
7. 点击"开始处理"按钮

速率限制说明:
- 请求延迟: 每个API请求之间的基础等待时间(秒)
- 最大退避时间: 遇到API限制时的最大等待时间(秒)
- 系统会自动使用指数退避算法处理API限制

注意事项:
- 需要有效的Google Gemini API密钥
- 处理大型文件可能需要较长时间
- 请确保网络连接稳定
- 系统会自动处理API限制，避免超出免费限额

更多信息请访问: https://ai.google.dev/
            """
            
            help_window = tk.Toplevel(self.root)
            help_window.title("使用说明")
            help_window.geometry("600x500")
            help_window.minsize(500, 400)
            
            # 设置图标（如果有）
            try:
                if os.path.exists("icon.ico"):
                    help_window.iconbitmap("icon.ico")
            except:
                pass
            
            # 创建滚动文本区域
            text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # 插入帮助文本
            text_area.insert(tk.END, help_text)
            text_area.config(state=tk.DISABLED)
            
            # 关闭按钮
            ttk.Button(help_window, text="关闭", command=help_window.destroy).pack(pady=10)
        
        # 在主线程中执行
        self.root.after_idle(show_help_window)
    
    def show_about(self):
        """显示关于信息"""
        # 确保在主线程中执行
        def show_about_dialog():
            about_text = """
Python代码自动注释工具

版本: 1.0.0

这是一个使用Google Gemini API自动为Python文件添加逐行中文注释的工具。

功能特点:
- 自动扫描指定文件夹中的Python文件
- 使用Gemini AI为每个文件生成逐行中文注释
- 支持递归处理子文件夹
- 保留原始代码结构，只添加注释
- 输出到单独的文件夹，不修改原始文件
- 提供图形用户界面(GUI)
- 自动从环境变量中提取API密钥

需要有效的Gemini API密钥才能使用此工具。
"""
            messagebox.showinfo("关于", about_text)
        
        # 在主线程中执行
        self.root.after_idle(show_about_dialog)
    
    def on_closing(self):
        """关闭窗口时的处理"""
        # 确保在主线程中执行
        def handle_closing():
            if self.is_processing:
                if messagebox.askyesno("确认", "处理任务正在进行中，确定要退出吗？"):
                    self.stop_processing()
                    self.root.destroy()
            else:
                self.root.destroy()
        
        # 在主线程中执行
        self.root.after_idle(handle_closing)
    
    def clear_log(self):
        """清空日志"""
        # 确保在主线程中执行
        def clear_log_text():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        # 在主线程中执行
        self.root.after_idle(clear_log_text)

def main():
    """主函数"""
    try:
        print("\n" + "="*50)
        print(f"[INFO] 启动Gemini代码注释器GUI")
        print(f"[INFO] Python版本: {sys.version}")
        print(f"[INFO] 操作系统: {platform.system()} {platform.release()} ({platform.platform()})")
        print(f"[INFO] 当前线程ID: {threading.get_ident()}, 主线程ID: {threading.main_thread().ident}")
        print(f"[INFO] 是否在主线程中: {threading.current_thread() is threading.main_thread()}")
        print("="*50 + "\n")
        
        # 检查是否在主线程中运行
        if threading.current_thread() is not threading.main_thread():
            print("[ERROR] GUI必须在主线程中运行")
            messagebox.showerror("错误", "GUI必须在主线程中运行")
            return
        
        # 检查必要的依赖
        try:
            import tkinter
            print(f"[INFO] Tkinter版本: {tkinter.TkVersion}")
        except ImportError:
            print("[ERROR] 未找到Tkinter库")
            messagebox.showerror("错误", "未找到Tkinter库，请确保已安装Python的Tkinter支持")
            return
        
        # 创建根窗口
        root = tk.Tk()
        
        # 尝试设置主题
        try:
            style = ttk.Style()
            available_themes = style.theme_names()
            print(f"[INFO] 可用的Tkinter主题: {', '.join(available_themes)}")
            
            # 尝试使用clam主题，如果可用
            if 'clam' in available_themes:
                style.theme_use('clam')
                print("[INFO] 使用'clam'主题")
            else:
                print(f"[INFO] 使用默认主题: {style.theme_use()}")
        except Exception as e:
            print(f"[WARNING] 设置主题时出错: {e}")
        
        # 创建应用
        app = GeminiCommenterGUI(root)
        
        # 运行应用
        print("[INFO] 开始运行GUI主循环")
        root.mainloop()
        print("[INFO] GUI主循环已退出")
        
    except Exception as e:
        print(f"[ERROR] 运行GUI时出错: {e}")
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("错误", f"运行GUI时出错: {str(e)}")
        except:
            print("[ERROR] 无法显示错误对话框")

if __name__ == "__main__":
    main() 