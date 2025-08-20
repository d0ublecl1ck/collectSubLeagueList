"""
基础页面类，为所有页面提供通用功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from loguru import logger

from models import DatabaseManager


class BasePage:
    """基础页面类，提供通用的界面组件和数据库连接"""
    
    def __init__(self, parent: tk.Widget, db_manager: Optional[DatabaseManager] = None):
        """
        初始化基础页面
        
        Args:
            parent: 父级容器
            db_manager: 数据库管理器实例
        """
        self.parent = parent
        self.db_manager = db_manager or DatabaseManager('sqlite:///data.db')
        
        # 创建主框架
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 初始化日志
        self.logger = logger
        
        # 设置页面
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面，子类需要重写此方法"""
        # 默认显示页面标题
        title_label = ttk.Label(
            self.frame, 
            text=self.__class__.__name__.replace('Page', ' 页面'),
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=20)
        
        # 占位内容
        placeholder_label = ttk.Label(
            self.frame,
            text="页面内容开发中...",
            font=('Arial', 12)
        )
        placeholder_label.pack(pady=50)
        
    def show_message(self, title: str, message: str, msg_type: str = "info"):
        """显示消息框"""
        if msg_type == "info":
            messagebox.showinfo(title, message)
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
        elif msg_type == "error":
            messagebox.showerror(title, message)
            
    def log_action(self, action: str, details: str = ""):
        """记录用户操作日志"""
        self.logger.info(f"页面操作: {action} - {details}")
        
    def get_db_session(self):
        """获取数据库会话"""
        return self.db_manager.get_session()
        
    def create_labeled_entry(self, parent: tk.Widget, label_text: str, row: int, 
                           column: int = 0, width: int = 20, **kwargs) -> ttk.Entry:
        """创建带标签的输入框"""
        ttk.Label(parent, text=label_text).grid(
            row=row, column=column, sticky='e', padx=5, pady=5
        )
        entry = ttk.Entry(parent, width=width, **kwargs)
        entry.grid(row=row, column=column+1, sticky='w', padx=5, pady=5)
        return entry
        
    def create_labeled_combobox(self, parent: tk.Widget, label_text: str, 
                              values: list, row: int, column: int = 0, 
                              width: int = 18, **kwargs) -> ttk.Combobox:
        """创建带标签的下拉框"""
        ttk.Label(parent, text=label_text).grid(
            row=row, column=column, sticky='e', padx=5, pady=5
        )
        combobox = ttk.Combobox(parent, values=values, width=width, **kwargs)
        combobox.grid(row=row, column=column+1, sticky='w', padx=5, pady=5)
        return combobox