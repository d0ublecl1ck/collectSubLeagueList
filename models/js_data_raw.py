# -*- coding: utf-8 -*-
"""
JsDataRaw 模型定义 - JS原始数据表
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Index
from sqlalchemy.orm import relationship
from loguru import logger

from .base import Base


class JsDataRaw(Base):
    """JS原始数据表 - 存储从网页爬取的原始JavaScript数据"""
    __tablename__ = 'js_data_raw'
    
    # 主键字段
    id = Column(Integer, primary_key=True, autoincrement=True, comment='JS数据唯一标识ID')
    
    # 关联字段
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='关联的任务ID')
    
    # 数据源信息
    link_type = Column(String(20), nullable=False, comment='链接类型: primary/secondary')
    
    # 原始数据
    js_data_raw = Column(Text, nullable=False, comment='原始JS数据内容')
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment='创建时间')
    
    # 关联关系
    task = relationship("Task", back_populates="js_data_records")
    teams = relationship("Team", back_populates="js_data_source")
    
    # 索引优化
    __table_args__ = (
        Index('idx_js_data_raw_task_id_link_type', 'task_id', 'link_type'),
        Index('idx_js_data_raw_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<JsDataRaw(id={self.id}, task_id={self.task_id}, link_type='{self.link_type}')>"
    
    def __str__(self):
        return f"JsDataRaw[{self.id}]: Task-{self.task_id} ({self.link_type})"