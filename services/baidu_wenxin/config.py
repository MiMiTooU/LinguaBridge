"""
百度文心大模型服务环境变量配置
"""
import os
from .constants import (
    DEFAULT_MODEL_NAME, DEFAULT_TEMPERATURE, DEFAULT_TOP_P, 
    DEFAULT_PENALTY_SCORE, DEFAULT_MAX_LENGTH, API_TIMEOUT
)

def get_baidu_api_key() -> str:
    """获取百度API密钥"""
    api_key = os.getenv("BAIDU_API_KEY")
    if not api_key:
        raise ValueError("需要设置BAIDU_API_KEY环境变量")
    return api_key

def get_baidu_secret_key() -> str:
    """获取百度Secret密钥"""
    secret_key = os.getenv("BAIDU_SECRET_KEY")
    if not secret_key:
        raise ValueError("需要设置BAIDU_SECRET_KEY环境变量")
    return secret_key

def get_model_name() -> str:
    """获取模型名称"""
    return os.getenv("BAIDU_MODEL_NAME", DEFAULT_MODEL_NAME)

def get_temperature() -> float:
    """获取温度参数"""
    return float(os.getenv("BAIDU_TEMPERATURE", str(DEFAULT_TEMPERATURE)))

def get_top_p() -> float:
    """获取top_p参数"""
    return float(os.getenv("BAIDU_TOP_P", str(DEFAULT_TOP_P)))

def get_penalty_score() -> float:
    """获取惩罚分数参数"""
    return float(os.getenv("BAIDU_PENALTY_SCORE", str(DEFAULT_PENALTY_SCORE)))

def get_max_length() -> int:
    """获取最大长度限制"""
    return int(os.getenv("BAIDU_MAX_LENGTH", str(DEFAULT_MAX_LENGTH)))

def get_api_timeout() -> int:
    """获取API超时时间"""
    return int(os.getenv("BAIDU_API_TIMEOUT", str(API_TIMEOUT)))
