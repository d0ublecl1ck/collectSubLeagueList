# -*- coding: utf-8 -*-
"""
赛程表数据导出格式化工具
"""

import csv
import os
from io import StringIO
from typing import Dict, List
from sqlalchemy.orm import Session

from models import Match, Task, Team, DatabaseManager
from utils import get_database_url


def format_match_output(year: str) -> str:
    """
    对外导出函数：根据年份查询赛程数据并返回 CSV 字符串。
    内部自行管理数据库会话。
    """
    # 使用统一的数据库路径获取方式
    db = DatabaseManager(get_database_url())
    with db.get_session() as session:
        return _format_match_output_with_session(session, year)


def _format_match_output_with_session(session: Session, year: str) -> str:
    """
    导出指定年份的所有赛程数据为 CSV 字符串。

    - 按任务分组，每个任务内按轮次分组
    - 每个轮次之间空一行
    - 表头为：
      比赛ID,联赛,赛季年份,轮次,大致日期,比赛时间,主队,主队得分,客队得分,客队,比赛状态

    Args:
        session: SQLAlchemy 会话
        year: 四位年份字符串，如 "2024"

    Returns:
        str: CSV 内容字符串（UTF-8 文本）
    """
    # 查找指定年份的所有任务。如果输入 2024，同时查询 2024-2025 赛季的任务
    tasks1 = session.query(Task).filter(Task.year == year).order_by(Task.id).all()
    year2 = f"{year}-{int(year) + 1}"
    tasks2 = session.query(Task).filter(Task.year == year2).order_by(Task.id).all()
    tasks = tasks1 + tasks2

    if not tasks:
        return ""

    # CSV 输出缓冲区
    output = StringIO()
    writer = csv.writer(output, lineterminator='\n')

    # 表头
    headers = [
        "比赛ID", "联赛", "赛季年份", "轮次", "大致日期",
        "比赛时间", "主队", "主队得分", "客队得分", "客队", "比赛状态"
    ]
    writer.writerow(headers)

    for task_idx, task in enumerate(tasks):
        # 查询该任务的所有比赛
        matches = (
            session.query(
                Match,
                Team.home_name_cn.label('home_team_name'),
                Team.home_name_cn.label('away_team_name'),
                Task.league,
                Task.year
            )
            .join(Team, (Match.home_team_code == Team.team_code) & (Match.task_id == Team.task_id))
            .join(Task, Match.task_id == Task.id)
            .filter(Match.task_id == task.id)
            .order_by(Match.round_num, Match.match_time)
            .all()
        )

        if not matches:
            continue

        # 计算每个轮次的"大致日期"
        round_approximate_dates = _calculate_round_dates(matches)

        # 按轮次分组
        from collections import defaultdict
        round_matches = defaultdict(list)
        for match_data, home_team_name, away_team_name, league, year in matches:
            round_matches[match_data.round_num].append(
                (match_data, home_team_name, away_team_name, league, year)
            )

        # 按轮次升序输出
        sorted_rounds = sorted(round_matches.keys())

        for round_idx, round_num in enumerate(sorted_rounds):
            round_match_list = round_matches[round_num]

            # 获取该轮次的"大致日期"
            approximate_date = round_approximate_dates.get(round_num, "")

            # 输出该轮次的所有比赛
            for match_data, home_team_name, away_team_name, league, year in round_match_list:
                # 格式化比分 - 拆分为主分和客分
                if match_data.full_score:
                    try:
                        # 解析比分格式 "5-2"
                        if '-' in match_data.full_score:
                            home_score, away_score = match_data.full_score.split('-', 1)
                            home_score = home_score.strip()
                            away_score = away_score.strip()
                        else:
                            home_score = match_data.full_score
                            away_score = match_data.full_score
                    except:
                        home_score = match_data.full_score
                        away_score = match_data.full_score
                else:
                    home_score = ""
                    away_score = ""

                # 格式化时间（match_time是字符串格式 "08-07 22:00"）
                match_time = match_data.match_time if match_data.match_time else '待定'

                # 状态判断
                status = "已结束" if match_data.full_score else "未开始"

                # 写入CSV行
                writer.writerow([
                    str(match_data.match_id),  # 比赛ID
                    league or "",              # 联赛
                    str(year) if year else "",  # 赛季年份
                    str(match_data.round_num), # 轮次
                    approximate_date,          # 大致日期
                    match_time,               # 比赛时间
                    home_team_name or f"队伍{match_data.home_team_code}",    # 主队
                    home_score,               # 主队得分
                    away_score,               # 客队得分
                    away_team_name or f"队伍{match_data.away_team_code}",    # 客队
                    status                    # 比赛状态
                ])

            # 轮次之间空一行（最后一轮不加）
            if round_idx < len(sorted_rounds) - 1:
                writer.writerow([])

        # 任务之间空一行（最后一个任务不加）
        if task_idx < len(tasks) - 1:
            writer.writerow([])

    csv_content = output.getvalue()
    output.close()
    return csv_content


def _calculate_round_dates(matches) -> Dict[int, str]:
    """
    计算每个轮次的"大致日期"（出现次数最多的日期）

    Args:
        matches: 查询到的所有Match对象列表，格式为 (match_data, home_name, away_name, league, year)

    Returns:
        dict: {轮次号: 大致日期} 的映射
    """
    round_date_count = {}
    round_approximate_date = {}

    for match_data, home_name, away_name, league, year in matches:
        round_num = match_data.round_num
        if not round_num:
            continue

        # 提取日期部分（从 "08-07 22:00" 提取 "08-07"）
        if match_data.match_time and isinstance(match_data.match_time, str):
            try:
                # 处理 "08-07 22:00" 格式
                date_part = match_data.match_time.split()[0]
            except:
                date_part = None
        else:
            date_part = None

        if date_part:
            # 统计每个轮次的日期出现次数
            if round_num not in round_date_count:
                round_date_count[round_num] = {}
            round_date_count[round_num][date_part] = round_date_count[round_num].get(date_part, 0) + 1

    # 找出每个轮次出现次数最多的日期
    for round_num, date_counts in round_date_count.items():
        if date_counts:
            # 按出现次数排序，取最多
            most_common_date = max(date_counts.items(), key=lambda x: x[1])[0]
            round_approximate_date[round_num] = most_common_date

    return round_approximate_date


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
    csv_content = format_match_output('2024')
    open('test_matches.csv', 'w', encoding='utf-8').write(csv_content)