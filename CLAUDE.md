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

pages/
├── __init__.py            # 页面模块导出
├── base_page.py          # 基础页面类
├── input_page.py         # 输入页面 - 任务录入
├── input_management_page.py  # 输入管理页面 - 任务管理
├── data_crawl_page.py    # 数据爬取页面 - 爬虫控制
└── data_management_page.py   # 数据管理页面 - 队伍数据管理

main.py                   # GUI主应用程序
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

## GUI 功能说明

### 页面功能
1. **输入页面** - 任务录入表单
   
2. **输入管理页面** - 任务管理界面
   
3. **数据爬取页面** - 爬虫执行控制
   
4. **数据管理页面** - 队伍数据管理

### 技术特性
- 基于 tkinter + ttk 的现代 GUI 界面
- MVC 架构设计，页面模块化
- 多线程爬虫执行，不阻塞界面
- 完整的日志记录系统
- 数据库会话管理

## 常用命令
```bash
# 安装依赖
uv sync

# 运行 GUI 应用
uv run main.py

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

## 开发经验记录
### GUI 开发注意事项
- 所有 Python 文件需添加 `# -*- coding: utf-8 -*-` 编码声明
- 使用 `uv run` 运行程序确保依赖正确加载
- tkinter 应用使用多线程时设置 `daemon=True` 避免程序无法退出
- 长文本字符串使用 `\\n` 转义换行符避免语法错误

### Git 提交流程
- 当需要提交 git 时，分成两步执行：
  1. 先告知即将提交的文件列表，等待用户确认
  2. 确认后自动执行提交并运行 `git push`
