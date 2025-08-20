"""
输入管理页面 - 提供任务列表的查看、编辑和删除功能
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from .base_page import BasePage
from models import Task


class InputManagementPage(BasePage):
    """输入管理页面 - 任务管理界面"""
    
    def setup_ui(self):
        """设置输入管理页面的用户界面"""
        # 页面标题
        title_label = ttk.Label(
            self.frame, 
            text="任务管理", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # 工具栏
        toolbar_frame = ttk.Frame(self.frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 刷新按钮
        refresh_btn = ttk.Button(
            toolbar_frame,
            text="刷新列表",
            command=self.refresh_data,
            width=12
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 删除按钮
        delete_btn = ttk.Button(
            toolbar_frame,
            text="删除选中",
            command=self.delete_selected,
            width=12
        )
        delete_btn.pack(side=tk.LEFT, padx=10)
        
        # 搜索框
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)
        
        # 任务列表
        self.create_task_list()
        
        # 详情区域
        self.create_detail_panel()
        
        # 加载数据
        self.refresh_data()
        
    def create_task_list(self):
        """创建任务列表"""
        list_frame = ttk.LabelFrame(self.frame, text="任务列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 创建 Treeview
        columns = ('ID', '联赛名称', '国家', '年份', '类型', '创建时间')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # 设置列标题和宽度
        self.task_tree.heading('ID', text='ID')
        self.task_tree.heading('联赛名称', text='联赛名称')
        self.task_tree.heading('国家', text='国家')
        self.task_tree.heading('年份', text='年份')
        self.task_tree.heading('类型', text='类型')
        self.task_tree.heading('创建时间', text='创建时间')
        
        self.task_tree.column('ID', width=50, anchor='center')
        self.task_tree.column('联赛名称', width=200)
        self.task_tree.column('国家', width=100)
        self.task_tree.column('年份', width=80, anchor='center')
        self.task_tree.column('类型', width=100, anchor='center')
        self.task_tree.column('创建时间', width=150, anchor='center')
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.task_tree.xview)
        self.task_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.task_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定选择事件
        self.task_tree.bind('<<TreeviewSelect>>', self.on_task_select)
        
    def create_detail_panel(self):
        """创建详情面板"""
        detail_frame = ttk.LabelFrame(self.frame, text="任务详情", padding=15)
        detail_frame.pack(fill=tk.X)
        
        # 创建详情显示区域
        self.detail_text = tk.Text(
            detail_frame, 
            height=8, 
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Consolas', 10)
        )
        
        detail_scrollbar = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)
        
        self.detail_text.grid(row=0, column=0, sticky='nsew')
        detail_scrollbar.grid(row=0, column=1, sticky='ns')
        
        detail_frame.grid_rowconfigure(0, weight=1)
        detail_frame.grid_columnconfigure(0, weight=1)
        
    def refresh_data(self):
        """刷新任务数据"""
        try:
            # 清空现有数据
            for item in self.task_tree.get_children():
                self.task_tree.delete(item)
            
            # 从数据库加载数据
            with self.get_db_session() as session:
                tasks = session.query(Task).order_by(Task.created_at.desc()).all()
                
                for task in tasks:
                    created_time = task.created_at.strftime('%Y-%m-%d %H:%M') if task.created_at else ''
                    self.task_tree.insert('', 'end', values=(
                        task.id,
                        task.league,
                        task.country,
                        task.year,
                        task.type,
                        created_time
                    ))
            
            self.log_action("刷新任务列表", f"加载了 {len(tasks)} 条记录")
            
        except Exception as e:
            self.logger.error(f"刷新数据失败: {e}")
            self.show_message("错误", f"刷新数据失败: {str(e)}", "error")
    
    def on_task_select(self, event):
        """任务选择事件处理"""
        selection = self.task_tree.selection()
        if not selection:
            self.clear_detail()
            return
            
        # 获取选中的任务ID
        item = self.task_tree.item(selection[0])
        task_id = item['values'][0]
        
        # 加载任务详情
        self.load_task_detail(task_id)
    
    def load_task_detail(self, task_id):
        """加载任务详情"""
        try:
            with self.get_db_session() as session:
                task = session.query(Task).filter(Task.id == task_id).first()
                
                if task:
                    detail_text = f"""任务ID: {task.id}
赛事级别: {task.level}
赛事名称: {task.event}
国家/地区: {task.country}
联赛名称: {task.league}
赛事类型: {task.type}
赛事年份: {task.year}
分组信息: {task.group}
主要链接: {task.link or '未设置'}
备用链接: {task.link_second or '未设置'}
最后爬取: {task.last_crawl_time.strftime('%Y-%m-%d %H:%M:%S') if task.last_crawl_time else '从未爬取'}
创建时间: {task.created_at.strftime('%Y-%m-%d %H:%M:%S') if task.created_at else ''}
更新时间: {task.updated_at.strftime('%Y-%m-%d %H:%M:%S') if task.updated_at else ''}"""
                    
                    self.detail_text.config(state=tk.NORMAL)
                    self.detail_text.delete(1.0, tk.END)
                    self.detail_text.insert(1.0, detail_text)
                    self.detail_text.config(state=tk.DISABLED)
                    
        except Exception as e:
            self.logger.error(f"加载任务详情失败: {e}")
            self.show_message("错误", f"加载详情失败: {str(e)}", "error")
    
    def clear_detail(self):
        """清空详情显示"""
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.config(state=tk.DISABLED)
    
    def delete_selected(self):
        """删除选中的任务"""
        selection = self.task_tree.selection()
        if not selection:
            self.show_message("提示", "请先选择要删除的任务", "warning")
            return
        
        # 确认删除
        item = self.task_tree.item(selection[0])
        task_id = item['values'][0]
        league_name = item['values'][1]
        
        if not tk.messagebox.askyesno(
            "确认删除", 
            f"确定要删除任务 '{league_name}' (ID: {task_id}) 吗？\n\n此操作将同时删除相关的队伍数据，且无法恢复！"
        ):
            return
        
        try:
            with self.get_db_session() as session:
                task = session.query(Task).filter(Task.id == task_id).first()
                if task:
                    session.delete(task)
                    session.commit()
                    
                    self.show_message("成功", "任务删除成功", "info")
                    self.log_action("删除任务", f"ID: {task_id}, 联赛: {league_name}")
                    self.refresh_data()
                    self.clear_detail()
                    
        except Exception as e:
            self.logger.error(f"删除任务失败: {e}")
            self.show_message("错误", f"删除失败: {str(e)}", "error")
    
    def on_search_change(self, *args):
        """搜索框内容变化事件"""
        search_text = self.search_var.get().lower()
        
        # 如果搜索框为空，显示所有项目
        if not search_text:
            for item in self.task_tree.get_children():
                self.task_tree.reattach(item, '', 'end')
            return
        
        # 过滤显示匹配的项目
        all_items = self.task_tree.get_children()
        for item in all_items:
            values = self.task_tree.item(item)['values']
            # 在联赛名称、国家、年份中搜索
            if (search_text in str(values[1]).lower() or 
                search_text in str(values[2]).lower() or 
                search_text in str(values[3]).lower()):
                self.task_tree.reattach(item, '', 'end')
            else:
                self.task_tree.detach(item)