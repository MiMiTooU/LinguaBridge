"""
百度文心大模型服务工具函数
"""
import logging
from typing import List, Dict, Any, Optional
from .constants import (
    SUMMARY_TYPES, MIN_TEXT_LENGTH, MAX_TEXT_LENGTH, 
    MAX_BATCH_SIZE, MAX_RETRIES
)

logger = logging.getLogger(__name__)


def validate_text_input(text: str) -> bool:
    """验证文本输入"""
    if not text or not isinstance(text, str):
        return False
    
    text_length = len(text.strip())
    if text_length < MIN_TEXT_LENGTH or text_length > MAX_TEXT_LENGTH:
        return False
    
    return True


def validate_batch_input(texts: List[str]) -> bool:
    """验证批量文本输入"""
    if not texts or not isinstance(texts, list):
        return False
    
    if len(texts) > MAX_BATCH_SIZE:
        return False
    
    return all(validate_text_input(text) for text in texts)


def get_summary_prompt(summary_type: str, text: str) -> str:
    """获取总结提示词"""
    if summary_type not in SUMMARY_TYPES:
        summary_type = "general"
    
    template = SUMMARY_TYPES[summary_type]["prompt_template"]
    return template.format(text=text)


def format_summary_result(text: str, summary_type: str, max_length: Optional[int] = None) -> str:
    """格式化总结结果"""
    if not text:
        return ""
    
    # 清理文本
    result = text.strip()
    
    # 如果设置了长度限制，进行截断
    if max_length and len(result) > max_length:
        result = result[:max_length] + "..."
    
    return result


def create_error_result(error_message: str) -> str:
    """创建错误结果"""
    return f"总结失败: {error_message}"


def retry_on_failure(func, max_retries: int = MAX_RETRIES):
    """重试装饰器"""
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"第{attempt + 1}次尝试失败: {e}")
                if attempt == max_retries - 1:
                    break
        
        raise last_exception
    
    return wrapper


def get_available_summary_types() -> Dict[str, Dict[str, str]]:
    """获取可用的总结类型"""
    return {
        key: {
            "name": value["name"],
            "description": value["description"]
        }
        for key, value in SUMMARY_TYPES.items()
    }
