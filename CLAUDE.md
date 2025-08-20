# collectSubLeagueList 项目文档

## 项目信息
- **功能**: 足球联赛数据爬虫和存储系统
- **技术栈**: Python 3.8.10, SQLAlchemy, loguru
- **仓库**: https://github.com/d0ublecl1ck/collectSubLeagueList.git

## 数据库模型

### Task 表 (tasks)
赛事任务表，存储爬虫任务信息
```python
- id: 主键，自增
- level: 赛事级别 (required)
- event: 赛事名称 (required)
- country: 国家/地区 (required)
- league: 联赛名称 (required)
- type: 赛事类型 (required)
- year: 赛事年份 (required)
- group: 分组信息 (default='默认组')
- link: 主要数据源链接
- link_second: 备用数据源链接
- js_data_raw: 原始JS数据
- standings: 积分榜数据
- last_crawl_time: 最后爬取时间
- created_at, updated_at: 时间戳
```

### Team 表 (teams)
队伍信息表，存储参赛队伍详细信息
```python
- task_id: 外键关联tasks.id (required)
- team_code: 队伍编码，主键 (required)
- home_name_cn: 中文名称
- home_name_tw: 繁体中文名称
- home_name_en: 英文名称
- image_path: 队徽图片路径
- league_id: 联赛内部ID (required)
- round_num: 所属轮次
- sclass_id: 赛事分类ID
- group_id: 分组ID
- unknown1: 未知字段
- created_at, updated_at: 时间戳
```

## 项目结构
```
models/
├── __init__.py     # 模块导出
├── base.py         # Base declarative_base
├── task.py         # Task模型
├── team.py         # Team模型
└── database.py     # DatabaseManager类
```

## 数据库操作示例
```python
from models import DatabaseManager, Task, Team

# 初始化
db = DatabaseManager('sqlite:///data.db')
db.create_tables()

# 使用会话
with db.get_session() as session:
    task = Task(level=1, event='World Cup', country='Qatar', 
                league='FIFA World Cup', type='常规', year='2022')
    session.add(task)
```

## 开发环境
- Python: 3.8.10
- 包管理: uv
- 依赖: SQLAlchemy, loguru
- 数据库: SQLite (可扩展其他)

## 常用命令
```bash
# 安装依赖
uv sync

# 运行项目
python main.py

# Git操作
git add .
git commit -m "message"
git push
```

## 开发规范
- 使用 loguru 记录日志
- 数据库操作使用会话管理器
- 遵循现有代码风格
- 错误记录在此文档防止重复