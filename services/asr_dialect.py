"""
ASR方言识别服务抽象基类和服务管理
"""
import os
import sys
import logging
import tempfile
import subprocess
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field

# 设置日志
logger = logging.getLogger(__name__)

# Pydantic模型定义
class ASRRecognitionSegment(BaseModel):
    """ASR识别结果段落模型"""
    text: str = Field(..., description="识别的文本内容")
    emotion: Optional[str] = Field(None, description="情感信息")
    speaker: Optional[str] = Field(None, description="说话人信息")
    language: Optional[str] = Field(None, description="语言信息")
    start_time: Optional[float] = Field(None, description="开始时间(秒)")
    end_time: Optional[float] = Field(None, description="结束时间(秒)")
    confidence: Optional[float] = Field(None, description="置信度")


# 服务注册表
ASR_SERVICE_REGISTRY = {}

def register_asr_service(name: str):
    """
    ASR服务注册装饰器
    
    Args:
        name: 服务名称
    """
    def decorator(cls):
        ASR_SERVICE_REGISTRY[name] = cls
        logger.info(f"ASR服务已注册: {name} -> {cls.__name__}")
        return cls
    return decorator


class ASRDialectService(ABC):
    """
    ASR方言识别服务抽象基类
    定义了所有ASR服务必须实现的接口
    """
    
    def __init__(self, sample_rate: int = 16000, output_dir: str = "output"):
        """
        初始化ASR服务
        
        Args:
            sample_rate: 采样率，默认16000Hz
            output_dir: 输出目录
        """
        self.sample_rate = sample_rate
        self.output_dir = output_dir
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    @abstractmethod
    def recognize_audio(self, audio_file: str) -> List[ASRRecognitionSegment]:
        """
        识别音频文件 - 抽象方法
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            List[ASRRecognitionSegment]: 识别结果段落列表
        """
        pass
    
    @abstractmethod
    def batch_recognize(self, audio_files: List[str]) -> List[List[ASRRecognitionSegment]]:
        """
        批量识别音频文件 - 抽象方法
        
        Args:
            audio_files: 音频文件路径列表
            
        Returns:
            List[List[ASRRecognitionSegment]]: 批量识别结果
        """
        pass
    
    @abstractmethod
    def ping(self) -> bool:
        """
        检查服务是否可用 - 抽象方法
        
        Returns:
            bool: 服务是否可用
        """
        pass
    
    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取服务信息 - 抽象方法
        
        Returns:
            Dict[str, Any]: 服务信息
        """
        pass


# 全局服务实例缓存
ASR_SERVICE_INSTANCES = {}

# 配置重试次数
ASR_PING_RETRY_COUNT = 3


def create_asr_service(service_name: str = "funasr", **kwargs) -> ASRDialectService:
    """
    根据服务名称创建ASR服务实例，优先使用缓存实例
    
    Args:
        service_name: 服务名称
        **kwargs: 服务初始化参数
        
    Returns:
        ASRDialectService: ASR服务实例
        
    Raises:
        ValueError: 服务未注册或不可用
    """
    if service_name not in ASR_SERVICE_REGISTRY:
        raise ValueError(f"ASR服务 '{service_name}' 未注册")
    
    # 优先使用缓存的服务实例
    if service_name in ASR_SERVICE_INSTANCES:
        cached_instance = ASR_SERVICE_INSTANCES[service_name]
        try:
            if cached_instance.ping():
                logger.debug(f"使用缓存的ASR服务实例: {service_name}")
                return cached_instance
            else:
                logger.warning(f"缓存的ASR服务实例 {service_name} ping失败，将重新创建")
                del ASR_SERVICE_INSTANCES[service_name]
        except Exception as e:
            logger.warning(f"缓存的ASR服务实例 {service_name} ping异常: {e}，将重新创建")
            del ASR_SERVICE_INSTANCES[service_name]
    
    # 创建新的服务实例
    service_class = ASR_SERVICE_REGISTRY[service_name]
    service_instance = service_class(**kwargs)
    
    # 缓存服务实例
    ASR_SERVICE_INSTANCES[service_name] = service_instance
    
    logger.info(f"创建新的ASR服务实例: {service_name}")
    return service_instance


def get_available_asr_services() -> List[str]:
    """
    获取所有可用的ASR服务列表，带重试机制
    
    Returns:
        List[str]: 可用的ASR服务名称列表
    """
    available_services = []
    
    for name, service_class in ASR_SERVICE_REGISTRY.items():
        service_available = False
        
        # 检查是否有缓存的实例
        if name in ASR_SERVICE_INSTANCES:
            service_instance = ASR_SERVICE_INSTANCES[name]
            
            # 尝试ping缓存的实例，带重试机制
            for retry in range(ASR_PING_RETRY_COUNT):
                try:
                    if service_instance.ping():
                        service_available = True
                        logger.debug(f"ASR服务 '{name}' 缓存实例ping成功 (重试 {retry + 1}/{ASR_PING_RETRY_COUNT})")
                        break
                    else:
                        logger.warning(f"ASR服务 '{name}' 缓存实例ping失败 (重试 {retry + 1}/{ASR_PING_RETRY_COUNT})")
                except Exception as e:
                    logger.warning(f"ASR服务 '{name}' 缓存实例ping异常: {e} (重试 {retry + 1}/{ASR_PING_RETRY_COUNT})")
                
                # 如果不是最后一次重试，重新创建实例
                if retry < ASR_PING_RETRY_COUNT - 1:
                    try:
                        logger.info(f"重新创建ASR服务实例: {name}")
                        service_instance = service_class()
                        ASR_SERVICE_INSTANCES[name] = service_instance
                    except Exception as e:
                        logger.error(f"重新创建ASR服务实例 '{name}' 失败: {e}")
                        break
        else:
            # 没有缓存实例，尝试创建新实例并ping
            for retry in range(ASR_PING_RETRY_COUNT):
                try:
                    service_instance = service_class()
                    if service_instance.ping():
                        ASR_SERVICE_INSTANCES[name] = service_instance
                        service_available = True
                        logger.debug(f"ASR服务 '{name}' 新实例创建并ping成功 (重试 {retry + 1}/{ASR_PING_RETRY_COUNT})")
                        break
                    else:
                        logger.warning(f"ASR服务 '{name}' 新实例ping失败 (重试 {retry + 1}/{ASR_PING_RETRY_COUNT})")
                except Exception as e:
                    logger.warning(f"ASR服务 '{name}' 创建或ping异常: {e} (重试 {retry + 1}/{ASR_PING_RETRY_COUNT})")
        
        if service_available:
            available_services.append(name)
        else:
            # 清理失败的缓存实例
            if name in ASR_SERVICE_INSTANCES:
                del ASR_SERVICE_INSTANCES[name]
                logger.info(f"清理失败的ASR服务缓存实例: {name}")
    
    return available_services


def get_registered_asr_services() -> Dict[str, type]:
    """
    获取所有已注册的ASR服务
    
    Returns:
        Dict[str, type]: 已注册的ASR服务字典
    """
    return ASR_SERVICE_REGISTRY.copy()


# 导入服务实现以确保装饰器注册生效
from services.asr import *
from services.summary import *
