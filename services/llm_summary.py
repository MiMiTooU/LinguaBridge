import os
import logging
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Type
from pathlib import Path
from langchain_community.chat_models import QianfanChatEndpoint
from langchain.schema import BaseMessage, HumanMessage
from langchain.prompts import PromptTemplate


# LLM服务注册表
LLM_SERVICE_REGISTRY = {}

# LLM服务实例注册表 - 存储初始化后的服务实例
LLM_SERVICE_INSTANCES = {}

def register_llm_service(name: str, service_class: Type['LLMSummaryService'] = None):
    """
    注册LLM服务
    可以作为装饰器使用或直接调用
    
    Args:
        name: 服务名称
        service_class: 服务类（装饰器模式时为None）
    
    Returns:
        装饰器函数或None
    """
    def decorator(cls: Type['LLMSummaryService']):
        LLM_SERVICE_REGISTRY[name] = cls
        return cls
    
    if service_class is None:
        # 装饰器模式
        return decorator
    else:
        # 直接调用模式
        LLM_SERVICE_REGISTRY[name] = service_class

def get_registered_llm_services() -> Dict[str, Type['LLMSummaryService']]:
    """获取已注册的LLM服务"""
    return LLM_SERVICE_REGISTRY.copy()

def get_available_llm_services() -> List[str]:
    """获取可用的LLM服务列表（经过ping检查）"""
    available_services = []
    for name, service_class in LLM_SERVICE_REGISTRY.items():
        try:
            # 创建临时实例进行ping检查
            temp_service = service_class()
            if temp_service.ping():
                available_services.append(name)
        except Exception as e:
            logging.getLogger(__name__).warning(f"LLM服务 {name} 不可用: {e}")
    return available_services

def register_llm_service_instance(name: str, service_instance: 'LLMSummaryService'):
    """注册LLM服务实例"""
    LLM_SERVICE_INSTANCES[name] = service_instance
    logging.getLogger(__name__).info(f"LLM服务实例 '{name}' 注册成功")

def get_llm_service_instance(name: str) -> Optional['LLMSummaryService']:
    """获取已注册的LLM服务实例"""
    return LLM_SERVICE_INSTANCES.get(name)

def get_registered_llm_service_instances() -> Dict[str, 'LLMSummaryService']:
    """获取所有已注册的LLM服务实例"""
    return LLM_SERVICE_INSTANCES.copy()

def get_available_llm_service_instances() -> List[str]:
    """获取可用的LLM服务实例列表（经过ping检查）"""
    available_instances = []
    for name, service_instance in LLM_SERVICE_INSTANCES.items():
        try:
            if service_instance.ping():
                available_instances.append(name)
        except Exception as e:
            logging.getLogger(__name__).warning(f"LLM服务实例 {name} 不可用: {e}")
    return available_instances

def remove_llm_service_instance(name: str) -> bool:
    """移除LLM服务实例"""
    if name in LLM_SERVICE_INSTANCES:
        del LLM_SERVICE_INSTANCES[name]
        logging.getLogger(__name__).info(f"LLM服务实例 '{name}' 已移除")
        return True
    return False

class LLMSummaryService(ABC):
    """
    大模型文本总结服务抽象基类
    定义文本总结服务的标准接口
    """
    
    def __init__(self, 
                 max_tokens: int = 1000,
                 temperature: float = 0.3):
        """
        初始化LLM总结服务基类
        
        Args:
            max_tokens: 最大生成token数
            temperature: 生成温度，控制随机性
        """
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def summarize_text(self, 
                      text: str, 
                      summary_type: str = "general",
                      max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        对文本进行总结 - 抽象方法
        
        Args:
            text: 待总结的文本
            summary_type: 总结类型 (general/key_points/brief)
            max_length: 总结最大长度
        
        Returns:
            Dict[str, Any]: 总结结果
        """
        pass
    
    @abstractmethod
    def batch_summarize(self, 
                       texts: list,
                       summary_type: str = "general") -> list:
        """
        批量总结文本 - 抽象方法
        
        Args:
            texts: 待总结的文本列表
            summary_type: 总结类型
        
        Returns:
            list: 批量总结结果
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


# 使用装饰器注册百度文心服务
@register_llm_service("baidu_wenxin")
class BaiduWenxinSummaryService(LLMSummaryService):
    """
    基于百度文心大模型的文本总结服务实现
    使用LangChain集成百度千帆平台
    """
    
    def __init__(self,
                 api_key: str,
                 secret_key: str,
                 model_name: str = "ERNIE-Bot-turbo",
                 max_tokens: int = 1000,
                 temperature: float = 0.3,
                 prompt_config_path: Optional[str] = None):
        """
        初始化百度文心总结服务
        
        Args:
            api_key: 百度千帆API Key
            secret_key: 百度千帆Secret Key
            model_name: 模型名称
            max_tokens: 最大生成token数
            temperature: 生成温度
            prompt_config_path: 提示词配置文件路径
        """
        super().__init__(max_tokens=max_tokens, temperature=temperature)
        
        self.api_key = api_key
        self.secret_key = secret_key
        self.model_name = model_name
        
        # 初始化百度千帆LLM
        self.llm = QianfanChatEndpoint(
            api_key=api_key,
            secret_key=secret_key,
            model=model_name,
            temperature=temperature,
            timeout=30
        )
        
        # 加载提示词配置
        self.summary_prompts = self._load_prompt_config(prompt_config_path)
        self.summary_types_config = self._load_summary_types_config(prompt_config_path)
    
    def _load_prompt_config(self, config_path: Optional[str] = None) -> Dict[str, PromptTemplate]:
        """
        加载提示词配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, PromptTemplate]: 提示词模板字典
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "prompts.json"
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"提示词配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        prompts = {}
        for prompt_type, prompt_config in config["summary_prompts"].items():
            prompts[prompt_type] = PromptTemplate(
                input_variables=prompt_config["input_variables"],
                template=prompt_config["template"]
            )
        
        return prompts
    
    def _load_summary_types_config(self, config_path: Optional[str] = None) -> list:
        """
        加载总结类型配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            list: 总结类型配置列表
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "prompts.json"
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"提示词配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return config["summary_types"]
    
    def _get_max_length_instruction(self, max_length: Optional[int]) -> str:
        """
        生成长度限制指令
        
        Args:
            max_length: 最大长度
            
        Returns:
            str: 长度限制指令
        """
        if max_length:
            return f"，控制在{max_length}字以内"
        return ""
    
    def summarize_text(self, 
                      text: str, 
                      summary_type: str = "general",
                      max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        对文本进行总结
        
        Args:
            text: 待总结的文本
            summary_type: 总结类型 (general/key_points/brief)
            max_length: 总结最大长度
        
        Returns:
            Dict[str, Any]: 总结结果
        """
        if not text.strip():
            return self._create_error_result("输入文本为空", text, summary_type)
        
        if summary_type not in self.summary_prompts:
            return self._create_error_result(f"不支持的总结类型: {summary_type}", text, summary_type)
        
        self.logger.info(f"开始总结文本，类型: {summary_type}, 长度: {len(text)}")
        
        # 构建提示
        prompt = self._build_prompt(text, summary_type, max_length)
        
        # 调用大模型并处理响应
        response = self.llm.invoke(prompt)
        summary = response.content.strip()
        
        result = self._create_success_result(text, summary, summary_type, max_length)
        
        self.logger.info(f"文本总结成功，原文长度: {len(text)}, 总结长度: {len(summary)}")
        return result
    
    def _build_prompt(self, text: str, summary_type: str, max_length: Optional[int]) -> str:
        """构建总结提示"""
        prompt_template = self.summary_prompts[summary_type]
        max_length_instruction = self._get_max_length_instruction(max_length)
        
        return prompt_template.format(
            text=text,
            max_length_instruction=max_length_instruction
        )
    
    def _create_success_result(self, text: str, summary: str, summary_type: str, max_length: Optional[int]) -> Dict[str, Any]:
        """创建成功结果"""
        return {
            "success": True,
            "summary": summary,
            "original_text": text,
            "summary_type": summary_type,
            "max_length": max_length,
            "model": self.model_name,
            "original_length": len(text),
            "summary_length": len(summary)
        }
    
    def _create_error_result(self, error: str, text: str, summary_type: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "success": False,
            "error": error,
            "original_text": text,
            "summary_type": summary_type,
            "model": self.model_name
        }
    
    def batch_summarize(self, 
                       texts: list,
                       summary_type: str = "general") -> list:
        """
        批量总结文本
        
        Args:
            texts: 待总结的文本列表
            summary_type: 总结类型
        
        Returns:
            list: 批量总结结果
        """
        results = []
        
        for i, text in enumerate(texts):
            result = self._try_summarize_single(text, summary_type, i)
            results.append(result)
        
        self.logger.info(f"批量总结完成，处理 {len(results)} 个文本")
        return results
    
    def _try_summarize_single(self, text: str, summary_type: str, index: int) -> Dict[str, Any]:
        """尝试总结单个文本，失败时返回错误结果"""
        try:
            result = self.summarize_text(text, summary_type)
            result["batch_index"] = index
            return result
        except Exception as e:
            self.logger.error(f"批量总结第{index}个文本失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "batch_index": index,
                "original_text": text,
                "summary_type": summary_type
            }
    
    def ping(self) -> bool:
        """
        检查百度文心服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        try:
            # 尝试进行一个简单的测试调用
            test_text = "测试"
            test_prompt = self.summary_prompts.get("general")
            if not test_prompt:
                return False
            formatted_prompt = test_prompt.format(
                text=test_text,
                max_length_instruction="简短回复即可"
            )
            # 发送测试请求
            response = self.llm.invoke([HumanMessage(content=formatted_prompt)])
            self.logger.debug("wenxin ping response: " + response.content)
            self.logger.info("百度文心服务连接成功")
            return True
        except Exception as e:
            self.logger.warning(f"百度文心服务连接失败: {e}")
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        获取百度文心服务信息
        
        Returns:
            Dict[str, Any]: 服务信息
        """
        return {
            "name": "Baidu Wenxin",
            "type": "LLM Summary Service",
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "available": self.ping(),
            "supported_types": len(self.summary_types_config)
        }
    
    def get_supported_summary_types(self) -> list:
        """
        获取支持的总结类型
        
        Returns:
            list: 支持的总结类型列表
        """
        return self.summary_types_config


# 默认LLM服务工厂
def create_default_llm_service(**kwargs) -> LLMSummaryService:
    """
    创建默认的LLM服务实例（百度文心）
    
    Args:
        **kwargs: 服务初始化参数
        
    Returns:
        LLMSummaryService: LLM服务实例
    """
    # 从环境变量获取API密钥
    api_key = kwargs.get('api_key') or os.getenv("BAIDU_API_KEY")
    secret_key = kwargs.get('secret_key') or os.getenv("BAIDU_SECRET_KEY")
    
    if not api_key or not secret_key:
        raise ValueError("需要设置BAIDU_API_KEY和BAIDU_SECRET_KEY环境变量")
    
    return BaiduWenxinSummaryService(api_key=api_key, secret_key=secret_key, **kwargs)

def create_llm_service(service_name: str = "baidu_wenxin", **kwargs) -> LLMSummaryService:
    """
    根据服务名称创建LLM服务实例
    
    Args:
        service_name: 服务名称
        **kwargs: 服务初始化参数
        
    Returns:
        LLMSummaryService: LLM服务实例
        
    Raises:
        ValueError: 服务未注册或不可用
    """
    if service_name not in LLM_SERVICE_REGISTRY:
        raise ValueError(f"LLM服务 '{service_name}' 未注册")
    
    service_class = LLM_SERVICE_REGISTRY[service_name]
    
    # 为百度文心服务自动添加环境变量支持
    if service_name == "baidu_wenxin":
        api_key = kwargs.get('api_key') or os.getenv("BAIDU_API_KEY")
        secret_key = kwargs.get('secret_key') or os.getenv("BAIDU_SECRET_KEY")
        
        if not api_key or not secret_key:
            raise ValueError("需要设置BAIDU_API_KEY和BAIDU_SECRET_KEY环境变量")
        
        kwargs.update({'api_key': api_key, 'secret_key': secret_key})
    
    service_instance = service_class(**kwargs)
    
    if not service_instance.ping():
        raise ValueError(f"LLM服务 '{service_name}' 不可用")
    
    return service_instance

def create_and_register_llm_service(service_name: str, instance_name: Optional[str] = None, **kwargs) -> LLMSummaryService:
    """
    创建并注册LLM服务实例
    
    Args:
        service_name: 服务名称
        instance_name: 实例名称，如果为None则使用service_name
        **kwargs: 服务初始化参数
        
    Returns:
        LLMSummaryService: LLM服务实例
    """
    service_instance = create_llm_service(service_name, **kwargs)
    
    if instance_name is None:
        instance_name = service_name
    
    # 注册实例
    LLM_SERVICE_INSTANCES[instance_name] = service_instance
    
    return service_instance


def get_summary_service(service_name: str = None):
    """获取总结服务实例（支持指定服务名称）"""
    from fastapi import HTTPException
    import logging
    
    logger = logging.getLogger(__name__)
    
    if service_name is None:
        service_name = "baidu_wenxin"  # DEFAULT_LLM_SERVICE_NAME
    
    # 首先尝试从实例注册表获取
    service_instance = get_llm_service_instance(service_name)
    if service_instance is not None:
        return service_instance
    
    # 如果实例不存在，尝试创建并注册
    try:
        service_instance = create_and_register_llm_service(service_name)
        logger.info(f"LLM总结服务 '{service_name}' 初始化成功")
        return service_instance
    except Exception as e:
        logger.error(f"LLM总结服务 '{service_name}' 初始化失败: {e}")
        raise HTTPException(status_code=503, detail=f"LLM总结服务 '{service_name}' 不可用")
