import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import datetime
import sys
from tkcalendar import Calendar  # 需安装：pip install tkcalendar

# 检查可选依赖
HAS_PIL = False
HAS_WIN32 = False
try:
    from PIL import Image, ImageTk

    HAS_PIL = True
except ImportError:
    pass

try:
    import win32clipboard

    HAS_WIN32 = True
except ImportError:
    pass


def get_data_directory():
    """获取数据存储目录，优先使用用户文档目录"""
    if getattr(sys, 'frozen', False):
        # 打包后的环境：使用可执行文件所在目录
        base_dir = os.path.dirname(sys.executable)
    else:
        # 开发环境：使用脚本所在目录
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 创建数据目录
    data_dir = os.path.join(base_dir, "todo_data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    return data_dir


class TodoListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("任务清单 - 共 0 个任务")
        self.root.geometry("900x700")
        self.root.minsize(400, 300)

        # 初始化Treeview的tag样式和行高
        self.init_tags()

        # 任务数据
        self.tasks = []
        self.task_count = 0
        self.max_tasks = 100
        self.is_topmost = False
        self.editing_index = -1
        self.simple_mode = False

        # 激励配置
        self.reward_config = {
            "enabled": True,
            "messages": ["太棒了！完成任务超高效～", "又攻克一个目标，继续加油！", "执行力拉满，值得奖励自己～"],
            "popup": True
        }

        # 配置文件路径 - 使用新的路径获取方法
        data_dir = get_data_directory()
        self.data_file = os.path.join(data_dir, "todo_data.json")
        self.config_file = os.path.join(data_dir, "todo_config.json")
        self.reward_config_file = os.path.join(data_dir, "reward_config.json")

        # 照片存储目录
        self.photo_dir = os.path.join(data_dir, "todo_photos")
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)

        # 创建界面
        self.create_widgets()

        # 加载配置和任务
        self.load_config()
        self.load_tasks()
        self.load_reward_config()

        # 设置窗口置顶
        if self.is_topmost:
            self.root.attributes('-topmost', True)

        # 关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def init_tags(self):
        """初始化Treeview的tag样式和行高（修复颜色显示）"""
        self.style = ttk.Style()
        # 行高调整为50（平衡显示完整度和间距）
        self.style.configure("Treeview", rowheight=50)
        self.task_tree = None  # 预留Treeview实例

    def create_widgets(self):
        # 字体配置
        self.title_font = ("Microsoft YaHei", 14, "bold")
        self.normal_font = ("Microsoft YaHei", 10)
        self.small_font = ("Microsoft YaHei", 9)

        # 主框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 网格权重配置
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(3, weight=1)

        # 标题
        title_label = tk.Label(self.main_frame, text="任务清单管理系统（优先级颜色区分）",
                               font=self.title_font, bg="white")
        title_label.grid(row=0, column=0, columnspan=8, pady=(0, 15), sticky="ew")

        # 任务输入区域
        tk.Label(self.main_frame, text="任务描述:", font=self.normal_font).grid(row=1, column=0, sticky="w",
                                                                                padx=(0, 5))
        self.task_entry = tk.Entry(self.main_frame, font=self.normal_font)
        self.task_entry.grid(row=1, column=1, sticky="ew", padx=5)

        tk.Label(self.main_frame, text="优先级:", font=self.normal_font).grid(row=1, column=2, sticky="w", padx=(10, 5))
        self.priority_var = tk.StringVar(value="中")
        priority_combo = ttk.Combobox(self.main_frame, textvariable=self.priority_var,
                                      values=["低", "中", "高"], state="readonly", width=8)
        priority_combo.grid(row=1, column=3, padx=5)

        tk.Label(self.main_frame, text="截止日期:", font=self.normal_font).grid(row=1, column=4, sticky="w",
                                                                                padx=(10, 5))
        self.date_entry = tk.Entry(self.main_frame, width=12, font=self.normal_font)
        self.date_entry.grid(row=1, column=5, padx=5)

        # 日期选择按钮
        tk.Button(self.main_frame, text="选择日期", command=self.choose_date,
                  font=self.normal_font, width=8).grid(row=1, column=6, padx=5)

        # 粘贴照片按钮（仅Windows且有依赖时显示）
        if sys.platform.startswith('win32') and HAS_PIL and HAS_WIN32:
            tk.Button(self.main_frame, text="粘贴照片", command=self.add_photo_to_task,
                      font=self.normal_font, bg="#795548", fg="white", width=8).grid(row=1, column=7, padx=5)

        # 按钮区域
        button_frame = tk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, columnspan=8, pady=10, sticky="ew")
        for i in range(11):  # 增加一列
            button_frame.columnconfigure(i, weight=1)

        # 操作按钮
        tk.Button(button_frame, text="添加任务", command=self.add_task,
                  font=self.normal_font, bg="#4CAF50", fg="white").grid(row=0, column=0, padx=2, sticky="ew")
        tk.Button(button_frame, text="编辑任务", command=self.edit_task,
                  font=self.normal_font, bg="#2196F3", fg="white").grid(row=0, column=1, padx=2, sticky="ew")
        tk.Button(button_frame, text="标记完成", command=self.toggle_complete,
                  font=self.normal_font, bg="#FF9800", fg="white").grid(row=0, column=2, padx=2, sticky="ew")
        tk.Button(button_frame, text="删除任务", command=self.delete_task,
                  font=self.normal_font, bg="#F44336", fg="white").grid(row=0, column=3, padx=2, sticky="ew")
        tk.Button(button_frame, text="隐藏任务", command=self.hide_task,
                  font=self.normal_font, bg="#9C27B0", fg="white").grid(row=0, column=4, padx=2, sticky="ew")
        # 新增：取消隐藏按钮
        tk.Button(button_frame, text="取消隐藏", command=self.unhide_task,
                  font=self.normal_font, bg="#FF9800", fg="white").grid(row=0, column=5, padx=2, sticky="ew")

        # 搜索区域
        tk.Label(button_frame, text="搜索:", font=self.normal_font).grid(row=0, column=6, padx=(10, 5))
        self.search_entry = tk.Entry(button_frame, font=self.normal_font)
        self.search_entry.grid(row=0, column=7, padx=5, sticky="ew")
        tk.Button(button_frame, text="搜索", command=self.search_tasks,
                  font=self.normal_font).grid(row=0, column=8, padx=2, sticky="ew")
        tk.Button(button_frame, text="统计", command=self.show_statistics,
                  font=self.normal_font).grid(row=0, column=9, padx=2, sticky="ew")
        tk.Button(button_frame, text="管理任务", command=self.manage_tasks,
                  font=self.normal_font).grid(row=0, column=10, padx=2, sticky="ew")

        # 任务列表框架
        list_frame = tk.Frame(self.main_frame)
        list_frame.grid(row=3, column=0, columnspan=8, pady=10, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 创建Treeview
        columns = ("状态", "任务描述", "优先级", "创建日期", "截止日期", "隐藏状态")
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=18)

        # 设置列标题和宽度
        for col in columns:
            self.task_tree.heading(col, text=col)
        self.task_tree.column("状态", width=60, anchor="center")
        self.task_tree.column("任务描述", width=350)
        self.task_tree.column("优先级", width=70, anchor="center")
        self.task_tree.column("创建日期", width=90, anchor="center")
        self.task_tree.column("截止日期", width=90, anchor="center")
        self.task_tree.column("隐藏状态", width=70, anchor="center")

        # 关键修复：配置Treeview标签颜色（确保显示）
        self.task_tree.tag_configure("completed", foreground='gray', background='#f0f0f0')
        self.task_tree.tag_configure("high", background='#ffebee')  # 高优先级：浅红
        self.task_tree.tag_configure("medium", background='#fff3e0')  # 中优先级：浅橙
        self.task_tree.tag_configure("low", background='#e8f5e9')  # 低优先级：浅绿
        self.task_tree.tag_configure("overdue", background='#ffcdd2', foreground='#b71c1c')  # 超期：深红红字

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        self.task_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 绑定双击事件
        self.task_tree.bind("<Double-1>", self.on_double_click)

        # 底部按钮框架
        bottom_frame = tk.Frame(self.main_frame)
        bottom_frame.grid(row=4, column=0, columnspan=8, pady=10, sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)
        bottom_frame.columnconfigure(2, weight=1)
        bottom_frame.columnconfigure(3, weight=1)

        # 开机自启（仅Windows显示）
        if sys.platform.startswith('win32'):
            tk.Button(bottom_frame, text="开机自启动", command=self.setup_autostart,
                      font=self.normal_font).grid(row=0, column=0, padx=5, sticky="w")

        tk.Button(bottom_frame, text="关于", command=self.show_about,
                  font=self.normal_font).grid(row=0, column=1, padx=5)
        self.topmost_button = tk.Button(bottom_frame, text="窗口置顶", command=self.toggle_topmost,
                                        font=self.normal_font)
        self.topmost_button.grid(row=0, column=2, padx=5)
        self.simple_mode_button = tk.Button(bottom_frame, text="简洁模式", command=self.toggle_simple_mode,
                                            font=self.normal_font, bg="#009688", fg="white")
        self.simple_mode_button.grid(row=0, column=3, padx=5, sticky="e")

        # 初始化状态
        self.update_topmost_button()
        self.task_entry.bind("<Return>", lambda e: self.add_task())
        self.search_entry.bind("<Return>", lambda e: self.search_tasks())
        self.create_simple_mode_frame()

    def should_show_task(self, task):
        """判断任务是否显示：代码2中的自动隐藏功能"""
        if task['manually_hidden']:
            return False
        if not task['completed']:
            return True
        # 已完成任务：检查是否超过两天
        if not task['completed_date']:
            return True
        try:
            completed_date = datetime.datetime.strptime(task['completed_date'], "%Y-%m-%d").date()
            days_passed = (datetime.date.today() - completed_date).days
            return days_passed < 2  # 两天内显示，超过两天自动隐藏
        except:
            return True

    def wrap_text(self, text, line_length=40):
        """长文本自动换行（不截断，完整显示所有文字）"""
        if not text:
            return ""
        words = text.split()
        wrapped = []
        current_line = ""
        for word in words:
            if len(word) > line_length:
                # 超长单词分段显示（确保每个字符都显示）
                for i in range(0, len(word), line_length):
                    wrapped.append(word[i:i + line_length])
                current_line = ""
            elif len(current_line) + len(word) + 1 <= line_length:
                current_line += f" {word}" if current_line else word
            else:
                wrapped.append(current_line)
                current_line = word
        if current_line:
            wrapped.append(current_line)
        return "\n".join(wrapped)

    def on_double_click(self, event):
        """双击事件：切换任务状态"""
        tree = event.widget
        selected_items = tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        try:
            original_index = int(item)
            if 0 <= original_index < len(self.tasks):
                self.tasks[original_index]['completed'] = not self.tasks[original_index]['completed']
                if self.tasks[original_index]['completed']:
                    self.tasks[original_index]['completed_date'] = datetime.datetime.now().strftime("%Y-%m-%d")
                else:
                    self.tasks[original_index]['completed_date'] = ""

                self.sort_tasks()
                self.show_all_tasks()
                if self.simple_mode:
                    self.update_simple_mode_display()
                self.save_tasks()
                self.show_reward()

        except (ValueError, IndexError) as e:
            messagebox.showerror("错误", f"双击处理失败：{str(e)}")

    def add_task_to_gui(self, index):
        """添加任务到列表（完整显示任务描述）"""
        task = self.tasks[index]
        status = "已完成" if task['completed'] else "待完成"
        wrapped_desc = self.wrap_text(task['description'])  # 仅换行不截断
        priority_text = {1: "低", 2: "中", 3: "高"}[task['priority']]
        create_date = task['create_date']
        due_date = task['due_date'] if task['due_date'] != "无" else "无截止日期"
        hidden_status = "已隐藏" if task['manually_hidden'] else "显示中"

        # 超期判断
        is_overdue = False
        if not task['completed'] and task['due_date'] != "无":
            try:
                due_date_obj = datetime.datetime.strptime(task['due_date'], "%Y-%m-%d").date()
                if due_date_obj < datetime.date.today():
                    is_overdue = True
            except:
                pass

        # 优先级颜色标签
        if is_overdue:
            tag = 'overdue'
        else:
            tag = 'completed' if task['completed'] else 'high' if task['priority'] == 3 else 'medium' if task[
                                                                                                             'priority'] == 2 else 'low'

        # 插入列表
        if self.should_show_task(task):
            self.task_tree.insert("", "end", iid=str(index), values=(
                status, wrapped_desc, priority_text, create_date, due_date, hidden_status
            ), tags=(tag,))

    def create_simple_mode_frame(self):
        """简洁模式框架（支持完整显示任务描述）"""
        self.simple_frame = tk.Frame(self.root)
        self.simple_frame.columnconfigure(0, weight=1)
        self.simple_frame.rowconfigure(1, weight=1)

        tk.Label(self.simple_frame, text="简洁模式 - 待办任务（完整描述）",
                 font=("Microsoft YaHei", 12, "bold"), bg="white").grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        list_container = tk.Frame(self.simple_frame)
        list_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        self.simple_scrollbar = tk.Scrollbar(list_container)
        self.simple_scrollbar.grid(row=0, column=1, sticky="ns")
        self.simple_canvas = tk.Canvas(list_container, yscrollcommand=self.simple_scrollbar.set,
                                       bg="white", highlightthickness=0)
        self.simple_canvas.grid(row=0, column=0, sticky="nsew")
        self.simple_scrollbar.config(command=self.simple_canvas.yview)

        self.simple_inner_frame = tk.Frame(self.simple_canvas, bg="white")
        self.simple_canvas_window = self.simple_canvas.create_window((0, 0), window=self.simple_inner_frame,
                                                                     anchor="nw")

        self.simple_inner_frame.bind("<Configure>", lambda e: self.simple_canvas.configure(
            scrollregion=self.simple_canvas.bbox("all")))
        self.simple_canvas.bind("<Configure>",
                                lambda e: self.simple_canvas.itemconfig(self.simple_canvas_window, width=e.width))
        self.simple_canvas.bind("<MouseWheel>",
                                lambda e: self.simple_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.simple_inner_frame.bind("<MouseWheel>",
                                     lambda e: self.simple_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        simple_bottom_frame = tk.Frame(self.simple_frame)
        simple_bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        tk.Button(simple_bottom_frame, text="返回完整模式", command=self.toggle_simple_mode,
                  font=self.small_font, bg="#FF5722", fg="white").pack(side=tk.LEFT, padx=5)
        self.simple_topmost_button = tk.Button(simple_bottom_frame, text="窗口置顶", command=self.toggle_topmost,
                                               font=self.small_font)
        self.simple_topmost_button.pack(side=tk.RIGHT, padx=5)

        self.simple_frame.pack_forget()

    def update_simple_mode_display(self):
        """更新简洁模式（完整显示任务描述，不省略任何字符）"""
        for widget in self.simple_inner_frame.winfo_children():
            widget.destroy()

        # 使用should_show_task过滤任务
        pending_tasks = [(i, t) for i, t in enumerate(self.tasks) if self.should_show_task(t) and not t['completed']]
        pending_tasks.sort(key=lambda x: x[1]['priority'], reverse=True)

        for i, (idx, task) in enumerate(pending_tasks):
            var = tk.BooleanVar()
            # 任务卡片：增加边框和间距，区分不同任务
            task_frame = tk.Frame(self.simple_inner_frame, bg="white", relief="solid", bd=2, padx=5, pady=5)
            task_frame.pack(fill=tk.X, padx=5, pady=8)  # 增大垂直间距，增强区分度

            content_frame = tk.Frame(task_frame, bg="white")
            content_frame.pack(fill=tk.X, padx=5, pady=3)

            # 顶部：优先级+复选框+截止日期+照片标识
            top_frame = tk.Frame(content_frame, bg="white")
            top_frame.pack(fill=tk.X)
            priority_color = "#F44336" if task['priority'] == 3 else "#FF9800" if task['priority'] == 2 else "#4CAF50"
            priority_text = {1: "低", 2: "中", 3: "高"}[task['priority']]
            tk.Frame(top_frame, width=4, height=18, bg=priority_color).pack(side=tk.LEFT, padx=(0, 8))
            tk.Checkbutton(top_frame, variable=var, command=lambda x=idx: self.complete_task_simple(x),
                           font=self.small_font, bg="white").pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(top_frame, text=f"[{priority_text}优先级]", font=self.small_font, bg="white").pack(side=tk.LEFT,
                                                                                                        padx=(0, 15))
            if task['due_date'] and task['due_date'] != "无":
                tk.Label(top_frame, text=f"截止: {task['due_date']}", font=("Microsoft YaHei", 8), fg="gray",
                         bg="white").pack(side=tk.LEFT, padx=(0, 15))
            if 'photo_path' in task and task['photo_path'] and os.path.exists(task['photo_path']):
                tk.Label(top_frame, text="📷", font=self.small_font, bg="white").pack(side=tk.RIGHT, padx=5)

            # 任务描述：完整显示所有文字，自动换行（关键修复）
            desc_label = tk.Label(
                content_frame,
                text=task['description'],  # 直接使用完整描述，不做任何截断
                font=self.small_font,
                bg="white",
                anchor="w",
                wraplength=600,  # 根据窗口宽度自动换行
                justify="left"
            )
            desc_label.pack(fill=tk.X, padx=30, pady=5)  # 增加内边距，优化显示

        if not pending_tasks:
            empty_frame = tk.Frame(self.simple_inner_frame, bg="white", height=100)
            empty_frame.pack(fill=tk.X, expand=True)
            empty_frame.pack_propagate(False)
            tk.Label(empty_frame, text="🎉 没有待办任务，休息一下吧！", font=self.normal_font, fg="gray", bg="white").pack(
                expand=True)

    def complete_task_simple(self, task_index):
        """简洁模式完成任务"""
        self.tasks[task_index]['completed'] = True
        self.tasks[task_index]['completed_date'] = datetime.datetime.now().strftime("%Y-%m-%d")
        self.save_tasks()
        self.update_simple_mode_display()
        self.update_task_count()
        self.show_reward()
        if not self.simple_mode:
            self.sort_tasks()
            self.show_all_tasks()

    def toggle_simple_mode(self):
        """切换简洁模式"""
        self.simple_mode = not self.simple_mode
        if self.simple_mode:
            self.main_frame.pack_forget()
            self.simple_frame.pack(fill=tk.BOTH, expand=True)
            self.simple_mode_button.config(text="完整模式", bg="#FF5722")
            self.update_simple_mode_display()
            self.update_simple_topmost_button()
            self.root.minsize(300, 200)
        else:
            self.simple_frame.pack_forget()
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            self.simple_mode_button.config(text="简洁模式", bg="#009688")
            self.root.minsize(750, 550)
            self.show_all_tasks()

    def update_simple_topmost_button(self):
        """更新简洁模式置顶按钮"""
        if self.is_topmost:
            self.simple_topmost_button.config(text="取消置顶", bg="#FF5722", fg="white")
        else:
            self.simple_topmost_button.config(text="窗口置顶", bg="#607D8B", fg="white")

    def choose_date(self):
        top = tk.Toplevel(self.root)
        top.title("选择日期")
        top.geometry("300x300")
        top.transient(self.root)
        top.grab_set()

        today = datetime.date.today()
        cal = Calendar(top, selectmode='day', year=today.year, month=today.month, day=today.day, date_pattern='y-mm-dd')
        cal.pack(pady=20)

        def set_date():
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, cal.get_date())
            top.destroy()

        tk.Button(top, text="确定", command=set_date, font=self.normal_font).pack(pady=10)

    def load_tasks(self):
        try:
            # 确保数据目录存在
            data_dir = os.path.dirname(self.data_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)

            if not os.path.exists(self.data_file):
                # 创建空数据文件
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump({'tasks': []}, f, ensure_ascii=False, indent=2)
                self.tasks = []
                self.task_count = 0
            else:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    self.task_count = len(self.tasks)

                for task in self.tasks:
                    if 'completed_date' not in task:
                        task['completed_date'] = ""
                    if 'manually_hidden' not in task:
                        task['manually_hidden'] = False
                    if 'photo_path' not in task:
                        task['photo_path'] = ""

                self.sort_tasks()
                self.show_all_tasks()
        except Exception as e:
            messagebox.showerror("错误", f"加载任务失败: {str(e)}\n数据文件路径: {self.data_file}")

    def save_tasks(self):
        try:
            # 确保数据目录存在
            data_dir = os.path.dirname(self.data_file)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({'tasks': self.tasks}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存任务失败: {str(e)}\n数据文件路径: {self.data_file}")

    def load_config(self):
        try:
            if not os.path.exists(self.config_file):
                default_config = {
                    'geometry': '900x700+100+100',
                    'topmost': False,
                    'simple_mode': False
                }
                with open(self.config_file, 'w') as f:
                    json.dump(default_config, f, indent=2)

            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.root.geometry(config.get('geometry', '900x700+100+100'))
                self.is_topmost = config.get('topmost', False)
                self.simple_mode = config.get('simple_mode', False)
                if self.simple_mode:
                    self.root.after(100, self.toggle_simple_mode)
        except Exception as e:
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")

    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump({
                    'geometry': self.root.geometry(),
                    'topmost': self.is_topmost,
                    'simple_mode': self.simple_mode
                }, f, indent=2)
        except Exception:
            pass

    def load_reward_config(self):
        try:
            if os.path.exists(self.reward_config_file):
                with open(self.reward_config_file, 'r', encoding='utf-8') as f:
                    self.reward_config.update(json.load(f))
        except:
            pass

    def save_reward_config(self):
        try:
            with open(self.reward_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.reward_config, f, ensure_ascii=False, indent=2)
        except:
            messagebox.showerror("错误", "保存激励配置失败")

    def open_reward_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("任务激励设置")
        settings_win.geometry("400x300")
        settings_win.transient(self.root)

        tk.Label(settings_win, text="启用任务激励:", font=self.normal_font).pack(pady=5)
        enable_var = tk.BooleanVar(value=self.reward_config["enabled"])
        tk.Checkbutton(settings_win, variable=enable_var, text="完成任务后显示激励", font=self.normal_font).pack()

        tk.Label(settings_win, text="激励文案（每行一条）:", font=self.normal_font).pack(pady=5)
        text_box = tk.Text(settings_win, height=6, font=self.normal_font)
        text_box.pack(padx=10, fill=tk.X)
        text_box.insert(tk.END, "\n".join(self.reward_config["messages"]))

        popup_var = tk.BooleanVar(value=self.reward_config["popup"])
        tk.Checkbutton(settings_win, variable=popup_var, text="弹窗显示激励（否则状态栏显示）",
                       font=self.normal_font).pack(pady=5)

        def save_settings():
            self.reward_config["enabled"] = enable_var.get()
            self.reward_config["messages"] = [line.strip() for line in text_box.get("1.0", tk.END).splitlines() if
                                              line.strip()]
            self.reward_config["popup"] = popup_var.get()
            self.save_reward_config()
            messagebox.showinfo("成功", "激励配置已保存")
            settings_win.destroy()

        tk.Button(settings_win, text="保存", command=save_settings, font=self.normal_font, bg="#4CAF50",
                  fg="white").pack(pady=10)

    def show_reward(self):
        if not self.reward_config["enabled"] or not self.reward_config["messages"]:
            return
        import random
        msg = random.choice(self.reward_config["messages"])
        if self.reward_config["popup"]:
            messagebox.showinfo("任务完成！", msg)
        else:
            status_var = tk.StringVar(value=msg)
            status_label = tk.Label(self.main_frame, textvariable=status_var, font=self.small_font, fg="#4CAF50")
            status_label.grid(row=6, column=0, pady=5)
            self.root.after(3000, status_label.destroy)

    def sort_tasks(self):
        self.tasks.sort(key=lambda x: (
            x['manually_hidden'],
            x['completed'],
            -x['priority'],
            -datetime.datetime.strptime(x['create_date'], "%Y-%m-%d").timestamp()
        ))

    def show_all_tasks(self):
        """显示所有任务（使用should_show_task过滤）"""
        self.task_tree.delete(*self.task_tree.get_children())
        for i in range(len(self.tasks)):
            if self.should_show_task(self.tasks[i]):
                self.add_task_to_gui(i)
        self.update_task_count()

    def add_task(self):
        desc = self.task_entry.get().strip()
        if not desc:
            messagebox.showinfo("提示", "请输入任务描述!")
            return

        priority = {"低": 1, "中": 2, "高": 3}[self.priority_var.get()]
        due_date = self.date_entry.get().strip() or "无"
        if due_date != "无":
            try:
                datetime.datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("错误", "日期格式应为 YYYY-MM-DD!")
                return

        if self.editing_index >= 0:
            self.tasks[self.editing_index].update({
                'description': desc, 'priority': priority, 'due_date': due_date
            })
            self.editing_index = -1
        else:
            if self.task_count >= self.max_tasks:
                messagebox.showerror("错误", "任务数量已达上限!")
                return
            self.tasks.append({
                'description': desc, 'priority': priority, 'completed': False,
                'completed_date': "", 'manually_hidden': False,
                'due_date': due_date, 'create_date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'photo_path': ""
            })
            self.task_count += 1

        self.task_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.priority_var.set("中")
        self.sort_tasks()
        self.show_all_tasks()
        if self.simple_mode:
            self.update_simple_mode_display()
        self.update_task_count()
        self.save_tasks()
        self.task_entry.focus()

    def delete_task(self):
        """删除任务"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请选择要删除的任务!")
            return

        original_indices = []
        for item in selected:
            try:
                original_indices.append(int(item))
            except:
                messagebox.showerror("错误", "无法获取任务索引!")
                return
        original_indices.sort(reverse=True)

        if messagebox.askyesno("确认", "确定删除选中任务?"):
            for idx in original_indices:
                task = self.tasks[idx]
                if 'photo_path' in task and task['photo_path'] and os.path.exists(task['photo_path']):
                    try:
                        os.remove(task['photo_path'])
                    except:
                        pass
                del self.tasks[idx]
                self.task_count -= 1
            self.sort_tasks()
            self.show_all_tasks()
            if self.simple_mode:
                self.update_simple_mode_display()
            self.update_task_count()
            self.save_tasks()

    def edit_task(self):
        """编辑任务"""
        selected = self.task_tree.selection()
        if not selected or len(selected) > 1:
            messagebox.showinfo("提示", "请选择一个任务编辑!")
            return

        try:
            original_index = int(selected[0])
            task = self.tasks[original_index]
        except:
            messagebox.showerror("错误", "无法获取任务信息!")
            return

        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, task['description'])
        self.date_entry.delete(0, tk.END)
        if task['due_date'] != "无":
            self.date_entry.insert(0, task['due_date'])
        self.priority_var.set({1: "低", 2: "中", 3: "高"}[task['priority']])
        self.editing_index = original_index
        self.task_entry.focus()

    def toggle_complete(self):
        """标记完成"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请选择要标记的任务!")
            return

        for item in selected:
            try:
                original_index = int(item)
                self.tasks[original_index]['completed'] = not self.tasks[original_index]['completed']
                if self.tasks[original_index]['completed']:
                    self.tasks[original_index]['completed_date'] = datetime.datetime.now().strftime("%Y-%m-%d")
                else:
                    self.tasks[original_index]['completed_date'] = ""
            except:
                messagebox.showerror("错误", "标记任务失败!")
                return

        self.sort_tasks()
        self.show_all_tasks()
        if self.simple_mode:
            self.update_simple_mode_display()
        self.save_tasks()
        self.show_reward()

    def hide_task(self):
        """隐藏任务"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请选择要隐藏的任务!")
            return

        for item in selected:
            try:
                original_index = int(item)
                self.tasks[original_index]['manually_hidden'] = True
            except:
                messagebox.showerror("错误", "隐藏任务失败!")
                return

        self.show_all_tasks()
        if self.simple_mode:
            self.update_simple_mode_display()
        self.save_tasks()
        messagebox.showinfo("提示", "已隐藏选中任务")

    def unhide_task(self):
        """取消隐藏任务 - 新增功能"""
        # 在管理窗口中显示所有任务以便选择
        unhide_win = tk.Toplevel(self.root)
        unhide_win.title("取消隐藏任务")
        unhide_win.geometry("800x500")
        unhide_win.transient(self.root)
        unhide_win.grab_set()

        frame = tk.Frame(unhide_win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(frame, text="选择要取消隐藏的任务", font=self.title_font).pack(pady=10)

        # Treeview显示所有隐藏的任务
        columns = ("状态", "任务描述", "优先级", "创建日期", "截止日期")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        for col in columns:
            tree.heading(col, text=col)
        tree.column("状态", width=60, anchor="center")
        tree.column("任务描述", width=400)
        tree.column("优先级", width=70, anchor="center")
        tree.column("创建日期", width=90, anchor="center")
        tree.column("截止日期", width=90, anchor="center")

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 只显示手动隐藏的任务
        hidden_tasks = [(i, t) for i, t in enumerate(self.tasks) if t['manually_hidden']]
        for i, task in hidden_tasks:
            tree.insert("", "end", iid=str(i), values=(
                "已完成" if task['completed'] else "待完成",
                task['description'],
                {1: "低", 2: "中", 3: "高"}[task['priority']],
                task['create_date'],
                task['due_date']
            ))

        def unhide_selected():
            """取消隐藏选中的任务"""
            selected = tree.selection()
            if not selected:
                messagebox.showinfo("提示", "请选择要取消隐藏的任务!")
                return

            for item in selected:
                try:
                    idx = int(item)
                    self.tasks[idx]['manually_hidden'] = False
                except:
                    messagebox.showerror("错误", "取消隐藏失败!")
                    return

            self.show_all_tasks()
            if self.simple_mode:
                self.update_simple_mode_display()
            self.save_tasks()
            messagebox.showinfo("成功", "已取消隐藏选中任务")
            unhide_win.destroy()

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="取消隐藏选中任务", command=unhide_selected,
                  font=self.normal_font, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=unhide_win.destroy,
                  font=self.normal_font).pack(side=tk.LEFT, padx=5)

    def manage_tasks(self):
        manage_win = tk.Toplevel(self.root)
        manage_win.title("任务管理")
        manage_win.geometry("900x600")
        manage_win.transient(self.root)
        manage_win.grab_set()

        top_frame = tk.Frame(manage_win)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(top_frame, text="搜索任务:", font=self.normal_font).pack(side=tk.LEFT, padx=(0, 5))
        self.manage_search_entry = tk.Entry(top_frame, font=self.normal_font, width=30)
        self.manage_search_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="搜索", command=lambda: self.manage_search_tasks(tree), font=self.normal_font).pack(
            side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="清空",
                  command=lambda: (self.manage_search_entry.delete(0, tk.END), self.refresh_manage_tree(tree)),
                  font=self.normal_font).pack(side=tk.LEFT, padx=5)

        frame = tk.Frame(manage_win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        tk.Label(frame, text="任务管理 - 所有任务", font=self.title_font).pack(pady=10)

        columns = ("状态", "任务描述", "优先级", "创建日期", "截止日期", "隐藏状态")
        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=20,
            style="Treeview"
        )
        for col in columns:
            tree.heading(col, text=col)
        tree.column("状态", width=60, anchor="center")
        tree.column("任务描述", width=350, anchor="w")  # 加宽任务描述列
        tree.column("优先级", width=70, anchor="center")
        tree.column("创建日期", width=90, anchor="center")
        tree.column("截止日期", width=90, anchor="center")
        tree.column("隐藏状态", width=70, anchor="center")

        # 配置管理窗口的Treeview颜色
        tree.tag_configure("completed", foreground='gray', background='#f0f0f0')
        tree.tag_configure("high", background='#ffebee')
        tree.tag_configure("medium", background='#fff3e0')
        tree.tag_configure("low", background='#e8f5e9')
        tree.tag_configure("overdue", background='#ffcdd2', foreground='#b71c1c')

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_manage_tree(tree, with_overdue_check=True)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="按创建日期排序", command=lambda: self.sort_manage_tasks(tree, 'create_date'),
                  font=self.normal_font, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="按截止日期排序", command=lambda: self.sort_manage_tasks(tree, 'due_date'),
                  font=self.normal_font, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="切换隐藏状态", command=lambda: self.toggle_hide_manage(tree), font=self.normal_font,
                  width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="显示所有任务", command=lambda: self.show_all_manage_tasks(tree),
                  font=self.normal_font, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="激励设置", command=self.open_reward_settings,
                  font=self.normal_font, width=15).pack(side=tk.LEFT, padx=5)

        if sys.platform.startswith('win32') and HAS_PIL and HAS_WIN32:
            tk.Button(btn_frame, text="查看照片", command=lambda: self.view_selected_photo(tree), font=self.normal_font,
                      width=15).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="关闭", command=manage_win.destroy, font=self.normal_font, width=15).pack(
            side=tk.LEFT, padx=5)

        self.check_overdue_tasks()

    def refresh_manage_tree(self, tree, with_overdue_check=False):
        tree.delete(*tree.get_children())
        today = datetime.date.today()
        for i, task in enumerate(self.tasks):
            is_overdue = False
            if not task['completed'] and task['due_date'] != "无":
                try:
                    due_date = datetime.datetime.strptime(task['due_date'], "%Y-%m-%d").date()
                    if due_date < today:
                        is_overdue = True
                except:
                    pass
            wrapped_desc = self.wrap_text(task['description'])  # 完整显示描述
            if task['completed']:
                tag = 'completed'
            else:
                tag = 'high' if task['priority'] == 3 else 'medium' if task['priority'] == 2 else 'low'
            if is_overdue and with_overdue_check:
                tag = ('overdue', tag) if isinstance(tag, str) else ('overdue',) + tag

            tree.insert("", "end", iid=str(i), values=(
                "已完成" if task['completed'] else "待完成",
                wrapped_desc,
                {1: "低", 2: "中", 3: "高"}[task['priority']],
                task['create_date'],
                task['due_date'],
                "已隐藏" if task['manually_hidden'] else "显示中"
            ), tags=tag)

    def manage_search_tasks(self, tree):
        keyword = self.manage_search_entry.get().strip().lower()
        tree.delete(*tree.get_children())
        count = 0
        today = datetime.date.today()
        for i, task in enumerate(self.tasks):
            if keyword in task['description'].lower():
                is_overdue = not task['completed'] and task['due_date'] != "无"
                if is_overdue:
                    try:
                        due_date = datetime.datetime.strptime(task['due_date'], "%Y-%m-%d").date()
                        is_overdue = due_date < today
                    except:
                        is_overdue = False
                wrapped_desc = self.wrap_text(task['description'])
                if task['completed']:
                    tag = 'completed'
                else:
                    tag = 'high' if task['priority'] == 3 else 'medium' if task['priority'] == 2 else 'low'
                if is_overdue:
                    tag = ('overdue', tag) if isinstance(tag, str) else ('overdue',) + tag

                tree.insert("", "end", iid=str(i), values=(
                    "已完成" if task['completed'] else "待完成",
                    wrapped_desc,
                    {1: "低", 2: "中", 3: "高"}[task['priority']],
                    task['create_date'],
                    task['due_date'],
                    "已隐藏" if task['manually_hidden'] else "显示中"
                ), tags=tag)
                count += 1
        messagebox.showinfo("搜索结果", f"找到 {count} 个匹配任务")

    def sort_manage_tasks(self, tree, sort_key):
        if sort_key == 'due_date':
            self.tasks.sort(key=lambda x: (x['due_date'] == "无", x[sort_key]))
        else:
            self.tasks.sort(key=lambda x: x[sort_key])
        self.refresh_manage_tree(tree, with_overdue_check=True)
        self.save_tasks()

    def toggle_hide_manage(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请选择任务!")
            return
        for item in selected:
            try:
                idx = int(item)
                self.tasks[idx]['manually_hidden'] = not self.tasks[idx]['manually_hidden']
            except:
                messagebox.showerror("错误", "操作失败!")
                return
        self.refresh_manage_tree(tree, with_overdue_check=True)
        self.show_all_tasks()
        if self.simple_mode:
            self.update_simple_mode_display()
        self.save_tasks()

    def show_all_manage_tasks(self, tree):
        for task in self.tasks:
            task['manually_hidden'] = False
        self.refresh_manage_tree(tree, with_overdue_check=True)
        self.show_all_tasks()
        if self.simple_mode:
            self.update_simple_mode_display()
        self.save_tasks()

    def check_overdue_tasks(self):
        today = datetime.date.today()
        overdue_tasks = []
        for task in self.tasks:
            if not task['completed'] and task['due_date'] != "无":
                try:
                    due_date = datetime.datetime.strptime(task['due_date'], "%Y-%m-%d").date()
                    if due_date < today:
                        overdue_tasks.append(task['description'])
                except:
                    pass
        if overdue_tasks:
            msg = f"⚠️  以下任务已超期未完成：\n\n" + "\n".join([f"• {t}" for t in overdue_tasks[:5]])
            if len(overdue_tasks) > 5:
                msg += f"\n• 还有 {len(overdue_tasks) - 5} 个任务未显示..."
            messagebox.showwarning("超期提醒", msg)

    def add_photo_to_task(self):
        if not HAS_PIL or not HAS_WIN32:
            messagebox.showerror("错误", "请先安装必要组件：\npip install pillow pywin32")
            return

        try:
            import io
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                img = Image.open(io.BytesIO(data))
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                photo_name = f"task_photo_{timestamp}.png"
                photo_path = os.path.join(self.photo_dir, photo_name)
                img.save(photo_path)
                if self.editing_index >= 0:
                    self.tasks[self.editing_index]['photo_path'] = photo_path
                    messagebox.showinfo("成功", "照片已添加到任务")
                else:
                    messagebox.showinfo("提示", "请先选择要编辑的任务")
            else:
                messagebox.showinfo("提示", "剪贴板中无图片")
            win32clipboard.CloseClipboard()
        except Exception as e:
            messagebox.showerror("错误", f"添加照片失败：{str(e)}")

    def view_selected_photo(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请选择任务")
            return
        try:
            task_index = int(selected[0])
            self.show_task_photo(task_index)
        except:
            messagebox.showerror("错误", "获取任务信息失败")

    def show_task_photo(self, task_index):
        if not HAS_PIL:
            messagebox.showerror("错误", "请先安装pillow：\npip install pillow")
            return

        task = self.tasks[task_index]
        if 'photo_path' not in task or not task['photo_path'] or not os.path.exists(task['photo_path']):
            messagebox.showinfo("提示", "该任务无关联照片")
            return
        try:
            img = Image.open(task['photo_path'])
            img.thumbnail((600, 400))
            photo_win = tk.Toplevel(self.root)
            photo_win.title("任务照片")
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(photo_win, image=photo)
            label.photo = photo
            label.pack()
        except Exception as e:
            messagebox.showerror("错误", f"打开照片失败：{str(e)}")

    def search_tasks(self):
        """搜索任务（使用should_show_task过滤）"""
        keyword = self.search_entry.get().strip().lower()
        self.task_tree.delete(*self.task_tree.get_children())

        if not keyword:
            self.show_all_tasks()
            messagebox.showinfo("搜索", "已显示所有任务")
            return

        count = 0
        for i, task in enumerate(self.tasks):
            if keyword in task['description'].lower() and self.should_show_task(task):
                self.add_task_to_gui(i)
                count += 1
        messagebox.showinfo("搜索结果", f"找到 {count} 个匹配任务")

    def show_statistics(self):
        if not self.task_count:
            messagebox.showinfo("统计", "暂无任务数据!")
            return

        # 统计所有任务
        total_completed = sum(1 for t in self.tasks if t['completed'])
        total_high = sum(1 for t in self.tasks if t['priority'] == 3)
        total_medium = sum(1 for t in self.tasks if t['priority'] == 2)
        total_low = sum(1 for t in self.tasks if t['priority'] == 1)
        hidden_count = sum(1 for t in self.tasks if t['manually_hidden'])

        # 统计显示中的任务
        visible_tasks = [t for t in self.tasks if self.should_show_task(t)]
        visible_count = len(visible_tasks)
        visible_completed = sum(1 for t in visible_tasks if t['completed'])

        msg = (
            f"任务统计（总计 {self.task_count} 个）\n\n"
            f"显示中任务: {visible_count} 个\n"
            f"隐藏任务: {hidden_count} 个\n"
            f"自动隐藏（完成>2天）: {self.task_count - visible_count - hidden_count} 个\n\n"
            f"已完成: {total_completed} ({(total_completed / self.task_count * 100):.1f}%)\n"
            f"待完成: {self.task_count - total_completed} ({((self.task_count - total_completed) / self.task_count * 100):.1f}%)\n\n"
            f"高优先级: {total_high}\n中优先级: {total_medium}\n低优先级: {total_low}"
        )
        messagebox.showinfo("任务统计", msg)

    def show_about(self):
        messagebox.showinfo(
            "关于",
            "任务清单管理系统 v3.4\n\n"
            "基于 Python Tkinter 开发\n\n"
            "核心功能：\n"
            "• 统一列表：所有任务合并显示，优先级用颜色区分（高：浅红/中：浅橙/低：浅绿）\n"
            "• 自动换行：长任务描述自适应分行（完整显示所有文字）\n"
            "• 简洁模式：显示完整任务描述，优化布局和间距\n"
            "• 任务管理：增删改查、隐藏/取消隐藏、标记完成\n"
            "• 超期提醒：未完成任务到期自动报警\n"
            "• 自动隐藏：已完成任务超过两天自动隐藏\n"
            "• 统计功能：包含隐藏任务的完整数据统计\n"
            "• 任务激励：完成任务显示随机激励文案\n"
            "• 照片关联：Windows系统支持粘贴照片到任务\n"
            "• 窗口置顶+开机自启（Windows）\n\n"
            "© Koskin1222"
        )

    def setup_autostart(self):
        try:
            import winreg
            # 使用绝对路径确保开机自启能找到文件
            exe_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])
            if exe_path.endswith('.py'):
                python_path = os.path.join(sys.exec_prefix, 'pythonw.exe')
                exe_path = f'"{python_path}" "{exe_path}"'

            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0,
                                 winreg.KEY_WRITE)
            winreg.SetValueEx(key, "TodoList", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            messagebox.showinfo("成功", "开机自启设置完成!")
        except Exception as e:
            messagebox.showerror("错误", f"设置失败: {str(e)}")

    def update_task_count(self):
        visible = sum(1 for t in self.tasks if self.should_show_task(t))
        self.root.title(f"任务清单 - 共 {visible} 个可见任务 (总计 {self.task_count})")

    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.root.attributes('-topmost', self.is_topmost)
        self.topmost_button.config(text="取消置顶" if self.is_topmost else "窗口置顶",
                                   bg="#FF5722" if self.is_topmost else "#607D8B", fg="white")
        if self.simple_mode:
            self.update_simple_topmost_button()
        self.save_config()

    def update_topmost_button(self):
        self.topmost_button.config(text="取消置顶" if self.is_topmost else "窗口置顶",
                                   bg="#FF5722" if self.is_topmost else "#607D8B", fg="white")

    def on_closing(self):
        self.save_tasks()
        self.save_config()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        root.iconbitmap("todo_icon.ico")
    except:
        pass
    app = TodoListApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
