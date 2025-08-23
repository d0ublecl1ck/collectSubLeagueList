"""
输入管理页面 - 提供任务列表的查看、编辑和删除功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
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
        
        # 全选按钮
        select_all_btn = ttk.Button(
            toolbar_frame,
            text="全选",
            command=self.select_all,
            width=8
        )
        select_all_btn.pack(side=tk.LEFT, padx=(10, 5))
        
        # 反选按钮
        invert_btn = ttk.Button(
            toolbar_frame,
            text="反选",
            command=self.invert_selection,
            width=8
        )
        invert_btn.pack(side=tk.LEFT, padx=5)
        
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
        
        # 初始化完整项目列表（用于搜索状态管理）
        self.all_task_items = []
        
        # 加载数据
        self.refresh_data()
        
    def create_task_list(self):
        """创建任务列表"""
        list_frame = ttk.LabelFrame(self.frame, text="任务列表", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 创建 Treeview
        columns = ('ID', '赛事级别', '赛事名称', '联赛名称', '国家', '年份', '类型', '分组', '最后爬取', '创建时间')
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12, selectmode='extended')
        
        # 设置列标题和宽度
        self.task_tree.heading('ID', text='ID')
        self.task_tree.heading('赛事级别', text='赛事级别')
        self.task_tree.heading('赛事名称', text='赛事名称')
        self.task_tree.heading('联赛名称', text='联赛名称')
        self.task_tree.heading('国家', text='国家')
        self.task_tree.heading('年份', text='年份')
        self.task_tree.heading('类型', text='类型')
        self.task_tree.heading('分组', text='分组')
        self.task_tree.heading('最后爬取', text='最后爬取')
        self.task_tree.heading('创建时间', text='创建时间')
        
        self.task_tree.column('ID', width=50, anchor='center')
        self.task_tree.column('赛事级别', width=80, anchor='center')
        self.task_tree.column('赛事名称', width=120)
        self.task_tree.column('联赛名称', width=150)
        self.task_tree.column('国家', width=80)
        self.task_tree.column('年份', width=60, anchor='center')
        self.task_tree.column('类型', width=80, anchor='center')
        self.task_tree.column('分组', width=80, anchor='center')
        self.task_tree.column('最后爬取', width=120, anchor='center')
        self.task_tree.column('创建时间', width=120, anchor='center')
        
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
            # 清空现有数据和完整项目列表
            for item in self.task_tree.get_children():
                self.task_tree.delete(item)
            self.all_task_items = []
            
            # 从数据库加载数据
            with self.get_db_session() as session:
                tasks = session.query(Task).order_by(Task.created_at.desc()).all()
                
                for task in tasks:
                    created_time = task.created_at.strftime('%Y-%m-%d %H:%M') if task.created_at else ''
                    last_crawl_time = task.last_crawl_time.strftime('%Y-%m-%d %H:%M') if task.last_crawl_time else '从未爬取'
                    item_id = self.task_tree.insert('', 'end', values=(
                        task.id,
                        task.level,
                        task.event,
                        task.league,
                        task.country,
                        task.year,
                        task.type,
                        task.group,
                        last_crawl_time,
                        created_time
                    ))
                    # 保存到完整项目列表
                    self.all_task_items.append(item_id)
            
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
        
        # 构建待删除任务列表
        tasks_to_delete = []
        for item_id in selection:
            item = self.task_tree.item(item_id)
            task_id = item['values'][0]
            league_name = item['values'][3]
            tasks_to_delete.append((task_id, league_name))
        
        # 构建确认删除对话框消息
        if len(tasks_to_delete) == 1:
            task_id, league_name = tasks_to_delete[0]
            confirm_message = f"确定要删除任务 '{league_name}' (ID: {task_id}) 吗？\n\n此操作将同时删除相关的队伍数据，且无法恢复！"
        else:
            task_list = "\n".join([f"• {league} (ID: {tid})" for tid, league in tasks_to_delete])
            confirm_message = f"确定要删除以下 {len(tasks_to_delete)} 个任务吗？\n\n{task_list}\n\n此操作将同时删除相关的队伍数据，且无法恢复！"
        
        if not messagebox.askyesno("确认删除", confirm_message):
            return
        
        # 批量删除任务
        deleted_count = 0
        failed_tasks = []
        
        try:
            with self.get_db_session() as session:
                for task_id, league_name in tasks_to_delete:
                    try:
                        task = session.query(Task).filter(Task.id == task_id).first()
                        if task:
                            session.delete(task)
                            deleted_count += 1
                        else:
                            failed_tasks.append(f"{league_name} (ID: {task_id}) - 任务不存在")
                    except Exception as e:
                        failed_tasks.append(f"{league_name} (ID: {task_id}) - {str(e)}")
                
                session.commit()
                
                # 显示删除结果
                if failed_tasks:
                    result_message = f"删除完成！成功删除 {deleted_count} 个任务"
                    if failed_tasks:
                        result_message += f"\n\n失败的任务：\n" + "\n".join(failed_tasks)
                    self.show_message("删除结果", result_message, "warning")
                else:
                    self.show_message("成功", f"成功删除 {deleted_count} 个任务", "info")
                
                # 记录日志
                task_names = ", ".join([league for _, league in tasks_to_delete[:3]])
                if len(tasks_to_delete) > 3:
                    task_names += f" 等{len(tasks_to_delete)}个任务"
                self.log_action("批量删除任务", f"成功删除 {deleted_count} 个任务: {task_names}")
                
                # 刷新界面
                self.refresh_data()
                self.clear_detail()
                    
        except Exception as e:
            self.logger.error(f"批量删除任务失败: {e}")
            self.show_message("错误", f"删除失败: {str(e)}", "error")
    
    def select_all(self):
        """全选所有可见任务"""
        try:
            # 获取所有可见项目（考虑搜索过滤）
            all_items = self.task_tree.get_children()
            if all_items:
                # 选中所有可见项目
                self.task_tree.selection_set(all_items)
                self.log_action("全选操作", f"已选中 {len(all_items)} 个任务")
            else:
                self.show_message("提示", "暂无任务可选择", "info")
        except Exception as e:
            self.logger.error(f"全选操作失败: {e}")
            self.show_message("错误", f"全选失败: {str(e)}", "error")
    
    def invert_selection(self):
        """反选任务"""
        try:
            # 获取当前选中项目和所有可见项目
            current_selection = set(self.task_tree.selection())
            all_items = set(self.task_tree.get_children())
            
            if not all_items:
                self.show_message("提示", "暂无任务可操作", "info")
                return
            
            # 计算反选后的项目
            new_selection = all_items - current_selection
            
            # 应用新的选择
            self.task_tree.selection_set(list(new_selection))
            
            selected_count = len(new_selection)
            unselected_count = len(current_selection)
            self.log_action("反选操作", f"新选中 {selected_count} 个任务，取消选中 {unselected_count} 个任务")
            
        except Exception as e:
            self.logger.error(f"反选操作失败: {e}")
            self.show_message("错误", f"反选失败: {str(e)}", "error")
    
    def on_search_change(self, *args):
        """搜索框内容变化事件"""
        search_text = self.search_var.get().lower()
        
        # 首先重新显示所有项目（解决搜索状态管理问题）
        for item in self.all_task_items:
            try:
                self.task_tree.reattach(item, '', 'end')
            except tk.TclError:
                # 如果项目已经被删除或不存在，跳过
                pass
        
        # 如果搜索框为空，显示所有项目
        if not search_text:
            return
        
        # 过滤显示匹配的项目，使用完整项目列表确保所有数据都参与搜索
        for item in self.all_task_items:
            try:
                values = self.task_tree.item(item)['values']
                # 在所有字段中搜索：ID、赛事级别、赛事名称、联赛名称、国家、年份、类型、分组、最后爬取、创建时间
                if any(search_text in str(value).lower() for value in values):
                    self.task_tree.reattach(item, '', 'end')
                else:
                    self.task_tree.detach(item)
            except tk.TclError:
                # 如果项目已经被删除或不存在，跳过
                pass