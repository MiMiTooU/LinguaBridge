"""
服务健康检查实现
负责检查ASR和LLM服务的健康状态
"""
import logging
from typing import Dict, Any
from services.asr_dialect import get_registered_asr_services, create_asr_service
from services.llm_summary import get_summary_service

logger = logging.getLogger(__name__)


class ServiceHealthChecker:
    """服务健康检查器"""
    
    def __init__(self):
        pass
    
    def check_all_services_health(self) -> Dict[str, Any]:
        """
        检查所有服务的健康状态
        
        Returns:
            dict: 服务健康状态信息
        """
        health_status = {}
        
        # 检查ASR服务
        health_status["asr"] = self._check_asr_services_health()
        
        # 检查LLM总结服务
        health_status["llm_summary"] = self._check_llm_summary_health()
        
        # 计算整体健康状态
        overall_health = self._calculate_overall_health(health_status)
        
        return {
            "success": True,
            "overall_health": overall_health,
            "services": health_status
        }
    
    def _check_asr_services_health(self) -> Dict[str, Any]:
        """检查ASR服务健康状态"""
        asr_health = {}
        registered_asr_services = get_registered_asr_services()
        
        for service_name in registered_asr_services.keys():
            try:
                asr_svc = create_asr_service(service_name)
                asr_health[service_name] = {
                    "available": asr_svc.ping(),
                    "service_info": asr_svc.get_service_info()
                }
            except Exception as e:
                asr_health[service_name] = {
                    "available": False,
                    "error": str(e)
                }
        
        return asr_health
    
    def _check_llm_summary_health(self) -> Dict[str, Any]:
        """检查LLM总结服务健康状态"""
        try:
            summary_svc = get_summary_service()
            return {
                "available": summary_svc.ping(),
                "service_info": summary_svc.get_service_info()
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    def _calculate_overall_health(self, health_status: Dict[str, Any]) -> bool:
        """计算整体健康状态"""
        def check_service_health(service_data):
            if isinstance(service_data, dict):
                if "available" in service_data:
                    return service_data["available"]
                else:
                    # 对于嵌套的服务（如ASR服务组）
                    return any(sub_service.get("available", False) 
                             for sub_service in service_data.values() 
                             if isinstance(sub_service, dict))
            return False
        
        return all(check_service_health(service) for service in health_status.values())
