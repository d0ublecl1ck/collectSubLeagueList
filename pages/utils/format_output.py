# -*- coding: utf-8 -*-
"""
数据导出格式化工具
"""

import csv
import os
from io import StringIO

from sqlalchemy.orm import Session
from typing import Dict, Tuple, Optional

from models import Match, Standings, Task, Team, DatabaseManager
from utils import get_database_url


def format_output(year: str) -> str:
    """
    对外导出函数：根据年份查询数据并返回 CSV 字符串。
    内部自行管理数据库会话。
    """
    # 使用统一的数据库路径获取方式
    db = DatabaseManager(get_database_url())
    with db.get_session() as session:
        return _format_output_with_session(session, year)


def _build_team_promotion_cache(session: Session, year: str) -> Dict[Tuple[str, str], str]:
    """
    构建球队升班马/降班马的缓存映射。
    
    Args:
        session: SQLAlchemy 会话
        year: 基准年份（如 "2025"）
        
    Returns:
        Dict: {(team_code, target_year): "升班马"/"降班马"/""} 的映射
    """
    cache = {}
    
    # 固定检查2025, 2024, 2023这三个年份
    years_to_check = [2025, 2024, 2023]
    
    # 获取所有相关的team_code
    all_team_codes = (
        session.query(Team.team_code)
        .distinct()
        .all()
    )
    
    for team_code_tuple in all_team_codes:
        team_code = str(team_code_tuple[0])  # 确保转换为字符串
        
        # 获取该队伍在不同年份的level信息
        team_year_levels = {}
        
        # 查询该team_code在所有任务中的level信息
        team_tasks = (
            session.query(Task.year, Task.level)
            .join(Team, Team.task_id == Task.id)
            .filter(Team.team_code == team_code)
            .distinct()
            .all()
        )
        
        for task_year, task_level in team_tasks:
            if task_year and task_level is not None:
                # 提取年份（处理 2025-2026 -> 2025 的情况）
                try:
                    if '-' in task_year:
                        extracted_year = int(task_year.split('-')[0])
                    else:
                        extracted_year = int(task_year)
                    
                    if extracted_year in years_to_check:
                        team_year_levels[extracted_year] = task_level
                except ValueError:
                    continue
        
        # 为每个目标年份计算升降级状态
        for target_year in years_to_check:
            target_year_str = str(target_year)
            prev_year = target_year - 1
            
            if target_year in team_year_levels and prev_year in team_year_levels:
                current_level = team_year_levels[target_year]
                prev_level = team_year_levels[prev_year]
                
                if current_level < prev_level:  # level数字越小等级越高
                    cache[(team_code, target_year_str)] = "升班马"
                elif current_level > prev_level:
                    cache[(team_code, target_year_str)] = "降班马"
                else:
                    cache[(team_code, target_year_str)] = ""
            else:
                cache[(team_code, target_year_str)] = ""
    
    return cache


def _format_output_with_session(session: Session, year: str) -> str:
    """
    导出指定年份的所有任务数据为 CSV 字符串。

    - 按轮次从低到高导出
    - 每个轮次之间空一行
    - 表头为：
      |联赛|赛季|年份|等级|球队名称|排名|赛/轮|积分|胜率|得球数|失球数|净胜球|赛/轮|积分|胜率|得球数|失球数|净胜球|赛/轮|积分|胜率|得球数|失球数|净胜球|
      其中三组指标依次为：总积分榜/主场积分榜/客场积分榜

    Args:
        session: SQLAlchemy 会话
        year: 四位年份字符串，如 "2022"

    Returns:
        str: CSV 内容字符串（UTF-8 文本；是否带 BOM 由写文件方决定）
    """

    # 查找指定年份的所有任务。如果输入 2024，同时查询 2024-2025 赛季的任务
    tasks1 = session.query(Task).filter(Task.year == year).order_by(Task.id).all()
    year2 = f"{year}-{int(year) + 1}"
    tasks2 = session.query(Task).filter(Task.year == year2).order_by(Task.id).all()
    tasks = tasks1 + tasks2

    if not tasks:
        return ""
    
    # 构建升班马/降班马缓存
    promotion_cache = _build_team_promotion_cache(session, year)

    # CSV 输出缓冲区
    output = StringIO()
    writer = csv.writer(output, lineterminator='\n')

    # 表头
    headers = [
        "联赛", "赛季", "年份", "等级", "球队名称", "排名",
        "赛/轮", "积分", "胜率", "得球数", "失球数", "净胜球",  # 总
        "赛/轮", "积分", "胜率", "得球数", "失球数", "净胜球",  # 主
        "赛/轮", "积分", "胜率", "得球数", "失球数", "净胜球",  # 客
        "2025队伍类型", "2024队伍类型", "2023队伍类型",  # 升降级信息
    ]
    writer.writerow(headers)

    for task in tasks:
        # 取该任务的所有轮次，升序
        rounds = (
            session.query(Match.round_num)
            .filter(Match.task_id == task.id)
            .distinct()
            .order_by(Match.round_num)
            .all()
        )

        for idx, round_data in enumerate(rounds):
            round_num = round_data[0]
            if not round_num:
                continue

            _export_round_data(writer, session, task, round_num, base_year=year, promotion_cache=promotion_cache)

            # 轮次之间空一行（最后一轮不加）
            if idx < len(rounds) - 1:
                writer.writerow([])

    csv_content = output.getvalue()
    output.close()
    return csv_content


def _export_round_data(
    writer: csv.writer, session: Session, task: Task, round_num: int, base_year: str, promotion_cache: Dict[Tuple[str, str], str]
):
    """
    导出单个任务在某个轮次的三类积分榜（总/主/客）汇总到每队一行。
    使用 Standings.rank 升序作为行顺序，球队名从 Team 表基于 (task_id, round_num) 获取。
    """

    # 用三类类型补全三组指标
    standings_types = ["total", "home", "away"]

    # 总积分榜（决定排名与行数）：按 rank 升序
    total_standings = (
        session.query(Standings)
        .filter(
            Standings.task_id == task.id,
            Standings.round_num == round_num,
            Standings.standings_category == "total",
        )
        .order_by(Standings.rank.asc())
        .all()
    )

    if not total_standings:
        return

    # 按排名构建本轮的所有行，直接通过team_code匹配中文名
    rows: list[list] = []
    for total_standing in total_standings:
        team_code = str(total_standing.team_code)
        
        # 通过team_code匹配中文名
        team = (
            session.query(Team)
            .filter(Team.task_id == task.id, Team.team_code == team_code)
            .first()
        )
        team_name = team.home_name_cn if team else ""

        # 基本信息（直接填入球队名称）
        row = [
            task.league or "",            # 联赛
            task.year or "",              # 赛季（原始）
            base_year or "",              # 年份（输入的年份）
            str(task.level) if task.level is not None else "",  # 等级
            team_name,                    # 球队名称（直接匹配）
            total_standing.rank or "",    # 排名
        ]

        # 三类积分榜补齐指标
        for standings_type in standings_types:
            standing = (
                session.query(Standings)
                .filter(
                    Standings.task_id == task.id,
                    Standings.round_num == round_num,
                    Standings.standings_category == standings_type,
                    Standings.team_code == team_code,
                )
                .first()
            )

            if standing:
                row.extend(
                    [
                        standing.games or 0,           # 赛/轮
                        standing.points or 0,          # 积分
                        standing.win_pct,              # 胜率（模型返回字符串）
                        standing.goals_for or 0,       # 得球数
                        standing.goals_against or 0,   # 失球数
                        standing.goal_diff or 0,       # 净胜球
                    ]
                )
            else:
                row.extend(["", "", "", "", "", ""])
        
        # 添加升降级信息（固定三个年份的队伍类型）
        for target_year_str in ["2025", "2024", "2023"]:
            team_type = promotion_cache.get((team_code, target_year_str), "")
            row.append(team_type)

        rows.append(row)

    # 输出所有行
    for row in rows:
        writer.writerow(row)



def validate_year_format(year_str: str) -> bool:
    """
    验证年份格式是否正确（四位数字，2000-2100）。
    """
    if not year_str or not isinstance(year_str, str):
        return False

    if not year_str.isdigit() or len(year_str) != 4:
        return False

    try:
        year_int = int(year_str)
        return 2000 <= year_int <= 2100
    except ValueError:
        return False


if __name__ == '__main__':
    # 手动调试检查
    csv_content = format_output('2024')
    open('test.csv', 'w', encoding='utf-8').write(csv_content)
