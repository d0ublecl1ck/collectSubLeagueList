"""
Task 模型定义 - 赛事任务表
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from loguru import logger

from .base import Base


class Task(Base):
    """赛事任务表 - 存储爬虫任务相关信息"""
    __tablename__ = 'tasks'
    
    # 主键字段
    id = Column(Integer, primary_key=True, autoincrement=True, comment='任务唯一标识ID')
    
    # 赛事基本信息
    level = Column(Integer, nullable=False, comment='赛事级别')
    event = Column(String(100), nullable=False, comment='赛事名称')
    country = Column(String(50), nullable=False, comment='所属国家/地区')
    league = Column(String(100), nullable=False, comment='联赛名称')
    type = Column(String(20), nullable=False, comment='赛事类型：常规/联二合并/春秋合并/东西拆分')
    year = Column(String(10), nullable=False, comment='赛事年份')
    group = Column(String(50), nullable=False, default='默认组', comment='分组信息')
    
    # 数据源相关
    link = Column(Text, nullable=True, comment='主要数据源链接')
    link_second = Column(Text, nullable=True, comment='备用数据源链接')
    
    # 时间戳字段
    last_crawl_time = Column(DateTime, nullable=True, comment='最后一次爬取时间')
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment='更新时间')
    
    # 关联关系
    teams = relationship("Team", back_populates="task", cascade="all, delete-orphan")
    js_data_records = relationship("JsDataRaw", back_populates="task", cascade="all, delete-orphan")
    standings_records = relationship("Standings", back_populates="task", cascade="all, delete-orphan")
    match_records = relationship("Match", back_populates="task", cascade="all, delete-orphan")
    
    # 索引优化建议和约束
    __table_args__ = (
        Index('idx_country_league_year', 'country', 'league', 'year'),
        Index('idx_last_crawl_time', 'last_crawl_time'),
        Index('idx_type', 'type'),
        UniqueConstraint('league', 'year', 'group', name='uk_league_year_group'),
    )
    
    def __repr__(self):
        return f"<Task(id={self.id}, league='{self.league}', year='{self.year}')>"
    
    def __str__(self):
        return f"Task[{self.id}]: {self.country} - {self.league} ({self.year})"