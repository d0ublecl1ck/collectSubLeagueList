"""
数据管理页面 - 提供队伍数据的查看、编辑和统计功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from .base_page import BasePage
from models import Task, Team


class DataManagementPage(BasePage):
    """数据管理页面 - 队伍数据管理界面"""
    
    def setup_ui(self):
        """设置数据管理页面的用户界面"""
        # 页面标题
        title_label = ttk.Label(
            self.frame, 
            text="数据管理", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # 任务选择器
        self.create_task_selector()
        
        # 工具栏
        self.create_toolbar()
        
        # 队伍数据表格
        self.create_team_table()
        
        # 统计信息
        self.create_statistics_panel()
        
        # 初始化
        self.refresh_task_list()
        
    def create_task_selector(self):
        """创建任务选择器"""
        selector_frame = ttk.LabelFrame(self.frame, text="选择联赛任务", padding=10)
        selector_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(selector_frame, text="任务:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.task_var = tk.StringVar()
        self.task_combo = ttk.Combobox(
            selector_frame, 
            textvariable=self.task_var,
            state="readonly",
            width=50
        )
        self.task_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.task_combo.bind('<<ComboboxSelected>>', self.on_task_selected)
        
        refresh_btn = ttk.Button(selector_frame, text="刷新", command=self.refresh_task_list)
        refresh_btn.pack(side=tk.LEFT)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(self.frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 数据操作按钮
        export_btn = ttk.Button(toolbar_frame, text="导出数据", command=self.export_data, width=12)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        import_btn = ttk.Button(toolbar_frame, text="导入数据", command=self.import_data, width=12)
        import_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        delete_btn = ttk.Button(toolbar_frame, text="删除选中", command=self.delete_selected_teams, width=12)
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 搜索框
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="搜索队伍:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)
        
    def create_team_table(self):
        """创建队伍数据表格"""
        table_frame = ttk.LabelFrame(self.frame, text="队伍数据", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 创建 Treeview
        columns = ('队伍编码', '中文名', '英文名', '联赛ID', '轮次', '分组ID', '更新时间')
        self.team_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题和宽度
        self.team_tree.heading('队伍编码', text='队伍编码')
        self.team_tree.heading('中文名', text='中文名称')
        self.team_tree.heading('英文名', text='英文名称')
        self.team_tree.heading('联赛ID', text='联赛ID')
        self.team_tree.heading('轮次', text='轮次')
        self.team_tree.heading('分组ID', text='分组ID')
        self.team_tree.heading('更新时间', text='更新时间')
        
        self.team_tree.column('队伍编码', width=80, anchor='center')
        self.team_tree.column('中文名', width=150)
        self.team_tree.column('英文名', width=150)
        self.team_tree.column('联赛ID', width=80, anchor='center')
        self.team_tree.column('轮次', width=80, anchor='center')
        self.team_tree.column('分组ID', width=80, anchor='center')
        self.team_tree.column('更新时间', width=120, anchor='center')
        
        # 滚动条
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.team_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.team_tree.xview)
        self.team_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.team_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # 双击编辑事件
        self.team_tree.bind('<Double-1>', self.on_team_double_click)
        
    def create_statistics_panel(self):
        """创建统计信息面板"""
        stats_frame = ttk.LabelFrame(self.frame, text="统计信息", padding=15)
        stats_frame.pack(fill=tk.X)
        
        # 统计信息网格
        self.total_teams_label = ttk.Label(stats_frame, text="总队伍数: 0")
        self.total_teams_label.grid(row=0, column=0, sticky='w', padx=(0, 20))
        
        self.cn_names_label = ttk.Label(stats_frame, text="有中文名: 0")
        self.cn_names_label.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        self.en_names_label = ttk.Label(stats_frame, text="有英文名: 0")
        self.en_names_label.grid(row=0, column=2, sticky='w', padx=(0, 20))
        
        self.groups_label = ttk.Label(stats_frame, text="分组数: 0")
        self.groups_label.grid(row=1, column=0, sticky='w', padx=(0, 20), pady=(5, 0))
        
        self.last_update_label = ttk.Label(stats_frame, text="最后更新: 未知")
        self.last_update_label.grid(row=1, column=1, sticky='w', padx=(0, 20), pady=(5, 0))
        
    def refresh_task_list(self):
        """刷新任务列表"""
        try:
            with self.get_db_session() as session:
                tasks = session.query(Task).order_by(Task.created_at.desc()).all()
                
                task_values = []
                self.task_dict = {}
                
                for task in tasks:
                    display_text = f"[{task.id}] {task.league} ({task.year}) - {task.country}"
                    task_values.append(display_text)
                    self.task_dict[display_text] = task.id
                
                self.task_combo['values'] = task_values
                if task_values:
                    self.task_combo.set(task_values[0])
                    self.on_task_selected()
                    
        except Exception as e:
            self.logger.error(f"刷新任务列表失败: {e}")
            self.show_message("错误", f"刷新任务列表失败: {str(e)}", "error")
            
    def on_task_selected(self, event=None):
        """任务选择事件处理"""
        selected_task = self.task_var.get()
        if not selected_task or selected_task not in self.task_dict:
            return
            
        task_id = self.task_dict[selected_task]
        self.load_team_data(task_id)
        
    def load_team_data(self, task_id):
        """加载队伍数据"""
        try:
            # 清空现有数据
            for item in self.team_tree.get_children():
                self.team_tree.delete(item)
                
            # 从数据库加载数据
            with self.get_db_session() as session:
                teams = session.query(Team).filter(Team.task_id == task_id).order_by(Team.team_code).all()
                
                for team in teams:
                    update_time = team.updated_at.strftime('%m-%d %H:%M') if team.updated_at else ''
                    self.team_tree.insert('', 'end', values=(
                        team.team_code,
                        team.home_name_cn or '',
                        team.home_name_en or '',
                        team.league_id,
                        team.round_num or '',
                        team.group_id or '',
                        update_time
                    ))
                    
                # 更新统计信息
                self.update_statistics(teams)
                
            self.log_action("加载队伍数据", f"任务ID: {task_id}, 队伍数: {len(teams)}")
            
        except Exception as e:
            self.logger.error(f"加载队伍数据失败: {e}")
            self.show_message("错误", f"加载数据失败: {str(e)}", "error")
            
    def update_statistics(self, teams):
        """更新统计信息"""
        total_count = len(teams)
        cn_names_count = sum(1 for team in teams if team.home_name_cn)
        en_names_count = sum(1 for team in teams if team.home_name_en)
        groups_count = len(set(team.group_id for team in teams if team.group_id))
        
        last_update = max(team.updated_at for team in teams if team.updated_at) if teams else None
        last_update_str = last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else '未知'
        
        self.total_teams_label.config(text=f"总队伍数: {total_count}")
        self.cn_names_label.config(text=f"有中文名: {cn_names_count}")
        self.en_names_label.config(text=f"有英文名: {en_names_count}")
        self.groups_label.config(text=f"分组数: {groups_count}")
        self.last_update_label.config(text=f"最后更新: {last_update_str}")
        
    def on_team_double_click(self, event):
        """队伍双击编辑事件"""
        selection = self.team_tree.selection()
        if not selection:
            return
            
        item = self.team_tree.item(selection[0])
        team_code = item['values'][0]
        
        self.show_message("提示", f"队伍编辑功能开发中...\n队伍编码: {team_code}", "info")
        
    def on_search_change(self, *args):
        """搜索框内容变化事件"""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            for item in self.team_tree.get_children():
                self.team_tree.reattach(item, '', 'end')
            return
            
        all_items = self.team_tree.get_children()
        for item in all_items:
            values = self.team_tree.item(item)['values']
            # 在队伍名称中搜索
            if (search_text in str(values[1]).lower() or 
                search_text in str(values[2]).lower() or
                search_text in str(values[0]).lower()):
                self.team_tree.reattach(item, '', 'end')
            else:
                self.team_tree.detach(item)
                
    def export_data(self):
        """导出数据到CSV文件"""
        try:
            if not self.task_var.get() or self.task_var.get() not in self.task_dict:
                self.show_message("提示", "请先选择一个任务", "warning")
                return
                
            # 选择保存文件
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
                title="导出队伍数据"
            )
            
            if not filename:
                return
                
            task_id = self.task_dict[self.task_var.get()]
            
            with self.get_db_session() as session:
                teams = session.query(Team).filter(Team.task_id == task_id).all()
                
                import csv
                with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    writer = csv.writer(csvfile)
                    # 写入表头
                    writer.writerow(['队伍编码', '中文名称', '繁体名称', '英文名称', '图片路径', 
                                   '联赛ID', '轮次', '分类ID', '分组ID', '创建时间', '更新时间'])
                    
                    # 写入数据
                    for team in teams:
                        writer.writerow([
                            team.team_code,
                            team.home_name_cn or '',
                            team.home_name_tw or '',
                            team.home_name_en or '',
                            team.image_path or '',
                            team.league_id,
                            team.round_num or '',
                            team.sclass_id or '',
                            team.group_id or '',
                            team.created_at.strftime('%Y-%m-%d %H:%M:%S') if team.created_at else '',
                            team.updated_at.strftime('%Y-%m-%d %H:%M:%S') if team.updated_at else ''
                        ])
                        
            self.show_message("成功", f"数据已导出到: {filename}\n共导出 {len(teams)} 条记录", "info")
            self.log_action("导出数据", f"文件: {filename}, 记录数: {len(teams)}")
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
            self.show_message("错误", f"导出失败: {str(e)}", "error")
            
    def import_data(self):
        """从CSV文件导入数据"""
        self.show_message("提示", "数据导入功能开发中...", "info")
        
    def delete_selected_teams(self):
        """删除选中的队伍"""
        selection = self.team_tree.selection()
        if not selection:
            self.show_message("提示", "请先选择要删除的队伍", "warning")
            return
            
        # 确认删除
        team_codes = [self.team_tree.item(item)['values'][0] for item in selection]
        
        if not messagebox.askyesno(
            "确认删除", 
            f"确定要删除选中的 {len(team_codes)} 个队伍吗？\n\n此操作无法恢复！"
        ):
            return
            
        try:
            with self.get_db_session() as session:
                for team_code in team_codes:
                    team = session.query(Team).filter(Team.team_code == team_code).first()
                    if team:
                        session.delete(team)
                        
                session.commit()
                
            self.show_message("成功", f"已删除 {len(team_codes)} 个队伍", "info")
            self.log_action("删除队伍", f"数量: {len(team_codes)}")
            
            # 刷新数据
            self.on_task_selected()
            
        except Exception as e:
            self.logger.error(f"删除队伍失败: {e}")
            self.show_message("错误", f"删除失败: {str(e)}", "error")