# -*- coding: utf-8 -*-
"""
足球联赛数据爬虫系统 - 主应用程序
提供图形化界面用于任务管理、数据爬取和数据管理
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from loguru import logger

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import DatabaseManager
from pages import (
    InputPage, 
    InputManagementPage, 
    DataCrawlPage, 
    DataManagementPage
)


class FootballDataApp:
    """足球联赛数据管理系统主应用"""
    
    def __init__(self):
        """初始化应用程序"""
        self.setup_logging()
        self.setup_database()
        self.setup_ui()
        
    def setup_logging(self):
        """配置日志系统"""
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            encoding="utf-8"
        )
        logger.info("应用程序启动")
        
    def setup_database(self):
        """初始化数据库"""
        try:
            self.db_manager = DatabaseManager('sqlite:///data.db')
            self.db_manager.create_tables()
            logger.info("数据库初始化成功")
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            messagebox.showerror("错误", f"数据库初始化失败：{str(e)}")
            sys.exit(1)
            
    def setup_ui(self):
        """设置用户界面"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("足球联赛数据管理系统 v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 设置应用图标（如果有的话）
        try:
            # self.root.iconbitmap("assets/icon.ico")
            pass
        except:
            pass
            
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')  # 使用现代主题
        
        # 创建主菜单
        self.create_menu()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建标签页容器
        self.create_notebook()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        logger.info("用户界面初始化完成")
        
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建任务", command=self.new_task)
        file_menu.add_separator()
        file_menu.add_command(label="导入数据", command=self.import_data)
        file_menu.add_command(label="导出数据", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="数据库管理", command=self.database_management)
        tools_menu.add_command(label="清理日志", command=self.clean_logs)
        tools_menu.add_separator()
        tools_menu.add_command(label="系统设置", command=self.system_settings)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 状态信息
        self.status_label = ttk.Label(
            self.status_bar, 
            text="就绪", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # 数据库状态
        self.db_status_label = ttk.Label(
            self.status_bar, 
            text="数据库: 已连接", 
            relief=tk.SUNKEN
        )
        self.db_status_label.pack(side=tk.RIGHT, padx=(0, 5))
        
    def create_notebook(self):
        """创建标签页容器和各个页面"""
        # 创建 Notebook 容器
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        try:
            # 创建各个页面
            self.input_page = InputPage(self.notebook, self.db_manager)
            self.input_management_page = InputManagementPage(self.notebook, self.db_manager)
            self.data_crawl_page = DataCrawlPage(self.notebook, self.db_manager)
            self.data_management_page = DataManagementPage(self.notebook, self.db_manager)
            
            # 添加标签页
            self.notebook.add(self.input_page.frame, text="输入", padding=5)
            self.notebook.add(self.input_management_page.frame, text="输入管理", padding=5)
            self.notebook.add(self.data_crawl_page.frame, text="数据爬取", padding=5)
            self.notebook.add(self.data_management_page.frame, text="数据管理", padding=5)
            
            # 绑定标签页切换事件
            self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
            
            logger.info("所有页面创建成功")
            
        except Exception as e:
            logger.error(f"页面创建失败: {e}")
            messagebox.showerror("错误", f"页面初始化失败：{str(e)}")
            
    def on_tab_changed(self, event):
        """标签页切换事件处理"""
        selected_tab = self.notebook.select()
        tab_text = self.notebook.tab(selected_tab, "text")
        self.update_status(f"当前页面: {tab_text}")
        logger.debug(f"切换到页面: {tab_text}")
        
    def update_status(self, message):
        """更新状态栏信息"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
        
    def new_task(self):
        """新建任务"""
        # 切换到输入页面
        self.notebook.select(0)
        self.update_status("新建任务")
        
    def import_data(self):
        """导入数据"""
        # 切换到数据管理页面
        self.notebook.select(3)
        self.update_status("导入数据")
        
    def export_data(self):
        """导出数据"""
        # 切换到数据管理页面
        self.notebook.select(3)
        self.update_status("导出数据")
        
    def database_management(self):
        """数据库管理"""
        try:
            with self.db_manager.get_session() as session:
                from models import Task, Team
                
                task_count = session.query(Task).count()
                team_count = session.query(Team).count()
                
                info_text = f"数据库统计信息:\\n\\n任务数量: {task_count}\\n队伍数量: {team_count}\\n数据库文件: data.db\\n\\n数据库状态: 正常"
                
                messagebox.showinfo("数据库管理", info_text)
                
        except Exception as e:
            logger.error(f"数据库管理操作失败: {e}")
            messagebox.showerror("错误", f"数据库操作失败：{str(e)}")
            
    def clean_logs(self):
        """清理日志文件"""
        result = messagebox.askyesno("确认清理", "确定要清理所有日志文件吗？")
        if result:
            try:
                import glob
                log_files = glob.glob("logs/*.log")
                for log_file in log_files:
                    os.remove(log_file)
                    
                messagebox.showinfo("成功", f"已清理 {len(log_files)} 个日志文件")
                logger.info(f"清理了 {len(log_files)} 个日志文件")
                
            except Exception as e:
                logger.error(f"清理日志失败: {e}")
                messagebox.showerror("错误", f"清理日志失败：{str(e)}")
                
    def system_settings(self):
        """系统设置"""
        messagebox.showinfo("系统设置", "系统设置功能开发中...")
        
    def show_help(self):
        """显示帮助信息"""
        help_text = "足球联赛数据管理系统 使用说明:\\n\\n1. 输入页面: 录入新的联赛任务信息\\n2. 输入管理: 查看、编辑和删除已有任务\\n3. 数据爬取: 执行爬虫任务，获取队伍数据\\n4. 数据管理: 查看和管理队伍数据\\n\\n更多帮助信息请参考项目文档。"
        
        messagebox.showinfo("使用说明", help_text)
        
    def show_about(self):
        """显示关于信息"""
        about_text = "足球联赛数据管理系统 v1.0\\n\\n一个用于管理足球联赛数据的爬虫系统\\n\\n技术栈:\\n- Python 3.8.10\\n- tkinter (GUI)\\n- SQLAlchemy (ORM)\\n- loguru (日志)\\n\\n开发: d0ublecl1ck\\n项目: collectSubLeagueList"
        
        messagebox.showinfo("关于", about_text)
        
    def on_closing(self):
        """窗口关闭事件处理"""
        result = messagebox.askyesno("确认退出", "确定要退出应用程序吗？")
        if result:
            logger.info("应用程序正常退出")
            self.root.destroy()
            
    def run(self):
        """运行应用程序"""
        try:
            self.update_status("应用程序已启动")
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("用户中断应用程序")
        except Exception as e:
            logger.error(f"应用程序运行错误: {e}")
            messagebox.showerror("错误", f"应用程序错误：{str(e)}")
        finally:
            logger.info("应用程序结束")


def main():
    """主函数"""
    try:
        # 创建日志目录
        os.makedirs("logs", exist_ok=True)
        
        # 创建并运行应用
        app = FootballDataApp()
        app.run()
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()