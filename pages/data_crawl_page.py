# -*- coding: utf-8 -*-
"""
数据爬取页面 - 提供爬虫执行控制和进度监控界面
"""

import re
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk

import requests

from models import JsDataRaw, Match, Standings, Task, Team
from .base_page import BasePage


class DataCrawlPage(BasePage):
    """数据爬取页面 - 爬虫控制界面"""

    def setup_ui(self):
        """设置数据爬取页面的用户界面"""
        # 页面标题
        title_label = ttk.Label(
            self.frame,
            text="数据爬取",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # 任务选择区域
        self.create_task_selection()

        # 爬取控制区域
        self.create_crawl_controls()

        # 进度监控区域
        self.create_progress_monitor()

        # 日志显示区域
        self.create_log_display()

        # 初始化状态
        self.is_crawling = False
        self.crawl_thread = None

        # 加载任务列表
        self.refresh_task_list()

    def create_task_selection(self):
        """创建任务选择区域"""
        selection_frame = ttk.LabelFrame(self.frame, text="选择爬取任务", padding=15)
        selection_frame.pack(fill=tk.X, pady=(0, 15))

        # 任务列表
        ttk.Label(selection_frame, text="待爬取任务:").grid(row=0, column=0, sticky='w', pady=(0, 5))

        self.task_listbox = tk.Listbox(selection_frame, height=6, selectmode=tk.MULTIPLE)
        self.task_listbox.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 10))

        # 滚动条
        task_scrollbar = ttk.Scrollbar(selection_frame, orient=tk.VERTICAL, command=self.task_listbox.yview)
        self.task_listbox.config(yscrollcommand=task_scrollbar.set)
        task_scrollbar.grid(row=1, column=2, sticky='ns', pady=(0, 10))

        # 刷新按钮
        refresh_btn = ttk.Button(selection_frame, text="刷新任务列表", command=self.refresh_task_list)
        refresh_btn.grid(row=2, column=0, sticky='w')

        # 全选/全不选按钮
        select_all_btn = ttk.Button(selection_frame, text="全选", command=self.select_all_tasks)
        select_all_btn.grid(row=2, column=1, padx=(10, 0), sticky='w')

        selection_frame.grid_columnconfigure(0, weight=1)

    def create_crawl_controls(self):
        """创建爬取控制区域"""
        control_frame = ttk.LabelFrame(self.frame, text="爬取控制", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))

        # 爬取设置
        settings_frame = ttk.Frame(control_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(settings_frame, text="并发数:").grid(row=0, column=0, sticky='e', padx=(0, 5))
        self.concurrent_var = tk.IntVar(value=5)
        concurrent_spin = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.concurrent_var, width=10)
        concurrent_spin.grid(row=0, column=1, sticky='w', padx=(0, 20))

        ttk.Label(settings_frame, text="延迟(秒):").grid(row=0, column=2, sticky='e', padx=(0, 5))
        self.delay_var = tk.DoubleVar(value=0)
        delay_spin = ttk.Spinbox(settings_frame, from_=0.1, to=10.0, increment=0.1, textvariable=self.delay_var, width=10)
        delay_spin.grid(row=0, column=3, sticky='w')

        # 控制按钮
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(button_frame, text="开始爬取", command=self.start_crawl, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.pause_btn = ttk.Button(button_frame, text="暂停", command=self.pause_crawl, width=15, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="停止", command=self.stop_crawl, width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

    def create_progress_monitor(self):
        """创建进度监控区域"""
        progress_frame = ttk.LabelFrame(self.frame, text="爬取进度", padding=15)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        # 整体进度
        ttk.Label(progress_frame, text="整体进度:").grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.overall_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.overall_progress.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 10))

        # 当前任务进度
        ttk.Label(progress_frame, text="当前任务:").grid(row=2, column=0, sticky='w', pady=(0, 5))
        self.current_task_label = ttk.Label(progress_frame, text="未开始", foreground='blue')
        self.current_task_label.grid(row=2, column=1, sticky='w', pady=(0, 5))

        self.current_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.current_progress.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(0, 10))

        # 统计信息
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=4, column=0, columnspan=2, sticky='ew')

        self.stats_label = ttk.Label(stats_frame, text="成功: 0 | 失败: 0 | 总计: 0")
        self.stats_label.pack(side=tk.LEFT)

        self.time_label = ttk.Label(stats_frame, text="用时: 00:00:00")
        self.time_label.pack(side=tk.RIGHT)

        progress_frame.grid_columnconfigure(0, weight=1)

    def create_log_display(self):
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(self.frame, text="爬取日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            wrap=tk.WORD,
            font=('Consolas', 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 日志控制按钮
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill=tk.X)

        clear_log_btn = ttk.Button(log_control_frame, text="清空日志", command=self.clear_log)
        clear_log_btn.pack(side=tk.LEFT)

        save_log_btn = ttk.Button(log_control_frame, text="保存日志", command=self.save_log)
        save_log_btn.pack(side=tk.LEFT, padx=(10, 0))

    def refresh_task_list(self):
        """刷新任务列表"""
        self.task_listbox.delete(0, tk.END)

        with self.get_db_session() as session:
            tasks = session.query(Task).order_by(Task.created_at.desc()).all()

            for task in tasks:
                display_text = f"[{task.id}] {task.league} ({task.year}) - {task.country}"
                self.task_listbox.insert(tk.END, display_text)

        self.add_log(f"加载了 {len(tasks)} 个任务")

    def select_all_tasks(self):
        """全选/全不选任务"""
        if self.task_listbox.size() == 0:
            return

        # 检查当前是否全选
        selected_count = len(self.task_listbox.curselection())
        total_count = self.task_listbox.size()

        if selected_count == total_count:
            # 全不选
            self.task_listbox.selection_clear(0, tk.END)
        else:
            # 全选
            self.task_listbox.selection_set(0, tk.END)

    def start_crawl(self):
        """开始爬取"""
        selected_indices = self.task_listbox.curselection()
        if not selected_indices:
            self.show_message("提示", "请选择要爬取的任务", "warning")
            return

        self.is_crawling = True
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)

        # 启动爬取线程
        self.crawl_thread = threading.Thread(target=self.crawl_worker, args=(selected_indices,))
        self.crawl_thread.daemon = True
        self.crawl_thread.start()

        self.add_log(f"开始爬取 {len(selected_indices)} 个任务")
        self.log_action("开始爬取", f"任务数: {len(selected_indices)}")

    def pause_crawl(self):
        """暂停爬取"""
        self.is_crawling = False
        self.add_log("爬取已暂停")

    def stop_crawl(self):
        """停止爬取"""
        self.is_crawling = False
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)

        self.current_task_label.config(text="已停止")
        self.current_progress.stop()

        self.add_log("爬取已停止")
        self.log_action("停止爬取")

    def crawl_worker(self, selected_indices):
        """爬取工作线程"""
        start_time = time.time()
        total_tasks = len(selected_indices)
        success_count = 0
        failed_count = 0

        try:
            for i, index in enumerate(selected_indices):
                if not self.is_crawling:
                    break

                # 更新整体进度
                progress_value = (i / total_tasks) * 100
                self.overall_progress['value'] = progress_value

                # 获取任务信息
                task_text = self.task_listbox.get(index)
                task_id = int(task_text.split(']')[0][1:])

                # 更新当前任务显示
                self.current_task_label.config(text=f"正在爬取: {task_text}")
                self.current_progress.start()

                self.add_log(f"开始爬取任务 {task_id}: {task_text}")

                # 执行真实爬取过程
                crawl_success = self.crawl_task(task_id)

                if crawl_success:
                    success_count += 1
                    self.add_log(f"任务 {task_id} 爬取成功", "SUCCESS")
                else:
                    failed_count += 1
                    self.add_log(f"任务 {task_id} 爬取失败", "ERROR")

                # 更新统计信息
                elapsed_time = time.time() - start_time
                time_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_time))
                self.stats_label.config(text=f"成功: {success_count} | 失败: {failed_count} | 总计: {i + 1}/{total_tasks}")
                self.time_label.config(text=f"用时: {time_str}")

                # 延迟
                time.sleep(self.delay_var.get())

        finally:
            # 完成爬取
            self.overall_progress['value'] = 100
            self.current_progress.stop()
            self.current_task_label.config(text="爬取完成")

            self.start_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)

            total_time = time.time() - start_time
            time_str = time.strftime('%H:%M:%S', time.gmtime(total_time))
            self.add_log(f"爬取完成! 成功: {success_count}, 失败: {failed_count}, 总用时: {time_str}")

    def crawl_task(self, task_id):
        """执行真实的任务爬取"""
        with self.get_db_session() as session:
            task = session.query(Task).filter(Task.id == task_id).first()
            if not task:
                self.logger.error(f"任务 {task_id} 不存在")
                return False

            self.logger.info(f"开始爬取任务: {task.league} ({task.type})")

            # 根据任务类型执行不同的爬取策略
            if task.type == '常规':
                success = self.crawl_regular_task(task, session)
            elif task.type == '东西拆分':
                success = self.crawl_east_west_split_task(task, session)
            elif task.type in ['联二合并', '春秋合并']:
                success = self.crawl_merge_task(task, session)
            else:
                self.logger.error(f"未知的任务类型: {task.type}")
                return False

            if success:
                task.last_crawl_time = datetime.now()
                session.commit()
                self.logger.info(f"任务 {task_id} 爬取成功")
            else:
                self.logger.error(f"任务 {task_id} 爬取失败")

            return success

    def crawl_regular_task(self, task, session):
        """爬取常规任务"""
        if not task.link:
            self.logger.error("常规任务缺少主链接")
            return False

            # 爬取和解析数据
        js_data_record, team_data, _ = self.fetch_and_parse_link(
            task.link, 'primary', task, session
        )

        if not js_data_record:
            return False

        # 保存Team数据
        self.save_team_data(team_data, task, js_data_record.id, session)

        # 解析比赛数据
        match_data = self.parse_match_data(js_data_record.js_data_raw)

        # 保存比赛数据
        self.save_match_data(match_data, task, js_data_record.id, session)

        # 计算三种积分榜
        calculated_standings = self.calculate_three_type_standings(match_data, team_data)

        # 保存结构化积分榜数据
        self.save_structured_standings(calculated_standings, task, session)

        return True

    def crawl_east_west_split_task(self, task, session):
        """爬取东西拆分任务"""
        if not task.link:
            self.logger.error("东西拆分任务缺少主链接")
            return False

        # 爬取和解析数据
        js_data_record, team_data, _ = self.fetch_and_parse_link(
            task.link, 'primary', task, session
        )

        if not js_data_record:
            return False

        # 保存Team数据
        self.save_team_data(team_data, task, js_data_record.id, session)

        # 解析比赛数据
        match_data = self.parse_match_data(js_data_record.js_data_raw)

        # 保存比赛数据
        self.save_match_data(match_data, task, js_data_record.id, session)

        # 计算三种积分榜
        calculated_standings = self.calculate_three_type_standings(match_data, team_data)

        # 为东西拆分任务保存结构化积分榜（按分区处理）
        self.save_east_west_structured_standings(calculated_standings, team_data, task, session)

        return True

    def crawl_merge_task(self, task, session):
        """爬取合并类型任务"""
        if not task.link or not task.link_second:
            self.logger.error(f"合并任务缺少链接: link={task.link}, link_second={task.link_second}")
            return False

        # 爬取第一个链接
        js_data1, team_data1, _ = self.fetch_and_parse_link(
            task.link, 'primary', task, session
        )

        # 爬取第二个链接
        js_data2, team_data2, _ = self.fetch_and_parse_link(
            task.link_second, 'secondary', task, session
        )

        if not js_data1 or not js_data2:
            return False

        # 保存Team数据（两个数据源）
        self.save_team_data(team_data1, task, js_data1.id, session)
        self.save_team_data(team_data2, task, js_data2.id, session)

        # 解析两个阶段的比赛数据
        match_data1 = self.parse_match_data(js_data1.js_data_raw)
        match_data2 = self.parse_match_data(js_data2.js_data_raw)

        # 保存比赛数据（两个阶段）
        self.save_match_data(match_data1, task, js_data1.id, session)
        self.save_match_data(match_data2, task, js_data2.id, session)

        # 合并比赛数据（使用正确的阶段合并逻辑）
        merged_match_data = self.merge_match_data_by_stage(match_data1, match_data2)

        # 合并队伍数据
        merged_team_data = team_data1 + [t for t in team_data2 if t not in team_data1]

        # 分别计算两个阶段的三种积分榜
        calculated_standings1 = self.calculate_three_type_standings(match_data1, team_data1)
        calculated_standings2 = self.calculate_three_type_standings(match_data2, team_data2)

        # 合并两个阶段的积分榜
        calculated_standings = self.merge_standings_by_stage(calculated_standings1, calculated_standings2)

        # 保存结构化积分榜数据
        self.save_structured_standings(calculated_standings, task, session)

        return True

    def fetch_and_parse_link(self, url, link_type, task, session):
        """爬取并解析单个链接"""
        # 获取HTML页面
        html_content = self.fetch_html(url)
        if not html_content:
            return None, None, None

        # 提取JS数据 URL
        js_url, version = self.extract_js_data_url(html_content)
        if not js_url or not version:
            self.logger.error(f"无法从 HTML 中提取 JS 数据 URL: {url}")
            return None, None, None

        # 获取JS数据
        js_data = self.fetch_js_data(js_url, version)
        if not js_data:
            return None, None, None

        # 保存JS原始数据
        js_data_record = JsDataRaw(
            task_id=task.id,
            link_type=link_type,
            js_data_raw=js_data
        )
        session.add(js_data_record)
        session.flush()  # 获取ID

        # 解析球队数据
        team_data = self.parse_team_data(js_data)

        return js_data_record, team_data, None

    def fetch_html(self, url):
        """获取HTML页面内容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            self.logger.error(f"获取HTML失败 {url}: {e}")
            return None

    def extract_js_data_url(self, html_content):
        """从 HTML 中提取 JS 数据 URL 和版本号"""
        # 查找 JS 数据 URL 模式
        pattern = r'src="(/jsData/matchResult.*?version=([^"]+))"'
        match = re.search(pattern, html_content)
        if not match:
            return None, None

        js_path_with_query, version = match.group(1), match.group(2)
        js_path = js_path_with_query.split('?')[0]
        js_url = f"http://zq.titan007.com{js_path}"

        return js_url, version

    def fetch_js_data(self, js_url, version):
        """获取JS数据内容"""
        try:
            params = {"version": version}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
            }
            response = requests.get(js_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"获取JS数据失败 {js_url}: {e}")
            return None

    def parse_team_data(self, js_data):
        """解析球队数据（arrTeam）"""
        # 查找 arrTeam 数组
        pattern = r"var\s+arrTeam\s*=\s*(\[.*?\]);"
        match = re.search(pattern, js_data, re.DOTALL)
        if not match:
            self.logger.warning("未在 JS 数据中找到 arrTeam 定义")
            return []

        raw_teams = eval(match.group(1))
        teams = []
        for team in raw_teams:
            if len(team) >= 7:
                teams.append({
                    "team_code"   : team[0],
                    "home_name_cn": team[1],
                    "home_name_tw": team[2],
                    "home_name_en": team[3],
                    "unknown1"    : team[4],
                    "image_path"  : team[5],
                    "group_id"    : team[6],
                })
        return teams

    def parse_match_data(self, js_data):
        """解析JS数据中的比赛数据（jh["R_1"]等轮次数据）"""
        if not js_data:
            return {}

        match_data = {}
        # 查找 jh["R_轮次"] 数据模式
        pattern = r'jh\["R_(\d+)"\]\s*=\s*(.*?);'
        matches = re.findall(pattern, js_data, re.DOTALL)

        for round_num, array_str in matches:
            round_str = array_str.strip()
            if round_str == '[]':
                match_data[round_num] = []
                continue

            # 连续空值补齐：使用多次处理连续的逗号，直到没有变化
            fixed_str = round_str.replace(',,', ',None,')
            prev_str = ""
            while prev_str != fixed_str:
                prev_str = fixed_str
                fixed_str = fixed_str.replace(',,', ',None,')
            round_str = fixed_str
            
            # 头尾空位补齐
            round_str = re.sub(r'\[,', '[None,', round_str)
            round_str = re.sub(r',\]', ',None]', round_str)

            # 解析数组数据
            round_matches = eval(round_str)
            parsed_matches = []

            for match_array in round_matches:
                if len(match_array) >= 10:  # 确保数组有足够的元素
                    match_info = {
                        "match_id"      : match_array[0],  # 比赛ID
                        "league_id"     : match_array[1],  # 联赛ID
                        "round_num"     : int(round_num),  # 轮次
                        "match_time"    : match_array[3],  # 比赛时间
                        "home_team_code": str(match_array[4]) if match_array[4] is not None else None,  # 主队编码
                        "away_team_code": str(match_array[5]) if match_array[5] is not None else None,  # 客队编码
                        "full_score"    : match_array[6] if len(match_array) > 6 and match_array[6] is not None else None,  # 全场比分
                        "half_score"    : match_array[7] if len(match_array) > 7 and match_array[7] is not None else None,  # 半场比分
                        "home_team_rank": str(match_array[8]) if len(match_array) > 8 and match_array[8] is not None else None,  # 主队排名
                        "away_team_rank": str(match_array[9]) if len(match_array) > 9 and match_array[9] is not None else None,  # 客队排名
                    }
                    parsed_matches.append(match_info)

            match_data[round_num] = parsed_matches

        self.logger.info(f"成功解析比赛数据: {len(match_data)} 个轮次")
        return match_data

    def calculate_three_type_standings(self, match_data, team_data):
        """计算三种类型积分榜：total/home/away"""
        if not match_data or not team_data:
            return {}

        # 创建队伍编码到名称的映射
        code_to_name = {team['team_code']: team.get('home_name_cn', '') for team in team_data}
        all_team_codes = set(team['team_code'] for team in team_data)

        result = {}
        rounds = sorted(match_data.keys(), key=int)

        # 初始化累积统计
        cum_all = {code: {'games'    : 0, 'wins': 0, 'draws': 0, 'losses': 0,
                          'goals_for': 0, 'goals_against': 0} for code in all_team_codes}
        cum_home = {code: {'games'    : 0, 'wins': 0, 'draws': 0, 'losses': 0,
                           'goals_for': 0, 'goals_against': 0} for code in all_team_codes}
        cum_away = {code: {'games'    : 0, 'wins': 0, 'draws': 0, 'losses': 0,
                           'goals_for': 0, 'goals_against': 0} for code in all_team_codes}

        def ensure_team_exists(stats_dict, team_code):
            """确保队伍在统计字典中存在"""
            if team_code not in stats_dict:
                stats_dict[team_code] = {'games'    : 0, 'wins': 0, 'draws': 0, 'losses': 0,
                                         'goals_for': 0, 'goals_against': 0}

        def create_team_record(team_code, stats, team_names):
            """创建单个队伍的积分榜记录"""
            games = stats['games']
            wins = stats['wins']
            draws = stats['draws']
            losses = stats['losses']
            goals_for = stats['goals_for']
            goals_against = stats['goals_against']
            goal_diff = goals_for - goals_against
            points = wins * 3 + draws * 1

            return {
                'team_code'    : team_code,
                'team_name'    : team_names.get(team_code, str(team_code)),
                'games'        : games,
                'wins'         : wins,
                'draws'        : draws,
                'losses'       : losses,
                'goals_for'    : goals_for,
                'goals_against': goals_against,
                'goal_diff'    : goal_diff,
                'points'       : points
            }

        def build_and_rank_table(stats_dict, team_names):
            """构建并排序积分榜"""
            table = []
            for team_code in all_team_codes:
                if team_code in stats_dict:
                    record = create_team_record(team_code, stats_dict[team_code], team_names)
                    table.append(record)

            # 排序：积分 > 净胜球 > 进球数
            table.sort(key=lambda x: (-x['points'], -x['goal_diff'], -x['goals_for']))

            # 设置排名
            for i, record in enumerate(table):
                record['rank'] = i + 1

            return table

        # 按轮次累积计算
        for round_num in rounds:
            matches = match_data[round_num]

            for match in matches:
                score = match.get('full_score')
                if not score or '-' not in str(score):
                    continue

                try:
                    home_goals, away_goals = map(int, str(score).split('-'))
                except (ValueError, AttributeError):
                    continue

                home_code = int(match['home_team_code']) if match['home_team_code'].isdigit() else match['home_team_code']
                away_code = int(match['away_team_code']) if match['away_team_code'].isdigit() else match['away_team_code']

                # 确保队伍存在于统计中
                ensure_team_exists(cum_all, home_code)
                ensure_team_exists(cum_all, away_code)
                ensure_team_exists(cum_home, home_code)
                ensure_team_exists(cum_away, away_code)

                # 更新全场统计
                cum_all[home_code]['games'] += 1
                cum_all[away_code]['games'] += 1
                cum_all[home_code]['goals_for'] += home_goals
                cum_all[home_code]['goals_against'] += away_goals
                cum_all[away_code]['goals_for'] += away_goals
                cum_all[away_code]['goals_against'] += home_goals

                # 更新主场统计
                cum_home[home_code]['games'] += 1
                cum_home[home_code]['goals_for'] += home_goals
                cum_home[home_code]['goals_against'] += away_goals

                # 更新客场统计
                cum_away[away_code]['games'] += 1
                cum_away[away_code]['goals_for'] += away_goals
                cum_away[away_code]['goals_against'] += home_goals

                # 判断比赛结果
                if home_goals > away_goals:  # 主队胜
                    cum_all[home_code]['wins'] += 1
                    cum_all[away_code]['losses'] += 1
                    cum_home[home_code]['wins'] += 1
                    cum_away[away_code]['losses'] += 1
                elif home_goals < away_goals:  # 客队胜
                    cum_all[home_code]['losses'] += 1
                    cum_all[away_code]['wins'] += 1
                    cum_home[home_code]['losses'] += 1
                    cum_away[away_code]['wins'] += 1
                else:  # 平局
                    cum_all[home_code]['draws'] += 1
                    cum_all[away_code]['draws'] += 1
                    cum_home[home_code]['draws'] += 1
                    cum_away[away_code]['draws'] += 1

            # 生成该轮次的三种积分榜
            result[round_num] = {
                'total': build_and_rank_table(cum_all, code_to_name),
                'home' : build_and_rank_table(cum_home, code_to_name),
                'away' : build_and_rank_table(cum_away, code_to_name)
            }

        self.logger.info(f"成功计算积分榜: {len(result)} 个轮次，每轮次3种类型")
        return result

    def save_team_data(self, team_data, task, js_data_id, session):
        """保存球队数据，采用覆盖式更新"""
        updated_count = 0
        created_count = 0

        for team_info in team_data:
            # 检查是否已存在（task_id + team_code 复合主键）
            existing_team = session.query(Team).filter(
                Team.task_id == task.id,
                Team.team_code == team_info["team_code"]
            ).first()

            if existing_team:
                # 覆盖式更新现有记录
                existing_team.js_data_id = js_data_id
                existing_team.home_name_cn = team_info.get("home_name_cn")
                existing_team.home_name_tw = team_info.get("home_name_tw")
                existing_team.home_name_en = team_info.get("home_name_en")
                existing_team.image_path = team_info.get("image_path")
                existing_team.group_id = team_info.get("group_id")
                existing_team.unknown1 = team_info.get("unknown1")
                updated_count += 1
            else:
                # 新建记录
                team = Team(
                    task_id=task.id,
                    team_code=team_info["team_code"],
                    js_data_id=js_data_id,
                    home_name_cn=team_info.get("home_name_cn"),
                    home_name_tw=team_info.get("home_name_tw"),
                    home_name_en=team_info.get("home_name_en"),
                    image_path=team_info.get("image_path"),
                    group_id=team_info.get("group_id"),
                    unknown1=team_info.get("unknown1")
                )
                session.add(team)
                created_count += 1

        self.logger.info(f"球队数据处理完成: 新建 {created_count} 个，更新 {updated_count} 个")

    def save_match_data(self, match_data, task, js_data_id, session):
        """保存比赛数据到Match表"""
        if not match_data:
            return

        saved_count = 0
        for round_num, matches in match_data.items():
            for match_info in matches:
                # 检查是否已存在该比赛记录
                existing_match = session.query(Match).filter(
                    Match.match_id == match_info['match_id']
                ).first()

                if not existing_match:
                    match_record = Match(
                        match_id=match_info['match_id'],
                        task_id=task.id,
                        js_data_id=js_data_id,
                        league_id=match_info['league_id'],
                        round_num=match_info['round_num'],
                        match_time=str(match_info['match_time']) if match_info['match_time'] else None,
                        home_team_code=str(match_info['home_team_code']),
                        away_team_code=str(match_info['away_team_code']),
                        full_score=str(match_info['full_score']) if match_info['full_score'] else None,
                        half_score=str(match_info['half_score']) if match_info['half_score'] else None,
                        home_team_rank=match_info['home_team_rank'],
                        away_team_rank=match_info['away_team_rank']
                    )
                    session.add(match_record)
                    saved_count += 1

        self.logger.info(f"保存了 {saved_count} 场比赛数据")

    def save_structured_standings(self, standings_data, task, session):
        """保存结构化积分榜数据到Standings表"""
        if not standings_data:
            return

        # 删除该任务的旧积分榜数据
        session.query(Standings).filter(Standings.task_id == task.id).delete()

        saved_count = 0
        for round_num, round_standings in standings_data.items():
            for standings_category, team_records in round_standings.items():
                for team_record in team_records:
                    # 为常规任务设置division_type为default
                    division_type = 'default'

                    standings_record = Standings(
                        task_id=task.id,
                        standings_category=standings_category,  # total/home/away
                        division_type=division_type,  # default/east/west
                        team_code=str(team_record['team_code']),
                        round_num=round_num,  # 截止轮次
                        rank=team_record['rank'],
                        games=team_record['games'],
                        wins=team_record['wins'],
                        draws=team_record['draws'],
                        losses=team_record['losses'],
                        goals_for=team_record['goals_for'],
                        goals_against=team_record['goals_against'],
                        goal_diff=team_record['goal_diff'],
                        points=team_record['points']
                    )
                    session.add(standings_record)
                    saved_count += 1

        self.logger.info(f"保存了 {saved_count} 条结构化积分榜记录")

    def save_east_west_structured_standings(self, standings_data, team_data, task, session):
        """保存东西拆分的结构化积分榜数据"""
        if not standings_data or not team_data:
            return

        # 删除该任务的旧积分榜数据
        session.query(Standings).filter(Standings.task_id == task.id).delete()

        # 按group_id分组队伍
        east_teams = set()
        west_teams = set()

        for team in team_data:
            group_id = team.get("group_id", 0)
            team_code = str(team['team_code'])
            # 奇数group_id为东部，偶数为西部
            if group_id % 2 == 1:
                east_teams.add(team_code)
            else:
                west_teams.add(team_code)

        saved_count = 0
        for round_num, round_standings in standings_data.items():
                for standings_category, team_records in round_standings.items():
                    for team_record in team_records:
                        team_code = str(team_record['team_code'])

                        # 确定division_type
                        if team_code in east_teams:
                            division_type = 'east'
                        elif team_code in west_teams:
                            division_type = 'west'
                        else:
                            division_type = 'default'  # 保险起见

                        standings_record = Standings(
                            task_id=task.id,
                            standings_category=standings_category,  # total/home/away
                            division_type=division_type,  # east/west
                            team_code=team_code,
                            round_num=round_num,  # 截止轮次
                            rank=team_record['rank'],
                            games=team_record['games'],
                            wins=team_record['wins'],
                            draws=team_record['draws'],
                            losses=team_record['losses'],
                            goals_for=team_record['goals_for'],
                            goals_against=team_record['goals_against'],
                            goal_diff=team_record['goal_diff'],
                            points=team_record['points']
                        )
                        session.add(standings_record)
                        saved_count += 1

        self.logger.info(f"保存了 {saved_count} 条东西拆分结构化积分榜记录")

    def merge_round_records_by_team(self, first_records, second_records):
        """根据球队名称合并两个阶段的积分榜记录"""
        if not first_records or not second_records:
            return first_records or second_records or []

        # 创建球队名称映射
        first_team_map = {}
        second_team_map = {}

        # 构建第一阶段和第二阶段的team_name映射
        for record in first_records:
            team_name = record.get('team_name', '')
            if team_name:
                first_team_map[team_name] = record

        for record in second_records:
            team_name = record.get('team_name', '')
            if team_name:
                second_team_map[team_name] = record

        merged_records = []
        processed_teams = set()

        # 合并有对应关系的球队数据
        for team_name, first_record in first_team_map.items():
            if team_name in second_team_map:
                second_record = second_team_map[team_name]

                # 累加统计数据
                merged_record = {
                    'team_code'    : first_record.get('team_code', ''),
                    'team_name'    : team_name,
                    'games'        : first_record.get('games', 0) + second_record.get('games', 0),
                    'wins'         : first_record.get('wins', 0) + second_record.get('wins', 0),
                    'draws'        : first_record.get('draws', 0) + second_record.get('draws', 0),
                    'losses'       : first_record.get('losses', 0) + second_record.get('losses', 0),
                    'goals_for'    : first_record.get('goals_for', 0) + second_record.get('goals_for', 0),
                    'goals_against': first_record.get('goals_against', 0) + second_record.get('goals_against', 0),
                }

                # 计算衍生字段
                merged_record['goal_diff'] = merged_record['goals_for'] - merged_record['goals_against']
                merged_record['points'] = merged_record['wins'] * 3 + merged_record['draws'] * 1

                merged_records.append(merged_record)
                processed_teams.add(team_name)

        # 添加只在第一阶段或第二阶段存在的球队数据
        for team_name, record in first_team_map.items():
            if team_name not in processed_teams:
                merged_records.append(record)
                processed_teams.add(team_name)

        for team_name, record in second_team_map.items():
            if team_name not in processed_teams:
                merged_records.append(record)

        # 根据积分重新排序并设置排名
        merged_records.sort(key=lambda x: (-x['points'], -x['goal_diff'], -x['goals_for']))

        for i, record in enumerate(merged_records):
            record['rank'] = i + 1

        return merged_records

    def calculate_standings_increment(self, prev_records, current_records):
        """计算两轮之间的增量数据"""
        if not prev_records or not current_records:
            return current_records or []

        # 创建上一轮的队伍数据映射
        prev_map = {record.get('team_name', ''): record for record in prev_records}
        
        increment_records = []
        for current_record in current_records:
            team_name = current_record.get('team_name', '')
            if team_name in prev_map:
                prev_record = prev_map[team_name]
                # 计算增量
                increment_record = {
                    'team_code': current_record.get('team_code', ''),
                    'team_name': team_name,
                    'games': current_record.get('games', 0) - prev_record.get('games', 0),
                    'wins': current_record.get('wins', 0) - prev_record.get('wins', 0),
                    'draws': current_record.get('draws', 0) - prev_record.get('draws', 0),
                    'losses': current_record.get('losses', 0) - prev_record.get('losses', 0),
                    'goals_for': current_record.get('goals_for', 0) - prev_record.get('goals_for', 0),
                    'goals_against': current_record.get('goals_against', 0) - prev_record.get('goals_against', 0),
                }
                # 计算衍生字段
                increment_record['goal_diff'] = increment_record['goals_for'] - increment_record['goals_against']
                increment_record['points'] = increment_record['wins'] * 3 + increment_record['draws'] * 1
                increment_records.append(increment_record)
            else:
                # 新队伍，直接使用当前记录
                increment_records.append(current_record.copy())
        
        return increment_records

    def merge_standings_by_stage(self, first_standings, second_standings):
        """合并两个阶段的积分榜数据"""
        if not first_standings or not second_standings:
            return first_standings or second_standings or {}

        # 步骤1：保留第一阶段的所有轮次数据
        merged_standings = dict(first_standings)

        # 步骤2：获取第一阶段最大轮次号和最后一轮数据
        first_rounds = sorted(first_standings.keys(), key=int)
        max_first_round = int(first_rounds[-1]) if first_rounds else 0
        last_first_standings = first_standings[first_rounds[-1]] if first_rounds else {}

        # 步骤3：处理第二阶段数据，进行轮次偏移和累积计算
        second_rounds = sorted(second_standings.keys(), key=int)
        
        # 用于累积计算的基础数据（从第一阶段最后一轮开始）
        cumulative_base = {}
        for table_type, records in last_first_standings.items():
            cumulative_base[table_type] = [record.copy() for record in records]

        for i, round_num in enumerate(second_rounds):
            # 计算新的轮次号（偏移）
            new_round_num = str(max_first_round + int(round_num))
            second_tables = second_standings[round_num]
            
            merged_tables = {}
            
            # 对每个表格类型(total, home, away)进行处理
            for table_type, second_table_records in second_tables.items():
                if i == 0:
                    # 第二阶段第一轮：基于第一阶段最后一轮进行累积
                    base_records = cumulative_base.get(table_type, [])
                    merged_records = self.merge_round_records_by_team(base_records, second_table_records)
                else:
                    # 第二阶段后续轮次：基于上一轮结果进行累积
                    prev_round_num = str(max_first_round + int(second_rounds[i-1]))
                    if prev_round_num in merged_standings:
                        base_records = merged_standings[prev_round_num].get(table_type, [])
                        # 计算当前轮次的增量数据
                        prev_second_round = second_rounds[i-1]
                        current_increment = self.calculate_standings_increment(
                            second_standings[prev_second_round].get(table_type, []),
                            second_table_records
                        )
                        merged_records = self.merge_round_records_by_team(base_records, current_increment)
                    else:
                        merged_records = second_table_records
                
                if merged_records:
                    merged_tables[table_type] = merged_records

            if merged_tables:
                merged_standings[new_round_num] = merged_tables

        return merged_standings

    def merge_match_data_by_stage(self, first_match_data, second_match_data):
        """合并两个阶段的比赛数据"""
        if not first_match_data or not second_match_data:
            return first_match_data or second_match_data or {}

        # 简单合并：第一阶段 + 第二阶段（轮次不重复）
        merged_data = dict(first_match_data)

        # 对第二阶段的轮次进行偏移，避免与第一阶段冲突
        first_rounds = [int(r) for r in first_match_data.keys() if r.isdigit()]
        max_first_round = max(first_rounds) if first_rounds else 0

        for round_num, matches in second_match_data.items():
            if round_num.isdigit():
                # 第二阶段轮次从第一阶段最大轮次+1开始
                new_round_num = str(max_first_round + int(round_num))
                # 更新每场比赛的round_num字段
                updated_matches = []
                for match in matches:
                    updated_match = match.copy()
                    updated_match['round_num'] = int(new_round_num)
                    updated_matches.append(updated_match)
                merged_data[new_round_num] = updated_matches
            else:
                merged_data[round_num] = matches

        self.logger.info(f"合并比赛数据完成：第一阶段{len(first_match_data)}轮，第二阶段{len(second_match_data)}轮，合并后{len(merged_data)}轮")
        return merged_data

    def add_log(self, message, level="INFO"):
        """添加日志信息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)

        # 设置颜色
        if level == "ERROR":
            start_line = self.log_text.index(tk.END + "-2l linestart")
            end_line = self.log_text.index(tk.END + "-1l lineend")
            self.log_text.tag_add("error", start_line, end_line)
            self.log_text.tag_config("error", foreground="red")
        elif level == "SUCCESS":
            start_line = self.log_text.index(tk.END + "-2l linestart")
            end_line = self.log_text.index(tk.END + "-1l lineend")
            self.log_text.tag_add("success", start_line, end_line)
            self.log_text.tag_config("success", foreground="green")

        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def save_log(self):
        """保存日志到文件"""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="保存爬取日志"
        )

        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.show_message("成功", f"日志已保存到: {filename}", "info")
