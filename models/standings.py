# -*- coding: utf-8 -*-
"""
Standings 模型定义 - 积分榜数据表
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Index
from sqlalchemy.orm import relationship
from loguru import logger

from .base import Base


class Standings(Base):
    """积分榜数据表 - 存储计算后的积分榜数据"""
    __tablename__ = 'standings'
    
    # 主键字段
    id = Column(Integer, primary_key=True, autoincrement=True, comment='积分榜唯一标识ID')
    
    # 关联字段
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='关联的任务ID')
    
    # 积分榜类型
    standings_type = Column(String(20), nullable=False, comment='积分榜类型: default/east/west')
    
    # 积分榜数据
    standings_data = Column(Text, nullable=False, comment='JSON格式的积分榜数据')
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment='创建时间')
    
    # 关联关系
    task = relationship("Task", back_populates="standings_records")
    
    # 索引优化
    __table_args__ = (
        Index('idx_standings_task_id_type', 'task_id', 'standings_type'),
        Index('idx_standings_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Standings(id={self.id}, task_id={self.task_id}, type='{self.standings_type}')>"
    
    def __str__(self):
        return f"Standings[{self.id}]: Task-{self.task_id} ({self.standings_type})"