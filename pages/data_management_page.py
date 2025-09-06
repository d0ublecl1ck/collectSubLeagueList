"""
数据管理页面 - 提供队伍数据的查看、编辑和统计功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from sqlalchemy import func
import webbrowser

from .base_page import BasePage
from models import Task, Team, Match, Standings


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
        
        # 任务搜索区域
        self.create_task_search_area()
        
        # 轮次选择区域
        self.create_round_selector()
        
        # 主要内容区域（赛程表和积分榜）
        self.create_main_content_area()
        
        # 统计信息
        self.create_statistics_panel()
        
        # 初始化数据
        self.all_task_items = []
        self.current_task_id = None
        self.current_round = None
        self.refresh_task_data()
        
    def create_task_search_area(self):
        """创建任务搜索区域"""
        # 任务搜索框架
        search_frame = ttk.LabelFrame(self.frame, text="任务搜索", padding=10)
        search_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 工具栏
        toolbar_frame = ttk.Frame(search_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 搜索框
        search_controls = ttk.Frame(toolbar_frame)
        search_controls.pack(side=tk.LEFT)
        
        ttk.Label(search_controls, text="搜索任务:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_task_search_change)
        search_entry = ttk.Entry(search_controls, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 刷新按钮
        refresh_btn = ttk.Button(toolbar_frame, text="刷新任务", command=self.refresh_task_data)
        refresh_btn.pack(side=tk.RIGHT)
        
        # 任务列表
        list_container = ttk.Frame(search_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建任务选择 Treeview
        columns = ('ID', '联赛名称', '国家', '年份', '类型', '分组', '最后爬取')
        self.task_tree = ttk.Treeview(list_container, columns=columns, show='headings', height=8)
        
        # 设置列标题和宽度
        self.task_tree.heading('ID', text='ID')
        self.task_tree.heading('联赛名称', text='联赛名称')
        self.task_tree.heading('国家', text='国家')
        self.task_tree.heading('年份', text='年份')
        self.task_tree.heading('类型', text='类型')
        self.task_tree.heading('分组', text='分组')
        self.task_tree.heading('最后爬取', text='最后爬取')
        
        self.task_tree.column('ID', width=50, anchor='center')
        self.task_tree.column('联赛名称', width=200)
        self.task_tree.column('国家', width=100)
        self.task_tree.column('年份', width=80, anchor='center')
        self.task_tree.column('类型', width=100, anchor='center')
        self.task_tree.column('分组', width=100, anchor='center')
        self.task_tree.column('最后爬取', width=120, anchor='center')
        
        # 滚动条
        task_scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=task_scrollbar.set)
        
        # 布局
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.task_tree.bind('<<TreeviewSelect>>', self.on_task_selected)
        
        # 统计信息栏
        stats_frame = ttk.Frame(search_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_label = ttk.Label(
            stats_frame, 
            text="总数: 0 | 显示: 0 | 选中: 0",
            font=('Arial', 9),
            foreground='blue'
        )
        self.stats_label.pack(side=tk.LEFT)
    
    def create_round_selector(self):
        """创建轮次选择区域"""
        round_frame = ttk.LabelFrame(self.frame, text="轮次选择", padding=10)
        round_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(round_frame, text="选择轮次:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.round_var = tk.StringVar()
        self.round_combo = ttk.Combobox(
            round_frame, 
            textvariable=self.round_var,
            state="readonly",
            width=20
        )
        self.round_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.round_combo.bind('<<ComboboxSelected>>', self.on_round_selected)
        
        # 积分榜类型选择
        ttk.Label(round_frame, text="积分榜类型:").pack(side=tk.LEFT, padx=(20, 5))
        self.standings_type_var = tk.StringVar()
        self.standings_type_combo = ttk.Combobox(
            round_frame,
            textvariable=self.standings_type_var,
            values=["总积分榜", "主场积分榜", "客场积分榜"],
            state="readonly",
            width=15
        )
        self.standings_type_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.standings_type_combo.set("总积分榜")
        self.standings_type_combo.bind('<<ComboboxSelected>>', self.on_standings_type_changed)
    
    def create_main_content_area(self):
        """创建主要内容区域（赛程表和积分榜）"""
        content_frame = ttk.Frame(self.frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 左侧：赛程表
        self.create_match_table(content_frame)
        
        # 右侧：积分榜
        self.create_standings_table(content_frame)
        
        # 设置权重
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
    
    def create_match_table(self, parent):
        """创建赛程表"""
        match_frame = ttk.LabelFrame(parent, text="赛程表", padding=10)
        match_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # 创建 Treeview
        match_columns = ('轮次', '时间', '主队', '主分', '客分', '客队', '状态')
        self.match_tree = ttk.Treeview(match_frame, columns=match_columns, show='headings', height=15)
        
        # 设置列标题和宽度
        self.match_tree.heading('轮次', text='轮次')
        self.match_tree.heading('时间', text='时间')
        self.match_tree.heading('主队', text='主队')
        self.match_tree.heading('主分', text='主分')
        self.match_tree.heading('客分', text='客分')
        self.match_tree.heading('客队', text='客队')
        self.match_tree.heading('状态', text='状态')
        
        self.match_tree.column('轮次', width=50, anchor='center')
        self.match_tree.column('时间', width=120, anchor='center')
        self.match_tree.column('主队', width=100, anchor='center')
        self.match_tree.column('主分', width=40, anchor='center')
        self.match_tree.column('客分', width=40, anchor='center')
        self.match_tree.column('客队', width=100, anchor='center')
        self.match_tree.column('状态', width=60, anchor='center')
        
        # 滚动条
        match_v_scrollbar = ttk.Scrollbar(match_frame, orient=tk.VERTICAL, command=self.match_tree.yview)
        self.match_tree.configure(yscrollcommand=match_v_scrollbar.set)
        
        # 布局
        self.match_tree.grid(row=0, column=0, sticky='nsew')
        match_v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        match_frame.grid_rowconfigure(0, weight=1)
        match_frame.grid_columnconfigure(0, weight=1)
    
    def create_standings_table(self, parent):
        """创建积分榜"""
        standings_frame = ttk.LabelFrame(parent, text="积分榜", padding=10)
        standings_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
        
        # 创建 Treeview
        standings_columns = ('排名', '队名', '场次', '胜', '平', '负', '进球', '失球', '净胜球', '积分', '胜率')
        self.standings_tree = ttk.Treeview(standings_frame, columns=standings_columns, show='headings', height=15)
        
        # 设置列标题和宽度
        self.standings_tree.heading('排名', text='排名')
        self.standings_tree.heading('队名', text='队名')
        self.standings_tree.heading('场次', text='场次')
        self.standings_tree.heading('胜', text='胜')
        self.standings_tree.heading('平', text='平')
        self.standings_tree.heading('负', text='负')
        self.standings_tree.heading('进球', text='进球')
        self.standings_tree.heading('失球', text='失球')
        self.standings_tree.heading('净胜球', text='净胜球')
        self.standings_tree.heading('积分', text='积分')
        self.standings_tree.heading('胜率', text='胜率')
        
        self.standings_tree.column('排名', width=50, anchor='center')
        self.standings_tree.column('队名', width=120, anchor='center')
        self.standings_tree.column('场次', width=50, anchor='center')
        self.standings_tree.column('胜', width=40, anchor='center')
        self.standings_tree.column('平', width=40, anchor='center')
        self.standings_tree.column('负', width=40, anchor='center')
        self.standings_tree.column('进球', width=50, anchor='center')
        self.standings_tree.column('失球', width=50, anchor='center')
        self.standings_tree.column('净胜球', width=60, anchor='center')
        self.standings_tree.column('积分', width=50, anchor='center')
        self.standings_tree.column('胜率', width=60, anchor='center')
        
        # 滚动条
        standings_v_scrollbar = ttk.Scrollbar(standings_frame, orient=tk.VERTICAL, command=self.standings_tree.yview)
        self.standings_tree.configure(yscrollcommand=standings_v_scrollbar.set)
        
        # 布局
        self.standings_tree.grid(row=0, column=0, sticky='nsew')
        standings_v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        standings_frame.grid_rowconfigure(0, weight=1)
        standings_frame.grid_columnconfigure(0, weight=1)
        
    def create_toolbar_old(self):
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
        
        # 初始化链接按钮容器
        self.link_buttons = []
    
    def open_link(self, url):
        """打开链接到浏览器"""
        try:
            webbrowser.open(url)
            self.logger.info(f"已打开链接: {url}")
        except Exception as e:
            self.logger.error(f"打开链接失败: {e}")
            self.show_message("错误", f"无法打开链接: {str(e)}", "error")
    
    def clear_link_buttons(self):
        """清空链接按钮"""
        for button in self.link_buttons:
            button.destroy()
        self.link_buttons.clear()
    
    def update_link_buttons(self, main_link=None, second_link=None):
        """更新链接按钮显示"""
        # 清空现有按钮
        self.clear_link_buttons()
        
        # 获取统计面板的父容器（从已完成标签获取）
        stats_frame = self.en_names_label.master
        
        # 主链接按钮 - 放在第0行第3列
        if main_link and main_link.strip():
            main_link_btn = ttk.Button(
                stats_frame,
                text="主链接",
                command=lambda url=main_link: self.open_link(url),
                width=8
            )
            main_link_btn.grid(row=0, column=3, sticky='w', padx=(20, 5))
            self.link_buttons.append(main_link_btn)
        
        # 备用链接按钮 - 放在第0行第4列
        if second_link and second_link.strip():
            second_link_btn = ttk.Button(
                stats_frame,
                text="备用链接", 
                command=lambda url=second_link: self.open_link(url),
                width=8
            )
            # 如果没有主链接，备用链接放在第3列；如果有主链接，放在第4列
            col_position = 3 if not (main_link and main_link.strip()) else 4
            second_link_btn.grid(row=0, column=col_position, sticky='w', padx=(5, 0))
            self.link_buttons.append(second_link_btn)
    
    # ========== 新的事件处理方法 ==========
    
    def refresh_task_data(self):
        """刷新任务数据"""
        try:
            # 清空任务树
            for item in self.task_tree.get_children():
                self.task_tree.delete(item)
            self.all_task_items.clear()
            
            # 从数据库加载任务
            with self.get_db_session() as session:
                tasks = session.query(Task).order_by(Task.created_at.desc()).all()
                
                for task in tasks:
                    last_crawl = task.last_crawl_time.strftime('%m-%d %H:%M') if task.last_crawl_time else '未爬取'
                    
                    item_id = self.task_tree.insert('', 'end', values=(
                        task.id,
                        task.league,
                        task.country, 
                        task.year,
                        task.type,
                        task.group,
                        last_crawl
                    ))
                    self.all_task_items.append(item_id)
                
            self.logger.info(f"加载了 {len(tasks)} 个任务")
            
        except Exception as e:
            self.logger.error(f"刷新任务数据失败: {e}")
            self.show_message("错误", f"加载任务失败: {str(e)}", "error")
        
        # 更新统计信息
        self.update_stats()
    
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
    
    def on_task_search_change(self, *args):
        """任务搜索框内容变化事件"""
        search_text = self.search_var.get().lower()
        
        # 重新显示所有项目
        for item in self.all_task_items:
            try:
                self.task_tree.reattach(item, '', 'end')
            except tk.TclError:
                pass
        
        # 如果搜索框为空，显示所有项目
        if not search_text:
            self.update_stats()
            return
        
        # 过滤显示匹配的项目
        for item in self.all_task_items:
            try:
                values = self.task_tree.item(item)['values']
                # 在所有字段中搜索
                if any(search_text in str(value).lower() for value in values):
                    self.task_tree.reattach(item, '', 'end')
                else:
                    self.task_tree.detach(item)
            except tk.TclError:
                pass
        
        # 更新统计信息
        self.update_stats()
    
    def on_task_selected(self, event=None):
        """任务选择事件处理"""
        selection = self.task_tree.selection()
        if not selection:
            self.current_task_id = None
            self.clear_data_displays()
            return
        
        # 获取选中的任务ID
        item = self.task_tree.item(selection[0])
        self.current_task_id = item['values'][0]
        
        # 加载轮次选择
        self.load_rounds_for_task(self.current_task_id)
        
        # 加载数据
        self.load_match_and_standings_data()
        
        # 更新统计信息
        self.update_stats()
    
    def load_rounds_for_task(self, task_id):
        """为选定任务加载轮次选择"""
        try:
            with self.get_db_session() as session:
                # 查询该任务的所有轮次
                rounds = session.query(Match.round_num).filter(
                    Match.task_id == task_id
                ).distinct().order_by(Match.round_num).all()
                
                round_values = ['全部轮次'] + [f"第{r[0]}轮" for r in rounds if r[0]]
                self.round_combo['values'] = round_values
                
                if round_values:
                    self.round_combo.set(round_values[0])
                    self.current_round = None  # 全部轮次
                    
        except Exception as e:
            self.logger.error(f"加载轮次失败: {e}")
            self.round_combo['values'] = ['全部轮次']
            self.round_combo.set('全部轮次')
    
    def on_round_selected(self, event=None):
        """轮次选择事件处理"""
        round_text = self.round_var.get()
        if round_text == '全部轮次':
            self.current_round = None
        else:
            # 提取轮次数字，如 "第1轮" -> 1
            import re
            match = re.search(r'第(\d+)轮', round_text)
            self.current_round = int(match.group(1)) if match else None
        
        # 重新加载数据
        self.load_match_and_standings_data()
    
    def on_standings_type_changed(self, event=None):
        """积分榜类型变化事件处理"""
        # 重新加载积分榜数据
        self.load_standings_data()
    
    def load_match_and_standings_data(self):
        """加载赛程和积分榜数据"""
        if not self.current_task_id:
            return
        
        self.load_match_data()
        self.load_standings_data()
        self.update_statistics_new()
    
    def load_match_data(self):
        """加载赛程数据"""
        try:
            # 清空赛程表
            for item in self.match_tree.get_children():
                self.match_tree.delete(item)
            
            with self.get_db_session() as session:
                # 构建查询
                query = session.query(Match, Team.home_name_cn.label('home_name'), Team.home_name_cn.label('away_name')).join(
                    Team, (Match.home_team_code == Team.team_code) & (Match.task_id == Team.task_id)
                ).filter(Match.task_id == self.current_task_id)
                
                # 如果选择了特定轮次
                if self.current_round:
                    query = query.filter(Match.round_num == self.current_round)
                
                matches = query.order_by(Match.round_num, Match.match_time).all()
                
                # 需要获取客队名称
                for match_data, home_name, _ in matches:
                    # 获取客队名称
                    away_team = session.query(Team).filter(
                        Team.team_code == match_data.away_team_code,
                        Team.task_id == self.current_task_id
                    ).first()
                    away_name = away_team.home_name_cn if away_team else f"队伍{match_data.away_team_code}"
                    
                    # 格式化比分 - 拆分为主分和客分
                    if match_data.full_score:
                        try:
                            # 解析比分格式 "5-2"
                            if '-' in match_data.full_score:
                                home_score, away_score = match_data.full_score.split('-', 1)
                                home_score = home_score.strip()
                                away_score = away_score.strip()
                            else:
                                home_score = match_data.full_score
                                away_score = match_data.full_score
                        except:
                            home_score = match_data.full_score
                            away_score = match_data.full_score
                    else:
                        home_score = ""
                        away_score = ""
                    
                    # 格式化时间（match_time是字符串格式）
                    if match_data.match_time:
                        # 如果是字符串格式 "2023-08-25 23:59"，提取月日时分
                        try:
                            if isinstance(match_data.match_time, str) and len(match_data.match_time) >= 16:
                                # 从 "2023-08-25 23:59" 提取 "08-25 23:59"
                                match_time = match_data.match_time[5:]  # 去掉年份部分
                            else:
                                match_time = str(match_data.match_time)
                        except:
                            match_time = str(match_data.match_time)
                    else:
                        match_time = '待定'
                    
                    # 状态判断
                    status = "已结束" if match_data.full_score else "未开始"
                    
                    self.match_tree.insert('', 'end', values=(
                        str(match_data.round_num),  # 轮次改为纯数字
                        match_time,
                        home_name or f"队伍{match_data.home_team_code}",
                        home_score,  # 主分
                        away_score,  # 客分
                        away_name,
                        status
                    ))
                    
        except Exception as e:
            self.logger.error(f"加载赛程数据失败: {e}")
            self.show_message("错误", f"加载赛程失败: {str(e)}", "error")
    
    def load_standings_data(self):
        """加载积分榜数据"""
        try:
            # 清空积分榜
            for item in self.standings_tree.get_children():
                self.standings_tree.delete(item)
            
            if not self.current_task_id:
                return
            
            # 获取积分榜类型映射
            type_mapping = {
                "总积分榜": "total",
                "主场积分榜": "home", 
                "客场积分榜": "away"
            }
            standings_category = type_mapping.get(self.standings_type_var.get(), "total")
            
            with self.get_db_session() as session:
                # 构建查询
                query = session.query(Standings, Team.home_name_cn).join(
                    Team, (Standings.team_code == Team.team_code) & (Standings.task_id == Team.task_id)
                ).filter(
                    Standings.task_id == self.current_task_id,
                    Standings.standings_category == standings_category
                )
                
                # 如果选择了特定轮次
                if self.current_round:
                    query = query.filter(Standings.round_num == self.current_round)
                else:
                    # 选择最新轮次的数据
                    latest_round = session.query(
                        func.max(Standings.round_num)
                    ).filter(
                        Standings.task_id == self.current_task_id,
                        Standings.standings_category == standings_category
                    ).scalar()
                    
                    if latest_round:
                        query = query.filter(Standings.round_num == latest_round)
                
                standings_data = query.order_by(Standings.points.desc(), Standings.goal_diff.desc()).all()
                
                # 填充积分榜
                for rank, (standing, team_name) in enumerate(standings_data, 1):
                    self.standings_tree.insert('', 'end', values=(
                        rank,
                        team_name or f"队伍{standing.team_code}",
                        standing.games,
                        standing.wins,
                        standing.draws,
                        standing.losses,
                        standing.goals_for,
                        standing.goals_against,
                        standing.goal_diff,
                        standing.points,
                        standing.win_pct
                    ))
                    
        except Exception as e:
            self.logger.error(f"加载积分榜数据失败: {e}")
            self.show_message("错误", f"加载积分榜失败: {str(e)}", "error")
    
    def clear_data_displays(self):
        """清空数据显示"""
        # 清空赛程表
        for item in self.match_tree.get_children():
            self.match_tree.delete(item)
        
        # 清空积分榜
        for item in self.standings_tree.get_children():
            self.standings_tree.delete(item)
        
        # 清空轮次选择
        self.round_combo['values'] = []
        self.round_var.set('')
        
        # 清空链接按钮
        self.clear_link_buttons()
    
    def update_statistics_new(self):
        """更新统计信息"""
        if not self.current_task_id:
            self.total_teams_label.config(text="总队伍数: 0")
            self.cn_names_label.config(text="比赛场次: 0")
            self.en_names_label.config(text="已完成: 0")
            self.groups_label.config(text="积分榜类型: 未选择")
            self.last_update_label.config(text="最后更新: 未知")
            self.clear_link_buttons()
            return
        
        try:
            with self.get_db_session() as session:
                # 获取当前任务信息
                current_task = session.query(Task).filter(Task.id == self.current_task_id).first()
                
                # 统计队伍数
                team_count = session.query(Team).filter(Team.task_id == self.current_task_id).count()
                
                # 统计比赛场次
                match_count = session.query(Match).filter(Match.task_id == self.current_task_id).count()
                
                # 统计已完成比赛
                finished_count = session.query(Match).filter(
                    Match.task_id == self.current_task_id,
                    Match.full_score.isnot(None)
                ).count()
                
                # 获取最后更新时间
                last_update = session.query(func.max(Match.updated_at)).filter(
                    Match.task_id == self.current_task_id
                ).scalar()
                
                last_update_str = last_update.strftime('%Y-%m-%d %H:%M:%S') if last_update else '未知'
                
                # 在会话内提取链接值，避免DetachedInstanceError
                main_link = current_task.link if current_task else None
                second_link = current_task.link_second if current_task else None
                
                # 更新显示
                self.total_teams_label.config(text=f"总队伍数: {team_count}")
                self.cn_names_label.config(text=f"比赛场次: {match_count}")
                self.en_names_label.config(text=f"已完成: {finished_count}")
                self.groups_label.config(text=f"积分榜类型: {self.standings_type_var.get()}")
                self.last_update_label.config(text=f"最后更新: {last_update_str}")
                
                # 更新链接按钮（传递字符串而不是对象）
                self.update_link_buttons(main_link, second_link)
                
        except Exception as e:
            self.logger.error(f"更新统计信息失败: {e}")
