# -*- coding: utf-8 -*-
"""
Match 模型定义 - 赛程数据表
"""

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Index
from sqlalchemy.orm import relationship
from loguru import logger

from .base import Base


class Match(Base):
    """赛程数据表 - 存储比赛赛程信息"""
    __tablename__ = 'matches'
    
    # 主键字段
    match_id = Column(Integer, primary_key=True, comment='比赛ID（来自JS数据）')
    
    # 关联字段
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='关联的任务ID')
    js_data_id = Column(Integer, ForeignKey('js_data_raw.id'), nullable=True, comment='JS数据来源ID')
    
    # 比赛基本信息
    league_id = Column(Integer, nullable=False, comment='联赛ID')
    round_num = Column(Integer, nullable=False, comment='轮次号')
    match_time = Column(String(50), nullable=True, comment='比赛时间')
    
    # 参赛队伍
    home_team_code = Column(String(20), nullable=False, comment='主队编码')
    away_team_code = Column(String(20), nullable=False, comment='客队编码')
    
    # 比赛结果
    full_score = Column(String(20), nullable=True, comment='全场比分')
    half_score = Column(String(20), nullable=True, comment='半场比分')
    
    # 排名信息
    home_team_rank = Column(String(10), nullable=True, comment='主队排名')
    away_team_rank = Column(String(10), nullable=True, comment='客队排名')
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment='创建时间')
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment='更新时间')
    
    # 关联关系
    task = relationship("Task", back_populates="match_records")
    js_data = relationship("JsDataRaw")
    
    # 索引优化
    __table_args__ = (
        Index('idx_match_task_id_round', 'task_id', 'round_num'),
        Index('idx_match_league_id', 'league_id'),
        Index('idx_match_teams', 'home_team_code', 'away_team_code'),
        Index('idx_match_time', 'match_time'),
    )
    
    def __repr__(self):
        return f"<Match(match_id={self.match_id}, round={self.round_num})>"
    
    def __str__(self):
        return f"Match[{self.match_id}]: R{self.round_num} {self.home_team_code} vs {self.away_team_code}"