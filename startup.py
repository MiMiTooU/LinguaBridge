#!/usr/bin/env python3
"""
LinguaBridge服务启动初始化模块
负责在应用启动时预加载所有注册的服务
"""

import logging
import asyncio
from typing import Dict, Any, List
from services.asr_dialect import (
    get_registered_asr_services,
    create_asr_service
)
from services.llm_summary import (
    get_registered_llm_services,
    create_and_register_llm_service,
    get_registered_llm_service_instances
)

logger = logging.getLogger(__name__)

class ServiceLoader:
    """服务加载器，负责预加载所有注册的服务"""
    
    def __init__(self):
        self.loaded_asr_services = {}
        self.loaded_llm_services = {}
        self.startup_errors = []
    
    async def initialize_all_services(self) -> Dict[str, Any]:
        """
        初始化所有注册的服务
        
        Returns:
            Dict[str, Any]: 初始化结果统计
        """
        logger.info("开始初始化所有注册的服务...")
        
        # 并行初始化ASR和LLM服务
        asr_task = asyncio.create_task(self._initialize_asr_services())
        llm_task = asyncio.create_task(self._initialize_llm_services())
        
        asr_results, llm_results = await asyncio.gather(asr_task, llm_task)
        
        # 汇总结果
        total_services = len(asr_results) + len(llm_results)
        successful_services = sum(1 for r in asr_results.values() if r['success']) + \
                            sum(1 for r in llm_results.values() if r['success'])
        
        result = {
            "total_services": total_services,
            "successful_services": successful_services,
            "failed_services": total_services - successful_services,
            "asr_services": asr_results,
            "llm_services": llm_results,
            "startup_errors": self.startup_errors
        }
        
        logger.info(f"服务初始化完成: {successful_services}/{total_services} 成功")
        if self.startup_errors:
            logger.warning(f"启动过程中发生 {len(self.startup_errors)} 个错误")
        
        return result
    
    async def _initialize_asr_services(self) -> Dict[str, Dict[str, Any]]:
        """初始化ASR服务"""
        logger.info("初始化ASR服务...")
        registered_services = get_registered_asr_services()
        results = {}
        
        for service_name, service_class in registered_services.items():
            try:
                logger.debug(f"正在初始化ASR服务: {service_name}")
                
                # 创建服务实例
                service_instance = create_asr_service(service_name)
                
                # 执行健康检查
                is_healthy = service_instance.ping()
                
                if is_healthy:
                    self.loaded_asr_services[service_name] = service_instance
                    service_info = service_instance.get_service_info()
                    results[service_name] = {
                        "success": True,
                        "service_info": service_info,
                        "message": f"ASR服务 {service_name} 初始化成功"
                    }
                    logger.info(f"ASR服务 {service_name} 初始化成功")
                else:
                    results[service_name] = {
                        "success": False,
                        "error": f"ASR服务 {service_name} 健康检查失败",
                        "message": f"ASR服务 {service_name} 不可用"
                    }
                    logger.warning(f"ASR服务 {service_name} 健康检查失败")
                    
            except Exception as e:
                error_msg = f"ASR服务 {service_name} 初始化失败: {e}"
                results[service_name] = {
                    "success": False,
                    "error": str(e),
                    "message": error_msg
                }
                self.startup_errors.append(error_msg)
                logger.error(error_msg)
        
        return results
    
    async def _initialize_llm_services(self) -> Dict[str, Dict[str, Any]]:
        """初始化LLM服务"""
        logger.info("初始化LLM服务...")
        registered_services = get_registered_llm_services()
        results = {}
        
        for service_name, service_class in registered_services.items():
            try:
                logger.debug(f"正在初始化LLM服务: {service_name}")
                
                # 检查是否已经有实例存在
                existing_instances = get_registered_llm_service_instances()
                if service_name in existing_instances:
                    logger.debug(f"LLM服务 {service_name} 实例已存在，跳过创建")
                    service_instance = existing_instances[service_name]
                else:
                    # 创建并注册服务实例
                    service_instance = create_and_register_llm_service(service_name)
                
                # 执行健康检查
                is_healthy = service_instance.ping()
                
                if is_healthy:
                    self.loaded_llm_services[service_name] = service_instance
                    service_info = service_instance.get_service_info()
                    results[service_name] = {
                        "success": True,
                        "service_info": service_info,
                        "message": f"LLM服务 {service_name} 初始化成功"
                    }
                    logger.info(f"LLM服务 {service_name} 初始化成功")
                else:
                    results[service_name] = {
                        "success": False,
                        "error": f"LLM服务 {service_name} 健康检查失败",
                        "message": f"LLM服务 {service_name} 不可用"
                    }
                    logger.warning(f"LLM服务 {service_name} 健康检查失败")
                    
            except Exception as e:
                error_msg = f"LLM服务 {service_name} 初始化失败: {e}"
                results[service_name] = {
                    "success": False,
                    "error": str(e),
                    "message": error_msg
                }
                self.startup_errors.append(error_msg)
                logger.error(error_msg)
        
        return results
    
    def get_loaded_services(self) -> Dict[str, Any]:
        """获取已加载的服务信息"""
        return {
            "asr_services": list(self.loaded_asr_services.keys()),
            "llm_services": list(self.loaded_llm_services.keys()),
            "total_loaded": len(self.loaded_asr_services) + len(self.loaded_llm_services)
        }


# 全局服务加载器实例
service_loader = ServiceLoader()


async def initialize_services() -> Dict[str, Any]:
    """
    初始化所有服务的入口函数
    
    Returns:
        Dict[str, Any]: 初始化结果
    """
    return await service_loader.initialize_all_services()


def get_service_loader() -> ServiceLoader:
    """获取服务加载器实例"""
    return service_loader


# 同步版本的初始化函数，用于非异步环境
def initialize_services_sync() -> Dict[str, Any]:
    """
    同步版本的服务初始化函数
    
    Returns:
        Dict[str, Any]: 初始化结果
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(initialize_services())


if __name__ == "__main__":
    # 测试服务加载
    import sys
    import os
    
    # 添加项目根目录到路径
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # 初始化日志
    logging.basicConfig(level=logging.INFO)
    
    # 运行服务初始化
    result = initialize_services_sync()
    print("服务初始化结果:")
    print(f"总服务数: {result['total_services']}")
    print(f"成功服务数: {result['successful_services']}")
    print(f"失败服务数: {result['failed_services']}")
    
    if result['startup_errors']:
        print("启动错误:")
        for error in result['startup_errors']:
            print(f"  - {error}")
