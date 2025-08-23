"""
数据库管理器 - 提供数据库连接和会话管理功能
"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from .base import Base


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str, echo: bool = False):
        """
        初始化数据库管理器
        
        Args:
            database_url: 数据库连接URL，格式如 'sqlite:///path/to/database.db'
            echo: 是否打印SQL语句
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=echo)
        self.Session = sessionmaker(bind=self.engine)
        
        logger.info(f"数据库管理器初始化完成，连接: {database_url}")

    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)
        logger.info("数据库表创建成功")

    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(self.engine)
        logger.info("数据库表删除成功")

    @contextmanager
    def get_session(self):
        """获取数据库会话上下文管理器"""
        session = self.Session()
        try:
            logger.debug("数据库会话已创建")
            yield session
            session.commit()
            logger.debug("数据库事务提交成功")
        except Exception as e:
            session.rollback()
            logger.error(f"数据库事务回滚: {e}")
            raise
        finally:
            session.close()
            logger.debug("数据库会话已关闭")

    def close_all_connections(self):
        """关闭所有连接"""
        self.engine.dispose()
        logger.info("所有数据库连接已关闭")

    def get_table_info(self):
        """获取数据库表信息"""
        with self.get_session() as session:
            tables = Base.metadata.tables.keys()
            logger.info(f"数据库包含表: {list(tables)}")
            return list(tables)