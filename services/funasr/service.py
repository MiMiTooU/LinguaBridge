"""
FunASR服务实现
基于FunASR WebSocket客户端的ASR服务
"""
import tempfile
import logging
from typing import List, Dict, Any
from pathlib import Path

from services.asr_dialect import ASRDialectService, ASRRecognitionSegment, register_asr_service
from .config import (
    get_funasr_host, get_funasr_port, get_funasr_use_ssl,
    get_funasr_mode, get_funasr_chunk_size, get_client_script_path
)
from .constants import (
    SUPPORTED_FORMATS, SUPPORTED_SAMPLE_RATES, SERVICE_NAME,
    SERVICE_VERSION, SERVICE_DESCRIPTION, PING_TIMEOUT
)
from .utils import (
    create_test_audio_file, build_funasr_command, execute_funasr_client,
    parse_funasr_output, cleanup_temp_file
)

logger = logging.getLogger(__name__)


@register_asr_service("funasr")
class FunASRService(ASRDialectService):
    """FunASR WebSocket客户端服务"""
    
    def __init__(self, host: str = None, port: int = None, 
                 use_ssl: bool = None, mode: str = None, 
                 chunk_size: str = None):
        """
        初始化FunASR服务
        
        Args:
            host: FunASR服务器地址，None时从环境变量获取
            port: 服务器端口，None时从环境变量获取
            use_ssl: 是否使用SSL，None时从环境变量获取
            mode: 识别模式，None时从环境变量获取
            chunk_size: 分块配置，None时从环境变量获取
        """
        super().__init__()
        self.host = host or get_funasr_host()
        self.port = port or get_funasr_port()
        self.use_ssl = use_ssl if use_ssl is not None else get_funasr_use_ssl()
        self.mode = mode or get_funasr_mode()
        self.chunk_size = chunk_size or get_funasr_chunk_size()
        self.client_script = get_client_script_path()
        
        logger.info(f"FunASR服务初始化: {self.host}:{self.port}, SSL: {self.use_ssl}, 模式: {self.mode}")
    
    def ping(self) -> bool:
        """检查FunASR服务是否可用"""
        try:
            # 创建测试音频文件
            test_file = create_test_audio_file()
            
            try:
                # 构建测试命令
                cmd = build_funasr_command(
                    self.client_script, self.host, self.port,
                    self.mode, self.chunk_size, test_file, self.use_ssl
                )
                
                # 执行测试
                result = execute_funasr_client(
                    cmd, Path(self.client_script).parent, PING_TIMEOUT
                )
                
                # 检查是否成功连接
                if result.returncode == 0:
                    return True
                else:
                    logger.warning(f"FunASR ping失败: {result.stderr}")
                    return False
                    
            finally:
                # 清理测试文件
                cleanup_temp_file(test_file)
                    
        except Exception as e:
            logger.error(f"FunASR ping异常: {e}")
            return False
    
    def recognize_audio(self, audio_file: str) -> List[ASRRecognitionSegment]:
        """
        识别音频文件
        
        Args:
            audio_file: 音频文件路径
            
        Returns:
            List[ASRRecognitionSegment]: 识别结果段落列表
        """
        try:
            return self._recognize_with_funasr(audio_file)
        except Exception as e:
            logger.error(f"FunASR识别失败: {e}")
            return [ASRRecognitionSegment(
                text=f"识别失败: {e}",
                emotion=None,
                speaker=None,
                language=None
            )]
    
    def batch_recognize(self, audio_files: List[str]) -> List[List[ASRRecognitionSegment]]:
        """
        批量识别音频文件
        
        Args:
            audio_files: 音频文件路径列表
            
        Returns:
            List[List[ASRRecognitionSegment]]: 批量识别结果
        """
        results = []
        for audio_file in audio_files:
            try:
                result = self.recognize_audio(audio_file)
                results.append(result)
            except Exception as e:
                logger.error(f"批量识别文件 {audio_file} 失败: {e}")
                results.append([ASRRecognitionSegment(
                    text=f"识别失败: {e}",
                    emotion=None,
                    speaker=None,
                    language=None
                )])
        return results
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "service_name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "host": self.host,
            "port": self.port,
            "use_ssl": self.use_ssl,
            "mode": self.mode,
            "chunk_size": self.chunk_size,
            "supported_formats": SUPPORTED_FORMATS,
            "sample_rates": SUPPORTED_SAMPLE_RATES,
            "description": SERVICE_DESCRIPTION
        }
    
    def _recognize_with_funasr(self, audio_file: str) -> List[ASRRecognitionSegment]:
        """使用FunASR客户端进行识别"""
        try:
            # 创建临时输出目录
            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir)
                
                # 构建命令
                cmd = build_funasr_command(
                    self.client_script, self.host, self.port,
                    self.mode, self.chunk_size, audio_file, 
                    self.use_ssl, str(output_dir)
                )
                
                # 执行识别
                result = execute_funasr_client(cmd, Path(self.client_script).parent)
                
                if result.returncode != 0:
                    raise Exception(f"FunASR客户端执行失败: {result.stderr}")
                
                # 解析输出结果
                return parse_funasr_output(result.stdout, output_dir)
                
        except Exception as e:
            logger.error(f"FunASR识别异常: {e}")
            raise
