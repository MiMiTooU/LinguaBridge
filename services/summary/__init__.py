"""
LLM总结服务实现模块
"""

# 导入所有LLM服务实现以确保装饰器注册生效
from services.baidu_wenxin import BaiduWenxinSummaryService

__all__ = [
    'BaiduWenxinSummaryService'
]