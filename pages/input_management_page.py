"""
输入管理页面 - 提供任务列表的查看、编辑和删除功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import re
import os
from openpyxl import Workbook

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
        
        # 导出按钮
        export_btn = ttk.Button(
            toolbar_frame,
            text="导出Excel",
            command=self.export_to_excel,
            width=12
        )
        export_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 搜索框
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)
        
        # 统计信息栏
        stats_frame = ttk.Frame(self.frame)
        stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.stats_label = ttk.Label(
            stats_frame, 
            text="总数: 0 | 显示: 0 | 选中: 0",
            font=('Arial', 9),
            foreground='blue'
        )
        self.stats_label.pack(side=tk.LEFT)
        
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
        columns = ('ID', '赛事级别', '赛事名称', '联赛名称', '国家', '年份', '类型', '分组', '主要链接', '备用链接', '最后爬取', '创建时间')
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
        self.task_tree.heading('主要链接', text='主要链接')
        self.task_tree.heading('备用链接', text='备用链接')
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
        self.task_tree.column('主要链接', width=150)
        self.task_tree.column('备用链接', width=150)
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
        
        # 绑定选择事件和双击编辑事件
        self.task_tree.bind('<<TreeviewSelect>>', self.on_task_select)
        self.task_tree.bind('<Double-1>', self.on_double_click)
        
        # 初始化编辑状态变量
        self.edit_item = None
        self.edit_column = None
        self.edit_widget = None
        
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
                        task.link or '',
                        task.link_second or '',
                        last_crawl_time,
                        created_time
                    ))
                    # 保存到完整项目列表
                    self.all_task_items.append(item_id)
            
            self.log_action("刷新任务列表", f"加载了 {len(tasks)} 条记录")
            
            # 更新统计信息
            self.update_stats()
            
        except Exception as e:
            self.logger.error(f"刷新数据失败: {e}")
            self.show_message("错误", f"刷新数据失败: {str(e)}", "error")
    
    def on_task_select(self, event):
        """任务选择事件处理"""
        selection = self.task_tree.selection()
        if not selection:
            self.clear_detail()
            self.update_stats()
            return
            
        # 获取选中的任务ID
        item = self.task_tree.item(selection[0])
        task_id = item['values'][0]
        
        # 加载任务详情
        self.load_task_detail(task_id)
        
        # 更新统计信息
        self.update_stats()
    
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
                self.update_stats()
                    
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
                self.update_stats()
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
            self.update_stats()
            
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
            self.update_stats()
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
        
        # 更新统计信息
        self.update_stats()
    
    def on_double_click(self, event):
        """处理双击事件"""
        # 取消当前编辑（如果有）
        self.cancel_edit()
        
        # 确定双击的位置
        item = self.task_tree.identify_row(event.y)
        column = self.task_tree.identify_column(event.x)
        
        if not item or not column:
            return
        
        # 获取列名
        column_index = int(column[1:]) - 1  # 列编号从#1开始
        columns = ('ID', '赛事级别', '赛事名称', '联赛名称', '国家', '年份', '类型', '分组', '主要链接', '备用链接', '最后爬取', '创建时间')
        
        if column_index < 0 or column_index >= len(columns):
            return
            
        column_name = columns[column_index]
        
        # 检查是否可编辑
        readonly_columns = ['ID', '最后爬取', '创建时间']
        if column_name in readonly_columns:
            self.show_message("提示", f"{column_name} 字段不可编辑", "warning")
            return
        
        # 开始编辑
        self.start_edit_cell(item, column_name, column_index)
    
    def start_edit_cell(self, item, column_name, column_index):
        """开始编辑单元格"""
        # 记录编辑状态
        self.edit_item = item
        self.edit_column = column_name
        
        # 获取当前值
        current_values = self.task_tree.item(item, 'values')
        current_value = current_values[column_index]
        
        # 获取单元格位置
        bbox = self.task_tree.bbox(item, f'#{column_index + 1}')
        if not bbox:
            return
        
        x, y, width, height = bbox
        
        # 创建编辑控件
        if column_name == '类型':
            # 下拉框编辑
            self.edit_widget = ttk.Combobox(
                self.task_tree,
                values=['常规', '东西拆分', '联二合并', '春秋合并'],
                state='readonly'
            )
            self.edit_widget.set(current_value)
        else:
            # 文本框编辑
            self.edit_widget = tk.Entry(self.task_tree)
            self.edit_widget.insert(0, current_value)
            self.edit_widget.select_range(0, tk.END)
        
        # 放置编辑控件
        self.edit_widget.place(x=x, y=y, width=width, height=height)
        self.edit_widget.focus_set()
        
        # 绑定事件
        self.edit_widget.bind('<Return>', self.save_edit)
        self.edit_widget.bind('<Escape>', self.cancel_edit)
        self.edit_widget.bind('<FocusOut>', self.save_edit)
    
    def save_edit(self, event=None):
        """保存编辑"""
        if not self.edit_widget or not self.edit_item:
            return
        
        try:
            # 获取新值
            new_value = self.edit_widget.get().strip()
            
            # 验证输入
            if not self.validate_input(self.edit_column, new_value):
                return
            
            # 获取任务ID
            item_values = self.task_tree.item(self.edit_item, 'values')
            task_id = item_values[0]
            
            # 更新数据库
            with self.get_db_session() as session:
                task = session.query(Task).filter(Task.id == task_id).first()
                if task:
                    # 根据列名更新对应字段
                    field_mapping = {
                        '赛事级别': 'level',
                        '赛事名称': 'event',
                        '联赛名称': 'league',
                        '国家': 'country',
                        '年份': 'year',
                        '类型': 'type',
                        '分组': 'group',
                        '主要链接': 'link',
                        '备用链接': 'link_second'
                    }
                    
                    if self.edit_column in field_mapping:
                        field_name = field_mapping[self.edit_column]
                        setattr(task, field_name, new_value if new_value else None)
                        task.updated_at = datetime.now()
                        session.commit()
                        
                        # 刷新显示
                        self.refresh_data()
                        self.log_action("编辑任务", f"更新任务 {task_id} 的 {self.edit_column}: {new_value}")
                        self.update_stats()
            
        except Exception as e:
            self.logger.error(f"保存编辑失败: {e}")
            self.show_message("错误", f"保存失败: {str(e)}", "error")
        finally:
            self.cancel_edit()
    
    def cancel_edit(self, event=None):
        """取消编辑"""
        if self.edit_widget:
            self.edit_widget.destroy()
            self.edit_widget = None
        self.edit_item = None
        self.edit_column = None
    
    def validate_input(self, column_name, value):
        """验证输入"""
        if column_name in ['赛事级别', '赛事名称', '联赛名称', '国家', '分组'] and not value:
            self.show_message("错误", f"{column_name} 不能为空", "error")
            return False
        
        if column_name == '赛事级别':
            try:
                int(value)
            except ValueError:
                self.show_message("错误", "赛事级别必须为数字", "error")
                return False
        
        if column_name == '年份':
            if value:
                try:
                    year = int(value)
                    if len(value) != 4 or year < 1900 or year > 2100:
                        self.show_message("错误", "年份格式不正确（请输入4位数字，如2024）", "error")
                        return False
                except ValueError:
                    self.show_message("错误", "年份必须为数字", "error")
                    return False
        
        if column_name == '类型':
            valid_types = ['常规', '东西拆分', '联二合并', '春秋合并']
            if value not in valid_types:
                self.show_message("错误", f"类型必须为: {'/'.join(valid_types)}", "error")
                return False
        
        if column_name in ['主要链接', '备用链接'] and value:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(value):
                self.show_message("错误", f"{column_name} URL格式不正确", "error")
                return False
        
        return True
    
    def export_to_excel(self):
        """导出任务数据到Excel文件"""
        try:
            # 从数据库查询所有任务数据
            with self.get_db_session() as session:
                tasks = session.query(Task).order_by(Task.created_at.desc()).all()
                
                if not tasks:
                    self.show_message("提示", "暂无任务数据可导出", "info")
                    return
                
                # 让用户选择保存位置
                file_path = filedialog.asksaveasfilename(
                    title="保存Excel文件",
                    defaultextension=".xlsx",
                    filetypes=[("Excel文件", "*.xlsx"), ("所有文件", "*.*")],
                    initialfile="任务数据导出.xlsx"
                )
                
                if not file_path:
                    return  # 用户取消了保存
                
                # 创建工作簿和工作表
                wb = Workbook()
                ws = wb.active
                ws.title = "任务数据"
                
                # 设置表头
                headers = ['赛事级别', '赛事名称', '国家/地区', '联赛名称', '赛事类型', '主要链接', '第二链接', '赛事年份', '分组信息']
                ws.append(headers)
                
                # 添加数据行
                for task in tasks:
                    row_data = [
                        task.level,
                        task.event or '',
                        task.country or '',
                        task.league or '',
                        task.type or '',
                        task.link or '',
                        task.link_second or '',
                        task.year or '',
                        task.group or ''
                    ]
                    ws.append(row_data)
                
                # 调整列宽
                column_widths = [10, 20, 15, 25, 12, 40, 40, 12, 15]
                for i, width in enumerate(column_widths, 1):
                    ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width
                
                # 设置表头样式
                for cell in ws[1]:
                    cell.font = cell.font.copy(bold=True)
                
                # 保存文件
                wb.save(file_path)
                
                # 显示成功消息
                self.show_message("成功", f"成功导出 {len(tasks)} 条任务数据到:\n{os.path.basename(file_path)}", "info")
                self.log_action("导出Excel", f"成功导出 {len(tasks)} 条任务数据到 {file_path}")
                
        except Exception as e:
            self.logger.error(f"导出Excel失败: {e}")
            self.show_message("错误", f"导出失败: {str(e)}", "error")
    
    def update_stats(self):
        """更新统计信息显示"""
        try:
            # 获取数据库总数
            with self.get_db_session() as session:
                total_count = session.query(Task).count()
            
            # 获取当前显示数量
            visible_count = len(self.task_tree.get_children())
            
            # 获取选中数量
            selected_count = len(self.task_tree.selection())
            
            # 更新显示
            stats_text = f"总数: {total_count} | 显示: {visible_count} | 选中: {selected_count}"
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
            self.stats_label.config(text="统计信息加载失败")