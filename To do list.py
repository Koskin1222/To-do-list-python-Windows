import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import datetime
import winreg
import sys
from tkcalendar import Calendar  # 需要安装：pip install tkcalendar


# ------------------------------ 修复tkcalendar语法警告（需手动修改第三方库文件）------------------------------
# 找到tkcalendar的calendar_.py文件（路径参考编译日志：D:\xxx\.venv\Lib\site-packages\tkcalendar\calendar_.py）
# 将第221行的：font = kw.pop("font", "Liberation\ Sans 9")
# 改为：font = kw.pop("font", r"Liberation Sans 9") 或 "Liberation Sans 9"（去掉转义符）

class TodoListApp:
    def __init__(self, root):
        self.root = root
        self.root.title("任务清单 - 共 0 个任务")
        self.root.geometry("900x700")
        self.root.minsize(400, 300)

        # 任务数据
        self.tasks = []
        self.task_count = 0
        self.max_tasks = 100
        self.is_topmost = False
        self.editing_index = -1
        self.simple_mode = False

        # 配置文件
        self.data_file = "todo_data.json"
        self.config_file = "todo_config.json"

        # 创建界面（先初始化Treeview，再绑定事件）
        self.create_widgets()

        # 加载配置和任务
        self.load_config()
        self.load_tasks()

        # 设置窗口置顶
        if self.is_topmost:
            self.root.attributes('-topmost', True)

        # 关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
        title_label = tk.Label(self.main_frame, text="任务清单管理系统",
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

        # 按钮区域
        button_frame = tk.Frame(self.main_frame)
        button_frame.grid(row=2, column=0, columnspan=8, pady=10, sticky="ew")
        for i in range(10):
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

        # 搜索区域
        tk.Label(button_frame, text="搜索:", font=self.normal_font).grid(row=0, column=5, padx=(10, 5))
        self.search_entry = tk.Entry(button_frame, font=self.normal_font)
        self.search_entry.grid(row=0, column=6, padx=5, sticky="ew")
        tk.Button(button_frame, text="搜索", command=self.search_tasks,
                  font=self.normal_font).grid(row=0, column=7, padx=2, sticky="ew")
        tk.Button(button_frame, text="统计", command=self.show_statistics,
                  font=self.normal_font).grid(row=0, column=8, padx=2, sticky="ew")
        tk.Button(button_frame, text="管理任务", command=self.manage_tasks,
                  font=self.normal_font).grid(row=0, column=9, padx=2, sticky="ew")

        # 任务列表框架（核心：Treeview配置）
        list_frame = tk.Frame(self.main_frame)
        list_frame.grid(row=3, column=0, columnspan=8, pady=10, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 创建Treeview（指定show="headings"，避免默认列干扰）
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

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        self.task_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # ------------------------------ 修复双击事件：简化绑定逻辑 ------------------------------
        # 移除冲突的单击事件绑定，只保留双击事件
        self.task_tree.bind("<Double-1>", self.on_double_click)

        # 底部按钮框架
        bottom_frame = tk.Frame(self.main_frame)
        bottom_frame.grid(row=4, column=0, columnspan=8, pady=10, sticky="ew")
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)
        bottom_frame.columnconfigure(2, weight=1)
        bottom_frame.columnconfigure(3, weight=1)

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

    # ------------------------------ 核心修复：简化双击事件处理 ------------------------------
    def on_double_click(self, event):
        """双击事件：简化处理逻辑，直接获取选中项"""
        # 获取当前选中的项目
        selected_items = self.task_tree.selection()
        if not selected_items:
            return

        # 只处理第一个选中的项目
        item = selected_items[0]

        try:
            # 直接获取选中项的IID
            original_index = int(item)

            # 切换任务状态
            if 0 <= original_index < len(self.tasks):
                self.tasks[original_index]['completed'] = not self.tasks[original_index]['completed']
                if self.tasks[original_index]['completed']:
                    self.tasks[original_index]['completed_date'] = datetime.datetime.now().strftime("%Y-%m-%d")
                else:
                    self.tasks[original_index]['completed_date'] = ""

                # 刷新显示+保存
                self.sort_tasks()
                self.show_all_tasks()
                if self.simple_mode:
                    self.update_simple_mode_display()
                self.save_tasks()

        except (ValueError, IndexError) as e:
            messagebox.showerror("错误", f"双击处理失败：{str(e)}")

    def add_task_to_gui(self, index):
        """添加任务到Treeview：确保IID唯一且正确绑定原始索引"""
        task = self.tasks[index]
        status = "已完成" if task['completed'] else "待完成"
        priority_text = {1: "低", 2: "中", 3: "高"}.get(task['priority'], "中")
        hidden_status = "已隐藏" if task['manually_hidden'] else "显示中"

        # 优先级颜色标签
        if task['completed']:
            tag = 'completed'
        else:
            tag = 'high' if task['priority'] == 3 else 'medium' if task['priority'] == 2 else 'low'

        # 关键：用原始索引作为IID（字符串类型，避免Tkinter类型错误）
        self.task_tree.insert(
            "", "end",
            iid=str(index),  # IID必须是字符串，与双击事件中的int转换对应
            values=(status, task['description'], priority_text,
                    task['create_date'], task['due_date'], hidden_status),
            tags=(tag,)
        )

        # 配置标签样式
        self.task_tree.tag_configure('completed', foreground='gray', background='#f0f0f0')
        self.task_tree.tag_configure('high', background='#ffebee')
        self.task_tree.tag_configure('medium', background='#fff3e0')
        self.task_tree.tag_configure('low', background='#e8f5e9')

    # ------------------------------ 其他方法保持不变 ------------------------------
    def create_simple_mode_frame(self):
        """简洁模式框架（支持滚轮）"""
        self.simple_frame = tk.Frame(self.root)
        self.simple_frame.columnconfigure(0, weight=1)
        self.simple_frame.rowconfigure(1, weight=1)

        # 标题
        tk.Label(self.simple_frame, text="简洁模式 - 待办任务",
                 font=("Microsoft YaHei", 12, "bold"), bg="white").grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        # 任务列表容器
        list_container = tk.Frame(self.simple_frame)
        list_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        # 滚动条+画布
        self.simple_scrollbar = tk.Scrollbar(list_container)
        self.simple_scrollbar.grid(row=0, column=1, sticky="ns")
        self.simple_canvas = tk.Canvas(list_container, yscrollcommand=self.simple_scrollbar.set,
                                       bg="white", highlightthickness=0)
        self.simple_canvas.grid(row=0, column=0, sticky="nsew")
        self.simple_scrollbar.config(command=self.simple_canvas.yview)

        # 内部框架
        self.simple_inner_frame = tk.Frame(self.simple_canvas, bg="white")
        self.simple_canvas_window = self.simple_canvas.create_window((0, 0), window=self.simple_inner_frame,
                                                                     anchor="nw")

        # 绑定事件
        self.simple_inner_frame.bind("<Configure>", lambda e: self.simple_canvas.configure(
            scrollregion=self.simple_canvas.bbox("all")))
        self.simple_canvas.bind("<Configure>",
                                lambda e: self.simple_canvas.itemconfig(self.simple_canvas_window, width=e.width))
        self.simple_canvas.bind("<MouseWheel>",
                                lambda e: self.simple_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        self.simple_inner_frame.bind("<MouseWheel>",
                                     lambda e: self.simple_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # 底部按钮
        simple_bottom_frame = tk.Frame(self.simple_frame)
        simple_bottom_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        tk.Button(simple_bottom_frame, text="返回完整模式", command=self.toggle_simple_mode,
                  font=self.small_font, bg="#FF5722", fg="white").pack(side=tk.LEFT, padx=5)
        self.simple_topmost_button = tk.Button(simple_bottom_frame, text="窗口置顶", command=self.toggle_topmost,
                                               font=self.small_font)
        self.simple_topmost_button.pack(side=tk.RIGHT, padx=5)

        self.simple_frame.pack_forget()

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

    def update_simple_mode_display(self):
        """更新简洁模式任务列表"""
        for widget in self.simple_inner_frame.winfo_children():
            widget.destroy()

        # 筛选未完成+未隐藏任务
        pending_tasks = [(i, t) for i, t in enumerate(self.tasks) if not t['completed'] and not t['manually_hidden']]
        pending_tasks.sort(key=lambda x: x[1]['priority'], reverse=True)
        canvas_width = self.simple_canvas.winfo_width() or 400

        # 添加任务项
        for i, (idx, task) in enumerate(pending_tasks):
            var = tk.BooleanVar()
            task_frame = tk.Frame(self.simple_inner_frame, bg="white", relief="solid", bd=1)
            task_frame.pack(fill=tk.X, padx=5, pady=2)

            # 内容框架
            content_frame = tk.Frame(task_frame, bg="white")
            content_frame.pack(fill=tk.X, padx=5, pady=5)
            content_frame.task_content_frame = content_frame

            # 优先级指示器
            top_frame = tk.Frame(content_frame, bg="white")
            top_frame.pack(fill=tk.X)
            priority_color = "#F44336" if task['priority'] == 3 else "#FF9800" if task['priority'] == 2 else "#4CAF50"
            tk.Frame(top_frame, width=4, height=18, bg=priority_color).pack(side=tk.LEFT, padx=(0, 8))

            # 复选框+描述
            tk.Checkbutton(top_frame, variable=var, command=lambda x=idx: self.complete_task_simple(x),
                           font=self.small_font, bg="white").pack(side=tk.LEFT, padx=(0, 8))
            tk.Label(top_frame, text=task['description'], font=self.small_font, anchor="w", justify=tk.LEFT,
                     bg="white", wraplength=canvas_width - 100).pack(side=tk.LEFT, fill=tk.X, expand=True)

            # 截止日期
            if task['due_date'] and task['due_date'] != "无":
                bottom_frame = tk.Frame(content_frame, bg="white")
                bottom_frame.pack(fill=tk.X, pady=(2, 0))
                tk.Label(bottom_frame, text=f"截止: {task['due_date']}", font=("Microsoft YaHei", 8), fg="gray",
                         bg="white").pack(side=tk.LEFT)

        # 无任务提示
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
        if not self.simple_mode:
            self.sort_tasks()
            self.show_all_tasks()

    def choose_date(self):
        """选择日期"""
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

    # 移除冲突的on_tree_click方法

    def load_tasks(self):
        """加载任务"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = data.get('tasks', [])
                    self.task_count = len(self.tasks)
                    # 补全旧数据字段
                    for task in self.tasks:
                        if 'completed_date' not in task:
                            task['completed_date'] = ""
                        if 'manually_hidden' not in task:
                            task['manually_hidden'] = False
                    self.sort_tasks()
                    self.show_all_tasks()
        except Exception as e:
            messagebox.showerror("错误", f"加载任务失败: {str(e)}")

    def save_tasks(self):
        """保存任务"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump({'tasks': self.tasks}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存任务失败: {str(e)}")

    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.root.geometry(config.get('geometry', '900x700+100+100'))
                    self.is_topmost = config.get('topmost', False)
                    self.simple_mode = config.get('simple_mode', False)
                    if self.simple_mode:
                        self.root.after(100, self.toggle_simple_mode)
        except Exception:
            pass

    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({
                    'geometry': self.root.geometry(),
                    'topmost': self.is_topmost,
                    'simple_mode': self.simple_mode
                }, f, indent=2)
        except Exception:
            pass

    def sort_tasks(self):
        """排序任务（未完成优先，高优先级在前）"""
        self.tasks.sort(key=lambda x: (-x['priority'] if not x['completed'] else 0 - x['priority']))

    def should_show_task(self, task):
        """判断任务是否显示"""
        if task['manually_hidden']:
            return False
        if not task['completed']:
            return True
        if not task['completed_date']:
            return True
        try:
            return (datetime.datetime.now() - datetime.datetime.strptime(task['completed_date'], "%Y-%m-%d")).days < 2
        except:
            return True

    def add_task(self):
        """添加/编辑任务"""
        desc = self.task_entry.get().strip()
        if not desc:
            messagebox.showinfo("提示", "请输入任务描述!")
            return

        # 优先级+日期处理
        priority = {"低": 1, "中": 2, "高": 3}[self.priority_var.get()]
        due_date = self.date_entry.get().strip() or "无"
        if due_date != "无":
            try:
                datetime.datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("错误", "日期格式应为 YYYY-MM-DD!")
                return

        # 编辑/新增逻辑
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
                'due_date': due_date, 'create_date': datetime.datetime.now().strftime("%Y-%m-%d")
            })
            self.task_count += 1

        # 重置+刷新
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

        # 安全删除（按原始索引从大到小）
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

        # 获取原始索引
        try:
            original_index = int(selected[0])
            task = self.tasks[original_index]
        except:
            messagebox.showerror("错误", "无法获取任务信息!")
            return

        # 填充表单
        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, task['description'])
        self.date_entry.delete(0, tk.END)
        if task['due_date'] != "无":
            self.date_entry.insert(0, task['due_date'])
        self.priority_var.set({1: "低", 2: "中", 3: "高"}[task['priority']])
        self.editing_index = original_index
        self.task_entry.focus()

    def toggle_complete(self):
        """标记完成（按钮）"""
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

    def manage_tasks(self):
        """任务管理窗口"""
        manage_win = tk.Toplevel(self.root)
        manage_win.title("任务管理")
        manage_win.geometry("800x600")
        manage_win.transient(self.root)
        manage_win.grab_set()

        # 布局
        frame = tk.Frame(manage_win)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(frame, text="任务管理 - 所有任务", font=self.title_font).pack(pady=10)

        # Treeview
        columns = ("状态", "任务描述", "优先级", "创建日期", "截止日期", "隐藏状态")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        for col in columns:
            tree.heading(col, text=col)
        tree.column("状态", width=60, anchor="center")
        tree.column("任务描述", width=300)
        tree.column("优先级", width=70, anchor="center")
        tree.column("创建日期", width=90, anchor="center")
        tree.column("截止日期", width=90, anchor="center")
        tree.column("隐藏状态", width=70, anchor="center")

        # 滚动条
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 填充数据
        for i, task in enumerate(self.tasks):
            tree.insert("", "end", iid=str(i), values=(
                "已完成" if task['completed'] else "待完成",
                task['description'],
                {1: "低", 2: "中", 3: "高"}[task['priority']],
                task['create_date'],
                task['due_date'],
                "已隐藏" if task['manually_hidden'] else "显示中"
            ))

        # 按钮
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)

        def toggle_hide():
            """切换隐藏状态"""
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
            # 刷新
            tree.delete(*tree.get_children())
            for i, task in enumerate(self.tasks):
                tree.insert("", "end", iid=str(i), values=(
                    "已完成" if task['completed'] else "待完成",
                    task['description'],
                    {1: "低", 2: "中", 3: "高"}[task['priority']],
                    task['create_date'],
                    task['due_date'],
                    "已隐藏" if task['manually_hidden'] else "显示中"
                ))
            self.show_all_tasks()
            if self.simple_mode:
                self.update_simple_mode_display()
            self.save_tasks()

        def show_all_tasks():
            """显示所有任务"""
            for task in self.tasks:
                task['manually_hidden'] = False
            # 刷新
            tree.delete(*tree.get_children())
            for i, task in enumerate(self.tasks):
                tree.insert("", "end", iid=str(i), values=(
                    "已完成" if task['completed'] else "待完成",
                    task['description'],
                    {1: "低", 2: "中", 3: "高"}[task['priority']],
                    task['create_date'],
                    task['due_date'],
                    "已隐藏" if task['manually_hidden'] else "显示中"
                ))
            self.show_all_tasks()
            if self.simple_mode:
                self.update_simple_mode_display()
            self.save_tasks()

        # 按钮布局
        tk.Button(btn_frame, text="切换隐藏状态", command=toggle_hide, font=self.normal_font, width=15).pack(
            side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="显示所有任务", command=show_all_tasks, font=self.normal_font, width=15).pack(
            side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=manage_win.destroy, font=self.normal_font, width=15).pack(
            side=tk.LEFT, padx=5)

    def search_tasks(self):
        """搜索任务"""
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

    def show_all_tasks(self):
        """显示所有任务"""
        self.task_tree.delete(*self.task_tree.get_children())
        for i in range(len(self.tasks)):
            if self.should_show_task(self.tasks[i]):
                self.add_task_to_gui(i)

    def show_statistics(self):
        """显示统计"""
        if not self.task_count:
            messagebox.showinfo("统计", "暂无任务数据!")
            return

        visible = [t for t in self.tasks if self.should_show_task(t)]
        completed = sum(1 for t in visible if t['completed'])
        high = sum(1 for t in visible if t['priority'] == 3)
        medium = sum(1 for t in visible if t['priority'] == 2)
        low = sum(1 for t in visible if t['priority'] == 1)

        msg = (
            f"任务统计 (显示 {len(visible)} 个)\n\n"
            f"总任务数: {self.task_count}\n"
            f"已完成: {completed} ({(completed / len(visible) * 100):.1f}%)\n"
            f"待完成: {len(visible) - completed} ({((len(visible) - completed) / len(visible) * 100):.1f}%)\n\n"
            f"高优先级: {high}\n中优先级: {medium}\n低优先级: {low}"
        )
        messagebox.showinfo("任务统计", msg)

    def show_about(self):
        """关于"""
        messagebox.showinfo(
            "关于",
            "任务清单管理系统 v2.7\n\n"
            "基于 Python Tkinter 开发\n\n"
            "功能: 任务增删改查、优先级管理、\n"
            "双击标记完成、简洁模式、开机自启\n\n"
            "© 2024 任务清单团队"
        )

    def setup_autostart(self):
        """开机自启（Windows）"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0,
                                 winreg.KEY_WRITE)
            winreg.SetValueEx(key, "TodoList", 0, winreg.REG_SZ, os.path.abspath(sys.argv[0]))
            winreg.CloseKey(key)
            messagebox.showinfo("成功", "开机自启设置完成!")
        except Exception as e:
            messagebox.showerror("错误", f"设置失败: {str(e)}")

    def update_task_count(self):
        """更新任务计数"""
        visible = sum(1 for t in self.tasks if self.should_show_task(t))
        self.root.title(f"任务清单 - 共 {visible} 个任务 (总计 {self.task_count})")

    def toggle_topmost(self):
        """切换置顶"""
        self.is_topmost = not self.is_topmost
        self.root.attributes('-topmost', self.is_topmost)
        self.topmost_button.config(text="取消置顶" if self.is_topmost else "窗口置顶",
                                   bg="#FF5722" if self.is_topmost else "#607D8B", fg="white")
        if self.simple_mode:
            self.update_simple_topmost_button()
        self.save_config()

    def update_topmost_button(self):
        """更新置顶按钮"""
        self.topmost_button.config(text="取消置顶" if self.is_topmost else "窗口置顶",
                                   bg="#FF5722" if self.is_topmost else "#607D8B", fg="white")

    def on_closing(self):
        """关闭窗口"""
        self.save_tasks()
        self.save_config()
        self.root.destroy()


def main():
    root = tk.Tk()
    # 图标（可选）
    try:
        root.iconbitmap("todo_icon.ico")
    except:
        pass
    app = TodoListApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()