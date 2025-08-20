# -*- coding: utf-8 -*-
"""
数据爬取页面 - 提供爬虫执行控制和进度监控界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from .base_page import BasePage
from models import Task, JsDataRaw, Standings, Team


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
        self.concurrent_var = tk.IntVar(value=3)
        concurrent_spin = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.concurrent_var, width=10)
        concurrent_spin.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        ttk.Label(settings_frame, text="延迟(秒):").grid(row=0, column=2, sticky='e', padx=(0, 5))
        self.delay_var = tk.DoubleVar(value=1.0)
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
        try:
            self.task_listbox.delete(0, tk.END)
            
            with self.get_db_session() as session:
                tasks = session.query(Task).order_by(Task.created_at.desc()).all()
                
                for task in tasks:
                    display_text = f"[{task.id}] {task.league} ({task.year}) - {task.country}"
                    self.task_listbox.insert(tk.END, display_text)
                    
            self.add_log(f"加载了 {len(tasks)} 个任务")
            
        except Exception as e:
            self.logger.error(f"刷新任务列表失败: {e}")
            self.add_log(f"刷新任务列表失败: {str(e)}", "ERROR")
            
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
                self.stats_label.config(text=f"成功: {success_count} | 失败: {failed_count} | 总计: {i+1}/{total_tasks}")
                self.time_label.config(text=f"用时: {time_str}")
                
                # 延迟
                time.sleep(self.delay_var.get())
                
        except Exception as e:
            self.add_log(f"爬取过程中出现错误: {str(e)}", "ERROR")
            
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
        try:
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
                
        except Exception as e:
            self.logger.error(f"爬取任务 {task_id} 发生异常: {e}")
            return False
    
    def crawl_regular_task(self, task, session):
        """爬取常规任务"""
        try:
            if not task.link:
                self.logger.error("常规任务缺少主链接")
                return False
                
            # 爬取和解析数据
            js_data_record, team_data, standings_data = self.fetch_and_parse_link(
                task.link, 'primary', task, session
            )
            
            if not js_data_record:
                return False
                
            # 保存Team数据
            self.save_team_data(team_data, task, js_data_record.id, session)
            
            # 保存积分榜数据
            self.save_standings_data(standings_data, 'default', task, session)
            
            return True
            
        except Exception as e:
            self.logger.error(f"常规任务爬取失败: {e}")
            return False
    
    def crawl_east_west_split_task(self, task, session):
        """爬取东西拆分任务"""
        try:
            if not task.link:
                self.logger.error("东西拆分任务缺少主链接")
                return False
                
            # 爬取和解析数据
            js_data_record, team_data, standings_data = self.fetch_and_parse_link(
                task.link, 'primary', task, session
            )
            
            if not js_data_record:
                return False
                
            # 保存Team数据
            self.save_team_data(team_data, task, js_data_record.id, session)
            
            # 按group_id拆分积分榜
            east_standings, west_standings = self.split_standings_by_group(standings_data, team_data)
            
            # 保存东西部积分榜
            self.save_standings_data(east_standings, 'east', task, session)
            self.save_standings_data(west_standings, 'west', task, session)
            
            return True
            
        except Exception as e:
            self.logger.error(f"东西拆分任务爬取失败: {e}")
            return False
    
    def crawl_merge_task(self, task, session):
        """爬取合并类型任务"""
        try:
            if not task.link or not task.link_second:
                self.logger.error(f"合并任务缺少链接: link={task.link}, link_second={task.link_second}")
                return False
                
            # 爬取第一个链接
            js_data1, team_data1, standings_data1 = self.fetch_and_parse_link(
                task.link, 'primary', task, session
            )
            
            # 爬取第二个链接
            js_data2, team_data2, standings_data2 = self.fetch_and_parse_link(
                task.link_second, 'secondary', task, session
            )
            
            if not js_data1 or not js_data2:
                return False
                
            # 保存Team数据（两个数据源）
            self.save_team_data(team_data1, task, js_data1.id, session)
            self.save_team_data(team_data2, task, js_data2.id, session)
            
            # 合并积分榜数据
            merged_standings = self.merge_standings_data(standings_data1, standings_data2)
            
            # 保存合并后的积分榜
            self.save_standings_data(merged_standings, 'default', task, session)
            
            return True
            
        except Exception as e:
            self.logger.error(f"合并任务爬取失败: {e}")
            return False
    
    def fetch_and_parse_link(self, url, link_type, task, session):
        """爬取并解析单个链接"""
        try:
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
            
            # 解析积分榜数据（这里简化处理，实际需要复杂的计算）
            standings_data = self.calculate_standings(js_data, team_data)
            
            return js_data_record, team_data, standings_data
            
        except Exception as e:
            self.logger.error(f"爬取解析链接失败 {url}: {e}")
            return None, None, None
    
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
        try:
            # 查找 JS 数据 URL 模式
            pattern = r'src="(/jsData/matchResult.*?version=([^"]+))"'
            match = re.search(pattern, html_content)
            if not match:
                return None, None
                
            js_path_with_query, version = match.group(1), match.group(2)
            js_path = js_path_with_query.split('?')[0]
            js_url = f"http://zq.titan007.com{js_path}"
            
            return js_url, version
        except Exception as e:
            self.logger.error(f"提取JS数据URL失败: {e}")
            return None, None
    
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
        try:
            # 查找 arrTeam 数组
            pattern = r"var\s+arrTeam\s*=\s*(\[.*?\]);"
            match = re.search(pattern, js_data, re.DOTALL)
            if not match:
                self.logger.warning("未在 JS 数据中找到 arrTeam 定义")
                return []
                
            try:
                raw_teams = eval(match.group(1))
                teams = []
                for team in raw_teams:
                    if len(team) >= 7:
                        teams.append({
                            "team_code": team[0],
                            "home_name_cn": team[1],
                            "home_name_tw": team[2],
                            "home_name_en": team[3],
                            "unknown1": team[4],
                            "image_path": team[5],
                            "group_id": team[6],
                        })
                return teams
            except Exception as e:
                self.logger.error(f"解析 arrTeam 数组失败: {e}")
                return []
                
        except Exception as e:
            self.logger.error(f"解析球队数据失败: {e}")
            return []
    
    def calculate_standings(self, js_data, team_data):
        """计算积分榜数据（简化处理）"""
        try:
            # 这里仅做简化处理，实际需要解析轮次数据并计算积分榜
            standings = []
            for i, team in enumerate(team_data):
                standings.append({
                    "rank": i + 1,
                    "team_name": team["home_name_cn"],
                    "games": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "goal_diff": 0,
                    "points": 0
                })
            return standings
        except Exception as e:
            self.logger.error(f"计算积分榜失败: {e}")
            return []
    
    def save_team_data(self, team_data, task, js_data_id, session):
        """保存球队数据"""
        try:
            for team_info in team_data:
                # 检查是否已存在
                existing_team = session.query(Team).filter(
                    Team.task_id == task.id,
                    Team.team_code == team_info["team_code"],
                    Team.js_data_id == js_data_id
                ).first()
                
                if not existing_team:
                    team = Team(
                        task_id=task.id,
                        js_data_id=js_data_id,
                        team_code=team_info["team_code"],
                        home_name_cn=team_info.get("home_name_cn"),
                        home_name_tw=team_info.get("home_name_tw"),
                        home_name_en=team_info.get("home_name_en"),
                        image_path=team_info.get("image_path"),
                        league_id=0,  # 默认值
                        group_id=team_info.get("group_id"),
                        unknown1=team_info.get("unknown1")
                    )
                    session.add(team)
                    
            self.logger.info(f"保存了 {len(team_data)} 个球队数据")
        except Exception as e:
            self.logger.error(f"保存球队数据失败: {e}")
    
    def save_standings_data(self, standings_data, standings_type, task, session):
        """保存积分榜数据"""
        try:
            # 删除旧的同类型积分榜
            session.query(Standings).filter(
                Standings.task_id == task.id,
                Standings.standings_type == standings_type
            ).delete()
            
            # 保存新积分榜
            standings = Standings(
                task_id=task.id,
                standings_type=standings_type,
                standings_data=json.dumps(standings_data, ensure_ascii=False)
            )
            session.add(standings)
            
            self.logger.info(f"保存了 {standings_type} 积分榜数据")
        except Exception as e:
            self.logger.error(f"保存积分榜数据失败: {e}")
    
    def split_standings_by_group(self, standings_data, team_data):
        """按组别拆分积分榜（东西部）"""
        try:
            # 按group_id分组球队
            east_teams = []
            west_teams = []
            
            for team in team_data:
                group_id = team.get("group_id", 0)
                # 简化逻辑：奇数group_id为东部，偶数为西部
                if group_id % 2 == 1:
                    east_teams.append(team["home_name_cn"])
                else:
                    west_teams.append(team["home_name_cn"])
            
            # 拆分积分榜
            east_standings = [s for s in standings_data if s["team_name"] in east_teams]
            west_standings = [s for s in standings_data if s["team_name"] in west_teams]
            
            # 重新排序和设置排名
            for i, standing in enumerate(east_standings):
                standing["rank"] = i + 1
            for i, standing in enumerate(west_standings):
                standing["rank"] = i + 1
                
            return east_standings, west_standings
            
        except Exception as e:
            self.logger.error(f"拆分积分榜失败: {e}")
            return [], []
    
    def merge_standings_data(self, standings_data1, standings_data2):
        """合并两个积分榜数据（简化处理）"""
        try:
            # 简化处理：直接合并两个列表
            merged = standings_data1 + standings_data2
            
            # 按球队名称合并重复数据（这里需要复杂的合并逻辑）
            team_stats = {}
            for standing in merged:
                team_name = standing["team_name"]
                if team_name not in team_stats:
                    team_stats[team_name] = standing.copy()
                else:
                    # 简单的数据加和
                    team_stats[team_name]["games"] += standing["games"]
                    team_stats[team_name]["wins"] += standing["wins"]
                    team_stats[team_name]["draws"] += standing["draws"]
                    team_stats[team_name]["losses"] += standing["losses"]
                    team_stats[team_name]["goals_for"] += standing["goals_for"]
                    team_stats[team_name]["goals_against"] += standing["goals_against"]
                    team_stats[team_name]["points"] += standing["points"]
                    
            # 转换为列表并排序
            result = list(team_stats.values())
            result.sort(key=lambda x: (-x["points"], -x["goal_diff"], -x["goals_for"]))
            
            # 重新设置排名
            for i, standing in enumerate(result):
                standing["rank"] = i + 1
                
            return result
            
        except Exception as e:
            self.logger.error(f"合并积分榜数据失败: {e}")
            return standings_data1  # 返回第一个作为备选
            
    def add_log(self, message, level="INFO"):
        """添加日志信息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\\n"
        
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
        try:
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
                
        except Exception as e:
            self.show_message("错误", f"保存日志失败: {str(e)}", "error")