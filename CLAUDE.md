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
- type: 赛事类型 (required) - 支持：常规/东西拆分/联二合并/春秋合并
- year: 赛事年份 (required)
- group: 分组信息 (default='默认组')
- link: 主要数据源链接
- link_second: 备用数据源链接（合并类型任务使用）
- last_crawl_time: 最后爬取时间
- created_at, updated_at: 时间戳
```

### JsDataRaw 表 (js_data_raw)
JS原始数据表，支持多数据源存储
```python
- id: 主键，自增
- task_id: 外键关联tasks.id (required)
- link_type: 链接类型 'primary'/'secondary' (required)
- js_data_raw: 原始JS数据内容 (required)
- created_at: 创建时间
```

### Standings 表 (standings)
积分榜数据表，支持多类型积分榜
```python
- id: 主键，自增
- task_id: 外键关联tasks.id (required)
- standings_type: 积分榜类型 'default'/'east'/'west' (required)
- standings_data: JSON格式积分榜数据 (required)
- created_at: 创建时间
```

### Team 表 (teams)
队伍信息表，存储参赛队伍详细信息
```python
- task_id: 外键关联tasks.id (required)
- js_data_id: 外键关联js_data_raw.id (追踪数据来源)
- team_code: 队伍编码，主键 (required)
- home_name_cn: 中文名称
- home_name_tw: 繁体中文名称
- home_name_en: 英文名称
- image_path: 队徽图片路径
- league_id: 联赛内部ID (required)
- round_num: 所属轮次
- sclass_id: 赛事分类ID
- group_id: 分组ID（东西拆分时使用）
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
├── js_data_raw.py  # JsDataRaw模型
├── standings.py    # Standings模型
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
from models import DatabaseManager, Task, Team, JsDataRaw, Standings

# 初始化
db = DatabaseManager('sqlite:///data.db')
db.create_tables()

# 使用会话
with db.get_session() as session:
    task = Task(level=1, event='World Cup', country='Qatar', 
                league='FIFA World Cup', type='常规', year='2022')
    session.add(task)
    
    # 保存JS数据
    js_data = JsDataRaw(task_id=task.id, link_type='primary', js_data_raw='...')
    session.add(js_data)
    
    # 保存积分榜
    standings = Standings(task_id=task.id, standings_type='default', standings_data='{}')
    session.add(standings)
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

# 添加依赖
uv add --default-index https://mirrors.aliyun.com/pypi/simple/ requests

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

### 搜索功能状态管理解决方案
- **问题**：Treeview搜索中使用`get_children()`只能获取可见项目，导致一次无结果搜索后再也搜不到结果
- **原因**：`detach`的项目不会出现在`get_children()`返回值中，搜索范围逐渐缩小
- **解决方案**：维护完整项目列表`self.all_task_items = []`存储所有项目ID
- **关键实现**：
  - 数据加载时保存项目ID到完整列表：`self.all_task_items.append(item_id)`
  - 搜索时先`reattach`所有项目，再进行过滤
  - 使用完整列表`self.all_task_items`而非`get_children()`作为搜索范围
- **技术要点**：添加TclError异常处理，避免已删除项目的错误

### Git 提交流程
- 当需要提交 git 时，分成两步执行：
  1. 先告知即将提交的文件列表，等待用户确认
  2. 确认后自动执行提交并运行 `git push`

## 爬取任务类型说明

### 四种任务类型
1. **常规** - 单链接爬取，生成一个默认积分榜
2. **东西拆分** - 单链接爬取，按group_id分组生成东部/西部积分榜
3. **联二合并** - 双链接爬取（联赛+第二阶段），合并数据生成积分榜
4. **春秋合并** - 双链接爬取（春季+秋季），合并数据生成积分榜

### 数据关系图
```
Task (1) ──┬─→ JsDataRaw (1:N)   # 多数据源支持
           ├─→ Standings (1:N)  # 多积分榜支持
           └─→ Team (1:N)       # 队伍数据

JsDataRaw (1) ──→ Team (1:N)    # 数据来源追踪
```

### 爬取流程核心方法
- `crawl_task()` - 主爬取入口，根据type分发任务
- `crawl_regular_task()` - 处理常规任务
- `crawl_east_west_split_task()` - 处理东西拆分任务  
- `crawl_merge_task()` - 处理合并类型任务
- `fetch_and_parse_link()` - 单链接爬取解析
- `split_standings_by_group()` - 东西拆分逻辑
- `merge_standings_data()` - 数据合并逻辑

### 重要开发注意事项
- 索引命名必须唯一：使用表前缀避免冲突
- JS数据解析依赖 `arrTeam` 数组结构
- 东西拆分依据：按 `group_id` 奇偶数分组
- 积分榜存储格式：JSON字符串，包含rank/team_name/points等字段
