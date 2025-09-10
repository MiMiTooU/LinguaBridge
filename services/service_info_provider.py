"""
服务信息提供器实现
负责提供ASR和LLM服务的详细信息
"""
import logging
from typing import Dict, Any, List
from services.asr_dialect import get_available_asr_services, get_registered_asr_services
from services.llm_summary import (
    get_available_llm_services, 
    get_registered_llm_services,
    get_registered_llm_service_instances,
    get_available_llm_service_instances,
    get_summary_service
)

logger = logging.getLogger(__name__)


class ServiceInfoProvider:
    """服务信息提供器"""
    
    def __init__(self, default_llm_service_name: str = "baidu_wenxin"):
        self.default_llm_service_name = default_llm_service_name
    
    def get_all_services_info(self, startup_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取所有可用服务信息
        
        Args:
            startup_info: 启动时的服务初始化结果
            
        Returns:
            dict: 包含所有服务信息的字典
        """
        # 获取ASR服务信息
        asr_services = get_available_asr_services()
        
        # 获取LLM服务信息
        llm_services = get_available_llm_services()
        
        response = {
            "asr_services": asr_services,
            "llm_services": llm_services,
            "total_services": len(asr_services) + len(llm_services)
        }
        
        # 如果有启动信息，添加到响应中
        if startup_info:
            response["startup_info"] = {
                "total_services_at_startup": startup_info["total_services"],
                "successful_services_at_startup": startup_info["successful_services"],
                "failed_services_at_startup": startup_info["failed_services"],
                "startup_errors": startup_info["startup_errors"]
            }
        
        return response
    
    def get_asr_services_info(self) -> Dict[str, Any]:
        """
        获取ASR服务信息
        
        Returns:
            dict: 已注册和可用的ASR服务信息
        """
        registered_services = get_registered_asr_services()
        available_services = get_available_asr_services()
        
        return {
            "success": True,
            "registered_services": list(registered_services.keys()),
            "available_services": available_services,
            "default_service": "funasr"
        }
    
    def get_llm_services_info(self) -> Dict[str, Any]:
        """
        获取LLM总结服务信息
        
        Returns:
            dict: 已注册和可用的LLM服务信息
        """
        registered_services = get_registered_llm_services()
        available_services = get_available_llm_services()
        
        # 获取已注册的服务实例信息
        registered_instances = get_registered_llm_service_instances()
        available_instances = get_available_llm_service_instances()
        
        # 获取默认服务的详细信息
        default_service_info = None
        try:
            default_service = get_summary_service()
            default_service_info = default_service.get_service_info()
        except Exception as e:
            logger.warning(f"获取默认服务信息失败: {e}")
        
        return {
            "success": True,
            "registered_services": list(registered_services.keys()),
            "available_services": available_services,
            "registered_instances": list(registered_instances.keys()),
            "available_instances": available_instances,
            "default_service": self.default_llm_service_name,
            "default_service_info": default_service_info
        }
