"""
输入页面 - 提供 Task 模型的数据录入界面
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from .base_page import BasePage
from models import Task


class InputPage(BasePage):
    """输入页面 - 任务录入表单"""
    
    def setup_ui(self):
        """设置输入页面的用户界面"""
        # 页面标题
        title_label = ttk.Label(
            self.frame, 
            text="任务录入", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # 创建表单框架
        form_frame = ttk.LabelFrame(self.frame, text="赛事任务信息", padding=20)
        form_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 表单字段
        self.level_var = tk.StringVar()
        self.event_var = tk.StringVar()
        self.country_var = tk.StringVar()
        self.league_var = tk.StringVar()
        self.type_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.group_var = tk.StringVar(value="默认组")
        self.link_var = tk.StringVar()
        self.link_second_var = tk.StringVar()
        
        # 第一行
        self.level_entry = self.create_labeled_entry(
            form_frame, "赛事级别*:", 0, width=15
        )
        self.level_entry.config(textvariable=self.level_var)
        
        self.event_entry = self.create_labeled_entry(
            form_frame, "赛事名称*:", 0, column=2, width=25
        )
        self.event_entry.config(textvariable=self.event_var)
        
        # 第二行
        self.country_entry = self.create_labeled_entry(
            form_frame, "国家/地区*:", 1, width=15
        )
        self.country_entry.config(textvariable=self.country_var)
        
        self.league_entry = self.create_labeled_entry(
            form_frame, "联赛名称*:", 1, column=2, width=25
        )
        self.league_entry.config(textvariable=self.league_var)
        
        # 第三行
        type_values = ["常规", "联二合并", "春秋合并", "东西拆分"]
        self.type_combo = self.create_labeled_combobox(
            form_frame, "赛事类型*:", type_values, 2, width=15
        )
        self.type_combo.config(textvariable=self.type_var)
        self.type_combo.set("常规")
        
        self.year_entry = self.create_labeled_entry(
            form_frame, "赛事年份*:", 2, column=2, width=15
        )
        self.year_entry.config(textvariable=self.year_var)
        
        # 第四行
        self.group_entry = self.create_labeled_entry(
            form_frame, "分组信息:", 3, width=15
        )
        self.group_entry.config(textvariable=self.group_var)
        
        # 第五行 - 链接信息
        link_frame = ttk.LabelFrame(form_frame, text="数据源链接", padding=10)
        link_frame.grid(row=4, column=0, columnspan=4, sticky='ew', pady=(20, 0))
        
        ttk.Label(link_frame, text="主要链接:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.link_entry = ttk.Entry(link_frame, textvariable=self.link_var, width=60)
        self.link_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        
        ttk.Label(link_frame, text="备用链接:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.link_second_entry = ttk.Entry(link_frame, textvariable=self.link_second_var, width=60)
        self.link_second_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)
        
        link_frame.columnconfigure(1, weight=1)
        
        # 按钮区域
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        # 保存按钮
        save_btn = ttk.Button(
            button_frame, 
            text="保存任务", 
            command=self.save_task,
            width=15
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空按钮
        clear_btn = ttk.Button(
            button_frame, 
            text="清空表单", 
            command=self.clear_form,
            width=15
        )
        clear_btn.pack(side=tk.LEFT, padx=10)
        
        # 必填字段提示
        tip_label = ttk.Label(
            self.frame,
            text="* 标记为必填字段",
            font=('Arial', 9),
            foreground='red'
        )
        tip_label.pack(anchor='w')
        
    def save_task(self):
        """保存任务到数据库"""
        try:
            # 验证必填字段
            if not all([
                self.level_var.get(),
                self.event_var.get(),
                self.country_var.get(),
                self.league_var.get(),
                self.type_var.get(),
                self.year_var.get()
            ]):
                self.show_message("错误", "请填写所有必填字段", "error")
                return
            
            # 验证级别为数字
            try:
                level = int(self.level_var.get())
            except ValueError:
                self.show_message("错误", "赛事级别必须为数字", "error")
                return
            
            # 创建任务对象
            task = Task(
                level=level,
                event=self.event_var.get(),
                country=self.country_var.get(),
                league=self.league_var.get(),
                type=self.type_var.get(),
                year=self.year_var.get(),
                group=self.group_var.get(),
                link=self.link_var.get() or None,
                link_second=self.link_second_var.get() or None
            )
            
            # 保存到数据库
            with self.get_db_session() as session:
                session.add(task)
                session.commit()
                task_id = task.id
            
            self.show_message("成功", f"任务保存成功！任务ID: {task_id}", "info")
            self.log_action("保存任务", f"ID: {task_id}, 联赛: {task.league}")
            self.clear_form()
            
        except Exception as e:
            self.logger.error(f"保存任务失败: {e}")
            self.show_message("错误", f"保存失败: {str(e)}", "error")
    
    def clear_form(self):
        """清空表单"""
        self.level_var.set("")
        self.event_var.set("")
        self.country_var.set("")
        self.league_var.set("")
        self.type_var.set("常规")
        self.year_var.set("")
        self.group_var.set("默认组")
        self.link_var.set("")
        self.link_second_var.set("")
        
        self.log_action("清空表单")