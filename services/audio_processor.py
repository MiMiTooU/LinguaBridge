"""
音频处理服务实现
负责音频文件的上传、转码、识别和总结等功能
"""
import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import UploadFile, HTTPException

from services.audio_recoder import AudioTranscoder
from services.asr_dialect import create_asr_service
from services.llm_summary import get_summary_service

logger = logging.getLogger(__name__)


class AudioProcessor:
    """音频处理服务类"""
    
    def __init__(self):
        self.transcoder = AudioTranscoder()
        self.default_wav_params = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "codec": "pcm_s16le"
        }
    
    async def transcode_audio(self, file: UploadFile) -> tuple[str, str]:
        """
        处理音频文件上传和转码
        
        Args:
            file: 上传的音频文件
            
        Returns:
            tuple: (原始文件路径, 转码后文件路径)
        """
        # 获取文件扩展名
        file_extension = Path(file.filename).suffix if file.filename else '.tmp'
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # 读取并保存上传的文件内容
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # 音频转码为WAV格式
        transcoded_file = self.transcoder.transcode_to_wav(temp_file_path, self.default_wav_params)
        
        return temp_file_path, transcoded_file
    
    def recognize_audio(self, temp_file_path: str, transcoded_file_path: str, 
                       model: str, file: UploadFile) -> Dict[str, Any]:
        """
        执行音频识别并清理临时文件
        
        Args:
            temp_file_path: 原始临时文件路径
            transcoded_file_path: 转码后文件路径
            model: ASR模型名称
            file: 原始上传文件对象
            
        Returns:
            dict: 识别结果
        """
        try:
            # 调用ASR服务进行识别
            current_asr_service = create_asr_service(model)
            recognition_segments = current_asr_service.recognize_audio(transcoded_file_path)
            
            # 构建兼容的返回格式
            recognition_result = {
                "success": True,
                "segments": [segment.dict() for segment in recognition_segments],
                "text": " ".join([segment.text for segment in recognition_segments]),
                "uploaded_filename": file.filename,
                "file_size": file.size,
                "content_type": file.content_type
            }
            
            return recognition_result
        finally:
            # 清理临时文件
            self._cleanup_temp_files(temp_file_path, transcoded_file_path)
    
    def summarize_audio(self, recognition_result: Dict[str, Any], enable_summary: bool,
                       summary_type: str, max_length: Optional[int], 
                       summary_service: str) -> Dict[str, Any]:
        """
        执行音频识别结果的文本总结
        
        Args:
            recognition_result: 识别结果
            enable_summary: 是否启用总结
            summary_type: 总结类型
            max_length: 总结最大长度
            summary_service: 总结服务名称
            
        Returns:
            dict: 包含总结结果的完整结果
        """
        # 检查是否启用总结
        if not enable_summary:
            recognition_result["summary_enabled"] = False
            return recognition_result
        
        # 检查识别是否成功
        if not recognition_result.get("success", False):
            recognition_result["summary_enabled"] = False
            return recognition_result
        
        # 检查识别文本是否为空
        recognized_text = recognition_result.get("text", "")
        if not recognized_text.strip():
            recognition_result["summary_result"] = {
                "success": False,
                "error": "ASR识别结果为空，无法进行总结"
            }
            recognition_result["summary_enabled"] = True
            return recognition_result
        
        # 执行文本总结
        try:
            summary_service_instance = get_summary_service(summary_service)
            summary_result = summary_service_instance.summarize_text(
                text=recognized_text,
                summary_type=summary_type,
                max_length=max_length
            )
            recognition_result["summary_result"] = summary_result
            recognition_result["summary_enabled"] = True
        except Exception as e:
            logger.error(f"文本总结失败: {e}")
            recognition_result["summary_result"] = {
                "success": False,
                "error": f"文本总结失败: {str(e)}"
            }
            recognition_result["summary_enabled"] = True
        
        return recognition_result
    
    def _cleanup_temp_files(self, temp_file_path: str, transcoded_file_path: str):
        """清理临时文件"""
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"已清理原始临时文件: {temp_file_path}")
            except Exception as e:
                logger.warning(f"清理原始临时文件失败 {temp_file_path}: {e}")
        
        if transcoded_file_path and os.path.exists(transcoded_file_path):
            try:
                os.unlink(transcoded_file_path)
                logger.debug(f"已清理转码文件: {transcoded_file_path}")
            except Exception as e:
                logger.warning(f"清理转码文件失败 {transcoded_file_path}: {e}")
    
    def validate_audio_file(self, file: UploadFile, max_size_mb: int = 500):
        """
        验证音频文件类型和大小
        
        Args:
            file: 上传的文件
            max_size_mb: 最大文件大小(MB)
            
        Raises:
            HTTPException: 文件验证失败时抛出
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
        
        # 检查文件大小
        max_size = max_size_mb * 1024 * 1024
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"文件太大，最大允许{max_size_mb}MB，当前文件: {file.size / 1024 / 1024:.2f}MB"
            )
