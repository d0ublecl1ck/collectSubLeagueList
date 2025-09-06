# -*- coding: utf-8 -*-
"""
比赛基本信息模型
"""

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from .base import Base


class MatchBasic(Base):
    """比赛基本信息表"""
    
    __tablename__ = 'match_basic'
    
    # 主键
    match_id = Column(String(50), primary_key=True, comment='比赛ID')
    
    # 基本信息
    game_name = Column(String(200), comment='联赛名称')
    game_date = Column(String(20), comment='比赛日期')
    game_time = Column(String(20), comment='比赛时间')
    home_name = Column(String(200), comment='主队名称')
    away_name = Column(String(200), comment='客队名称')
    home_code = Column(String(50), comment='主队代码')
    away_code = Column(String(50), comment='客队代码')
    home_score = Column(String(20), comment='主队比分')
    away_score = Column(String(20), comment='客队比分')
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    
    def __repr__(self):
        return f"<MatchBasic(match_id='{self.match_id}', game_name='{self.game_name}', home_name='{self.home_name}', away_name='{self.away_name}')>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'match_id': self.match_id,
            'game_name': self.game_name,
            'game_date': self.game_date,
            'game_time': self.game_time,
            'home_name': self.home_name,
            'away_name': self.away_name,
            'home_code': self.home_code,
            'away_code': self.away_code,
            'home_score': self.home_score,
            'away_score': self.away_score,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }