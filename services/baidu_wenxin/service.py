"""
百度文心大模型总结服务实现
基于LangChain的百度文心集成
"""
import logging
from typing import List, Dict, Any, Optional

from services.llm_summary import LLMSummaryService, register_llm_service
from .config import (
    get_baidu_api_key, get_baidu_secret_key, get_model_name,
    get_temperature, get_top_p, get_penalty_score, get_max_length
)
from .constants import (
    SUPPORTED_MODELS, SERVICE_NAME, SERVICE_VERSION, SERVICE_DESCRIPTION
)
from .utils import (
    validate_text_input, validate_batch_input, get_summary_prompt,
    format_summary_result, create_error_result, retry_on_failure,
    get_available_summary_types
)

logger = logging.getLogger(__name__)


@register_llm_service("baidu_wenxin")
class BaiduWenxinSummaryService(LLMSummaryService):
    """百度文心总结服务实现"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None, 
                 model_name: Optional[str] = None):
        """
        初始化百度文心服务
        
        Args:
            api_key: 百度API密钥，None时从环境变量获取
            secret_key: 百度Secret密钥，None时从环境变量获取
            model_name: 模型名称，None时从环境变量获取
        """
        self.api_key = api_key or get_baidu_api_key()
        self.secret_key = secret_key or get_baidu_secret_key()
        self.model_name = model_name or get_model_name()
        self.temperature = get_temperature()
        self.top_p = get_top_p()
        self.penalty_score = get_penalty_score()
        self.max_length = get_max_length()
        self.llm = None
        
        logger.info(f"百度文心服务初始化，模型: {self.model_name}")
    
    def _load_model(self):
        """懒加载LangChain模型"""
        if self.llm is None:
            try:
                from langchain_community.llms import QianfanLLMEndpoint
                
                self.llm = QianfanLLMEndpoint(
                    qianfan_ak=self.api_key,
                    qianfan_sk=self.secret_key,
                    model=self.model_name,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    penalty_score=self.penalty_score
                )
                logger.info(f"百度文心模型加载成功: {self.model_name}")
            except Exception as e:
                logger.error(f"百度文心模型加载失败: {e}")
                raise
    
    def ping(self) -> bool:
        """检查百度文心服务是否可用"""
        try:
            self._load_model()
            # 使用简单的测试文本进行ping
            test_result = self.llm.invoke("测试连接")
            return bool(test_result and len(test_result.strip()) > 0)
        except Exception as e:
            logger.error(f"百度文心服务ping失败: {e}")
            return False
    
    def summarize_text(self, text: str, summary_type: str = "general", 
                      max_length: Optional[int] = None) -> str:
        """
        总结单个文本
        
        Args:
            text: 要总结的文本
            summary_type: 总结类型
            max_length: 最大长度限制
            
        Returns:
            str: 总结结果
        """
        if not validate_text_input(text):
            return create_error_result("输入文本无效")
        
        try:
            self._load_model()
            
            # 获取提示词
            prompt = get_summary_prompt(summary_type, text)
            
            # 调用模型进行总结
            @retry_on_failure
            def _summarize():
                return self.llm.invoke(prompt)
            
            result = _summarize()
            
            # 格式化结果
            max_len = max_length or self.max_length
            return format_summary_result(result, summary_type, max_len)
            
        except Exception as e:
            logger.error(f"文本总结失败: {e}")
            return create_error_result(str(e))
    
    def batch_summarize(self, texts: List[str], summary_type: str = "general", 
                       max_length: Optional[int] = None) -> List[str]:
        """
        批量总结文本
        
        Args:
            texts: 要总结的文本列表
            summary_type: 总结类型
            max_length: 最大长度限制
            
        Returns:
            List[str]: 总结结果列表
        """
        if not validate_batch_input(texts):
            return [create_error_result("批量输入无效")]
        
        results = []
        for text in texts:
            try:
                result = self.summarize_text(text, summary_type, max_length)
                results.append(result)
            except Exception as e:
                logger.error(f"批量总结单个文本失败: {e}")
                results.append(create_error_result(str(e)))
        
        return results
    
    def get_supported_types(self) -> List[str]:
        """获取支持的总结类型"""
        return list(get_available_summary_types().keys())
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service_name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "model_name": self.model_name,
            "supported_models": SUPPORTED_MODELS,
            "supported_types": self.get_supported_types(),
            "type_descriptions": get_available_summary_types(),
            "max_length": self.max_length,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "penalty_score": self.penalty_score,
            "description": SERVICE_DESCRIPTION
        }
