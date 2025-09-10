import logging
import logging.config
import os
from datetime import datetime
from typing import Dict, Any
import json


class JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加额外的字段
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'endpoint'):
            log_entry["endpoint"] = record.endpoint
        if hasattr(record, 'method'):
            log_entry["method"] = record.method
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
        if hasattr(record, 'duration'):
            log_entry["duration"] = record.duration
            
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> Dict[str, Any]:
    """设置日志配置"""
    
    # 确保logs目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 从环境变量获取日志级别，默认为INFO
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # 日志配置
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": JSONFormatter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            },
            "access_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/access.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "linguabridge": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "linguabridge.access": {
                "level": "INFO",
                "handlers": ["access_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["access_file"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file"]
        }
    }
    
    return config


# 移除冗余的get_logger函数，直接使用logging.getLogger(__name__)


def init_logging():
    """初始化日志配置"""
    config = setup_logging()
    logging.config.dictConfig(config)
    
    # 获取主日志记录器
    logger = logging.getLogger("linguabridge")
    logger.info("日志系统初始化完成")
    
    return logger
