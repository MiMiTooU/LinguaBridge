from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
import os
import tempfile
import logging
from pathlib import Path
from services.asr_dialect import (
    create_asr_service,
    get_available_asr_services,
    get_registered_asr_services
)
from services.audio_recoder import AudioTranscoder
from services.llm_summary import (
    create_default_llm_service,
    get_available_llm_services,
    get_registered_llm_services,
    get_llm_service_instance,
    get_registered_llm_service_instances,
    get_available_llm_service_instances,
    create_and_register_llm_service,
    get_summary_service
)
from services.audio_processor import AudioProcessor
from services.service_health_checker import ServiceHealthChecker
from services.service_info_provider import ServiceInfoProvider

# 创建路由器
router = APIRouter(prefix="/api")

# 设置日志
logger = logging.getLogger(__name__)

# 总结类型枚举
class SummaryType(str, Enum):
    GENERAL = "general"
    KEY_POINTS = "key_points"
    BRIEF = "brief"

# 默认服务名称
DEFAULT_LLM_SERVICE_NAME = "baidu_wenxin"

# 创建服务实例
audio_processor = AudioProcessor()
health_checker = ServiceHealthChecker()
info_provider = ServiceInfoProvider(DEFAULT_LLM_SERVICE_NAME)


# 请求模型定义
class SummaryRequest(BaseModel):
    text: str
    summary_type: SummaryType = SummaryType.GENERAL
    max_length: Optional[int] = None
    service_name: Optional[str] = DEFAULT_LLM_SERVICE_NAME

class BatchSummaryRequest(BaseModel):
    texts: List[str]
    summary_type: SummaryType = SummaryType.GENERAL
    service_name: Optional[str] = DEFAULT_LLM_SERVICE_NAME

# 响应模型定义
class SummaryResult(BaseModel):
    success: bool
    summary: Optional[str] = None
    original_text: Optional[str] = None
    summary_type: Optional[str] = None
    max_length: Optional[int] = None
    model: Optional[str] = None
    original_length: Optional[int] = None
    summary_length: Optional[int] = None
    error: Optional[str] = None

class ASRResult(BaseModel):
    success: bool
    text: Optional[str] = None
    original_file: Optional[str] = None
    transcoded_file: Optional[str] = None
    mode: Optional[str] = None
    sample_rate: Optional[int] = None
    wav_params: Optional[Dict[str, Any]] = None
    client_output: Optional[str] = None
    error: Optional[str] = None

class AudioUploadResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    original_file: Optional[str] = None
    transcoded_file: Optional[str] = None
    mode: Optional[str] = None
    sample_rate: Optional[int] = None
    wav_params: Optional[Dict[str, Any]] = None
    client_output: Optional[str] = None
    uploaded_filename: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    summary_enabled: bool = False
    summary_result: Optional[SummaryResult] = None
    error: Optional[str] = None

class ModelsResponse(BaseModel):
    success: bool
    models: List[str]
    default_model: str
    service: str = "FunASR WebSocket"


class BatchSummaryResponse(BaseModel):
    success: bool
    results: List[SummaryResult]
    total_count: int
    success_count: int


@router.post("/upload-audio", response_model=AudioUploadResponse, tags=["audio"])
async def upload_audio_file(
    file: UploadFile = File(...),
    model: Optional[str] = "funasr",
    enable_summary: bool = False,
    summary_type: SummaryType = SummaryType.GENERAL,
    max_length: Optional[int] = None,
    summary_service: Optional[str] = DEFAULT_LLM_SERVICE_NAME
) -> AudioUploadResponse:
    """
    上传音频文件并进行ASR识别，可选择是否进行文本总结
    
    Args:
        file: 上传的音频文件
        model: ASR服务名称，默认funasr
        enable_summary: 是否启用文本总结，默认False
        summary_type: 总结类型，默认general
        max_length: 总结最大长度，可选
        summary_service: 总结服务名称，可选
    
    Returns:
        dict: ASR识别结果，如果启用总结则包含总结结果
    """
    # 验证音频文件
    audio_processor.validate_audio_file(file, max_size_mb=500)
    
    # 执行音频处理流程
    # 步骤1: 音频转码
    temp_file_path, transcoded_file = await audio_processor.transcode_audio(file)
    
    # 步骤2: 音频识别（包含文件清理）
    recognition_result = audio_processor.recognize_audio(temp_file_path, transcoded_file, model, file)
    
    # 步骤3: 音频总结
    final_result = audio_processor.summarize_audio(
        recognition_result, enable_summary, summary_type.value, max_length, 
        summary_service or DEFAULT_LLM_SERVICE_NAME
    )
    
    return AudioUploadResponse(**final_result)


# 服务信息端点
@router.get("/services")
async def get_services(request):
    """获取所有可用服务信息"""
    try:
        # 获取启动时的服务初始化结果
        startup_info = getattr(request.app.state, 'service_init_result', None)
        
        return info_provider.get_all_services_info(startup_info)
    except Exception as e:
        logger.error(f"获取服务信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务信息失败: {e}")

@router.get("/asr-services", tags=["audio"])
async def get_asr_services():
    """
    获取ASR服务信息
    
    Returns:
        dict: 已注册和可用的ASR服务信息
    """
    try:
        return info_provider.get_asr_services_info()
    except Exception as e:
        logger.error(f"获取ASR服务信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务信息失败: {str(e)}")

@router.get("/services/health", tags=["system"])
async def check_services_health():
    """
    检查所有服务的健康状态
    
    Returns:
        dict: 服务健康状态信息
    """
    try:
        return health_checker.check_all_services_health()
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")




@router.post("/summarize", response_model=SummaryResult, tags=["summary"])
async def summarize_text(request: SummaryRequest) -> SummaryResult:
    """
    对文本进行总结
    
    Args:
        request: 总结请求，包含文本、总结类型、最大长度和服务名称
    
    Returns:
        dict: 总结结果
    """
    service = get_summary_service(request.service_name or DEFAULT_LLM_SERVICE_NAME)
    result = service.summarize_text(
        text=request.text,
        summary_type=request.summary_type.value,
        max_length=request.max_length
    )
    return result


@router.post("/batch-summarize", response_model=BatchSummaryResponse, tags=["summary"])
async def batch_summarize_texts(request: BatchSummaryRequest) -> BatchSummaryResponse:
    """
    批量总结文本
    
    Args:
        request: 批量总结请求，包含文本列表、总结类型和服务名称
    
    Returns:
        dict: 批量总结结果
    """
    service = get_summary_service(request.service_name or DEFAULT_LLM_SERVICE_NAME)
    results = service.batch_summarize(
        texts=request.texts,
        summary_type=request.summary_type.value
    )
    return BatchSummaryResponse(
        success=True,
        results=[SummaryResult(**r) for r in results],
        total_count=len(results),
        success_count=sum(1 for r in results if r.get("success", False))
    )



@router.get("/summary-models", tags=["summary"])
async def get_summary_models():
    """
    获取LLM总结服务信息
    
    Returns:
        dict: 已注册和可用的LLM服务信息
    """
    try:
        return info_provider.get_llm_services_info()
    except Exception as e:
        logger.error(f"获取LLM服务信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取服务信息失败: {str(e)}")



