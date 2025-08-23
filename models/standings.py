# -*- coding: utf-8 -*-
"""
Standings 模型定义 - 积分榜数据表
"""

from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from decimal import Decimal, ROUND_HALF_UP
from loguru import logger

from .base import Base


class Standings(Base):
    """积分榜数据表 - 存储结构化的积分榜数据"""
    __tablename__ = 'standings'
    
    # 主键字段
    id = Column(Integer, primary_key=True, autoincrement=True, comment='积分榜唯一标识ID')
    
    # 关联字段
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=False, comment='关联的任务ID')
    
    # 积分榜分类维度
    standings_category = Column(String(10), nullable=False, comment='积分榜类型: total/home/away')
    division_type = Column(String(10), nullable=False, default='default', comment='分区类型: default/east/west')
    
    # 队伍信息
    team_code = Column(String(20), nullable=False, comment='队伍编码')
    
    # 轮次信息
    round_num = Column(Integer, nullable=False, comment='截止轮次（该积分榜数据截止到第几轮）')
    
    # 积分榜数据
    rank = Column(Integer, nullable=False, comment='排名')
    games = Column(Integer, nullable=False, default=0, comment='已赛场次')
    wins = Column(Integer, nullable=False, default=0, comment='胜场')
    draws = Column(Integer, nullable=False, default=0, comment='平场')
    losses = Column(Integer, nullable=False, default=0, comment='负场')
    goals_for = Column(Integer, nullable=False, default=0, comment='进球数')
    goals_against = Column(Integer, nullable=False, default=0, comment='失球数')
    goal_diff = Column(Integer, nullable=False, default=0, comment='净胜球')
    points = Column(Integer, nullable=False, default=0, comment='积分')
    
    # 时间戳字段
    created_at = Column(DateTime, server_default=func.current_timestamp(), comment='创建时间')
    
    # 关联关系
    task = relationship("Task", back_populates="standings_records")
    
    # 计算属性
    @hybrid_property
    def win_pct(self):
        """胜率百分比"""
        if self.games == 0:
            return "0.0%"
        return f"{(self.wins / self.games * 100):.1f}%"
    
    @hybrid_property
    def draw_pct(self):
        """平局率百分比"""
        if self.games == 0:
            return "0.0%"
        return f"{(self.draws / self.games * 100):.1f}%"
    
    @hybrid_property
    def loss_pct(self):
        """负率百分比"""
        if self.games == 0:
            return "0.0%"
        return f"{(self.losses / self.games * 100):.1f}%"
    
    @hybrid_property
    def avg_goals_for(self):
        """平均进球数（四舍五入到2位小数）"""
        if self.games == 0:
            return "0.00"
        value = self.goals_for / self.games
        return str(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    @hybrid_property
    def avg_goals_against(self):
        """平均失球数（四舍五入到2位小数）"""
        if self.games == 0:
            return "0.00"
        value = self.goals_against / self.games
        return str(Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    # 索引优化
    __table_args__ = (
        Index('idx_standings_task_category_division_round', 'task_id', 'standings_category', 'division_type', 'round_num'),
        Index('idx_standings_team_code', 'team_code'),
        Index('idx_standings_rank', 'rank'),
        Index('idx_standings_round_num', 'round_num'),
        Index('idx_standings_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Standings(id={self.id}, task_id={self.task_id}, category='{self.standings_category}', division='{self.division_type}', team='{self.team_code}', rank={self.rank})>"
    
    def __str__(self):
        return f"Standings[{self.id}]: Task-{self.task_id} ({self.standings_category}/{self.division_type}) {self.team_code} 排名{self.rank}"