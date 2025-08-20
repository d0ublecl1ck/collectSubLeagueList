"""
Pages package for GUI application
包含所有页面组件
"""

from .base_page import BasePage
from .input_page import InputPage
from .input_management_page import InputManagementPage
from .data_crawl_page import DataCrawlPage
from .data_management_page import DataManagementPage
from .batch_import_page import BatchImportPage

__all__ = [
    'BasePage',
    'InputPage', 
    'InputManagementPage',
    'DataCrawlPage',
    'DataManagementPage',
    'BatchImportPage'
]