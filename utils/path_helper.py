# -*- coding: utf-8 -*-
"""
路径帮助工具 - 处理打包后的路径问题
"""

import os
import sys


def get_executable_dir():
    """
    获取可执行文件所在目录
    
    在开发环境中返回脚本所在目录
    在打包环境中返回exe文件所在目录
    
    Returns:
        str: 可执行文件所在目录的绝对路径
    """
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_database_path(db_filename='data.db'):
    """
    获取数据库文件的完整路径
    
    Args:
        db_filename: 数据库文件名，默认为 'data.db'
        
    Returns:
        str: 数据库文件的完整路径
    """
    executable_dir = get_executable_dir()
    return os.path.join(executable_dir, db_filename)


def get_database_url(db_filename='data.db'):
    """
    获取SQLAlchemy数据库连接URL
    
    Args:
        db_filename: 数据库文件名，默认为 'data.db'
        
    Returns:
        str: SQLite数据库连接URL
    """
    db_path = get_database_path(db_filename)
    # 将Windows路径分隔符转换为URL格式，避免路径问题
    db_url = db_path.replace('\\', '/')
    return f'sqlite:///{db_url}'