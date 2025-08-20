# -*- coding: utf-8 -*-
"""
数据爬取页面 - 提供爬虫执行控制和进度监控界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime

from .base_page import BasePage
from models import Task


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
                
                # 模拟爬取过程
                crawl_success = self.simulate_crawl(task_id)
                
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
            
    def simulate_crawl(self, task_id):
        """模拟爬取过程"""
        try:
            # 模拟网络请求延迟
            time.sleep(0.5 + (hash(str(task_id)) % 20) / 10)  # 0.5-2.5秒随机延迟
            
            # 模拟成功率 (80%)
            import random
            success = random.random() > 0.2
            
            if success:
                # 更新数据库中的爬取时间
                with self.get_db_session() as session:
                    task = session.query(Task).filter(Task.id == task_id).first()
                    if task:
                        task.last_crawl_time = datetime.now()
                        session.commit()
                        
            return success
            
        except Exception as e:
            self.logger.error(f"模拟爬取失败: {e}")
            return False
            
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