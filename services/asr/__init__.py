"""
ASR服务实现模块
"""

# 导入所有ASR服务实现以确保装饰器注册生效
from services.funasr import FunASRService

__all__ = [
    'FunASRService'
]