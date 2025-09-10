"""
FunASR服务环境变量配置
"""
import os
from .constants import (
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_USE_SSL, 
    DEFAULT_MODE, DEFAULT_CHUNK_SIZE
)

def get_funasr_host() -> str:
    """获取FunASR服务器地址"""
    return os.getenv("FUNASR_HOST", DEFAULT_HOST)

def get_funasr_port() -> int:
    """获取FunASR服务器端口"""
    return int(os.getenv("FUNASR_PORT", str(DEFAULT_PORT)))

def get_funasr_use_ssl() -> bool:
    """获取是否使用SSL连接"""
    return os.getenv("FUNASR_USE_SSL", str(DEFAULT_USE_SSL)).lower() == "true"

def get_funasr_mode() -> str:
    """获取识别模式"""
    return os.getenv("FUNASR_MODE", DEFAULT_MODE)

def get_funasr_chunk_size() -> str:
    """获取分块配置"""
    return os.getenv("FUNASR_CHUNK_SIZE", DEFAULT_CHUNK_SIZE)

def get_client_script_path() -> str:
    """获取客户端脚本路径"""
    from pathlib import Path
    default_path = Path(__file__).parent.parent.parent / "client" / "funasr_wss_client.py"
    return os.getenv("FUNASR_CLIENT_SCRIPT", str(default_path))
