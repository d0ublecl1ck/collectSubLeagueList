"""
Team 模型定义 - 队伍信息表
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import relationship
from loguru import logger

from .base import Base


class Team(Base):
    """队伍信息表 - 存储参赛队伍详细信息"""
    __tablename__ = 'teams'
    
    # 外键关联
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, comment='关联的任务ID')
    js_data_id = Column(Integer, ForeignKey('js_data_raw.id'), nullable=True, comment='关联的JS数据源ID')
    
    # 队伍基本信息
    team_code = Column(Integer, primary_key=True, nullable=False, comment='队伍编码（主键）')
    home_name_cn = Column(String(100), nullable=True, comment='队伍中文名称')
    home_name_tw = Column(String(100), nullable=True, comment='队伍繁体中文名称')
    home_name_en = Column(String(100), nullable=True, comment='队伍英文名称')
    image_path = Column(String(255), nullable=True, comment='队徽图片路径')
    
    # 赛事相关信息
    league_id = Column(Integer, nullable=False, comment='联赛内部ID')
    round_num = Column(String(20), nullable=True, comment='所属轮次')
    sclass_id = Column(String(50), nullable=True, comment='赛事分类ID')
    group_id = Column(Integer, nullable=True, comment='分组ID')
    
    # 其他字段
    unknown1 = Column(String(100), nullable=True, comment='未知字段1，待明确用途')
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment='更新时间')
    
    # 关联关系
    task = relationship("Task", back_populates="teams")
    js_data_source = relationship("JsDataRaw", back_populates="teams")
    
    # 索引优化建议
    __table_args__ = (
        Index('idx_task_id', 'task_id'),
        Index('idx_js_data_id', 'js_data_id'),
        Index('idx_league_id', 'league_id'),
        Index('idx_home_name_cn', 'home_name_cn'),
    )
    
    def __repr__(self):
        return f"<Team(team_code={self.team_code}, home_name_cn='{self.home_name_cn}')>"
    
    def __str__(self):
        return f"Team[{self.team_code}]: {self.home_name_cn or self.home_name_en or 'Unknown'}"