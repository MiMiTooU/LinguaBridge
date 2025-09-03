from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional, Dict, Any
import os
import tempfile
from pathlib import Path
from services.asr_dialect import ASRDialectService

# 创建路由器
router = APIRouter(prefix="/api", tags=["audio"])

# 初始化ASR服务实例
asr_service = ASRDialectService()


@router.post("/upload-audio")
async def upload_audio_file(
    file: UploadFile = File(...),
    model: Optional[str] = "conformer_wenetspeech",
    sample_rate: Optional[int] = 16000
):
    """
    上传音频文件并进行ASR识别
    
    Args:
        file: 上传的音频文件
        model: ASR模型名称，默认conformer_wenetspeech
        sample_rate: 采样率，默认16000Hz
    
    Returns:
        dict: ASR识别结果
    """
    # 检查文件类型
    if not file.content_type or not file.content_type.startswith('audio/'):
        # 允许一些常见的音频文件类型
        allowed_types = [
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav',
            'audio/aac', 'audio/flac', 'audio/ogg', 'audio/webm',
            'audio/mp4', 'audio/x-m4a', 'application/octet-stream'
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file.content_type}"
            )
    
    # 检查文件大小（限制为100MB）
    max_size = 100 * 1024 * 1024  # 100MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"文件太大，最大允许100MB，当前文件: {file.size / 1024 / 1024:.2f}MB"
        )
    
    # 创建临时文件来保存上传的音频
    temp_file = None
    try:
        # 获取文件扩展名
        file_extension = Path(file.filename).suffix if file.filename else '.tmp'
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # 读取并保存上传的文件内容
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 调用ASR服务进行识别
        recognition_result = asr_service.recognize_audio(
            audio_file=temp_file_path,
            wav_params={
                "sample_rate": sample_rate,
                "channels": 1,
                "bit_depth": 16,
                "codec": "pcm_s16le"
            }
        )
        
        # 添加上传文件信息
        recognition_result.update({
            "uploaded_filename": file.filename,
            "file_size": file.size,
            "content_type": file.content_type
        })
        
        return recognition_result
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"音频处理失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        if temp_file and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"清理临时文件失败: {e}")


@router.get("/models")
async def get_supported_models():
    """
    获取支持的ASR模型列表
    
    Returns:
        dict: 支持的模型列表
    """
    try:
        models = asr_service.get_supported_models()
        return {
            "success": True,
            "models": models,
            "default_model": "conformer_wenetspeech"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取模型列表失败: {str(e)}"
        )