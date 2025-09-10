"""
FunASR服务工具函数
"""
import os
import sys
import json
import wave
import struct
import tempfile
import subprocess
import logging
from typing import List, Dict, Any
from pathlib import Path

from services.asr_dialect import ASRRecognitionSegment
from .constants import (
    TEST_AUDIO_DURATION, TEST_AUDIO_CHANNELS, 
    TEST_AUDIO_SAMPLE_WIDTH, TEST_AUDIO_FRAME_RATE,
    PING_TIMEOUT, RECOGNITION_TIMEOUT
)

logger = logging.getLogger(__name__)


def create_test_audio_file() -> str:
    """创建测试音频文件"""
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(TEST_AUDIO_CHANNELS)
        wav_file.setsampwidth(TEST_AUDIO_SAMPLE_WIDTH)
        wav_file.setframerate(TEST_AUDIO_FRAME_RATE)
        
        # 写入静音
        frames = int(TEST_AUDIO_FRAME_RATE * TEST_AUDIO_DURATION)
        for _ in range(frames):
            wav_file.writeframes(struct.pack('<h', 0))
    
    return temp_file.name


def build_funasr_command(client_script: str, host: str, port: int, mode: str, 
                        chunk_size: str, audio_file: str, use_ssl: bool = True, 
                        output_dir: str = None) -> List[str]:
    """构建FunASR客户端命令"""
    cmd = [
        sys.executable, str(client_script),
        "--host", host,
        "--port", str(port),
        "--mode", mode,
        "--chunk_size", chunk_size,
        "--audio_in", audio_file
    ]
    
    if output_dir:
        cmd.extend(["--output_dir", str(output_dir)])
    
    if not use_ssl:
        cmd.append("--no-ssl")
    
    return cmd


def execute_funasr_client(cmd: List[str], client_script_dir: Path, 
                         timeout: int = RECOGNITION_TIMEOUT) -> subprocess.CompletedProcess:
    """执行FunASR客户端命令"""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=client_script_dir
    )


def parse_funasr_output(stdout: str, output_dir: Path) -> List[ASRRecognitionSegment]:
    """解析FunASR输出结果"""
    segments = []
    
    try:
        # 尝试从输出目录读取结果文件
        result_files = list(output_dir.glob("*.txt"))
        if result_files:
            with open(result_files[0], 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    segments.append(ASRRecognitionSegment(
                        text=content,
                        emotion=None,
                        speaker=None,
                        language="zh"
                    ))
        
        # 如果没有结果文件，尝试解析stdout
        if not segments and stdout:
            lines = stdout.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('[') and not line.startswith('INFO'):
                    # 尝试解析JSON格式的结果
                    try:
                        result_data = json.loads(line)
                        if 'text' in result_data:
                            segments.append(ASRRecognitionSegment(
                                text=result_data['text'],
                                emotion=result_data.get('emotion'),
                                speaker=result_data.get('speaker'),
                                language=result_data.get('language', 'zh')
                            ))
                    except json.JSONDecodeError:
                        # 如果不是JSON，直接作为文本处理
                        segments.append(ASRRecognitionSegment(
                            text=line,
                            emotion=None,
                            speaker=None,
                            language="zh"
                        ))
        
        # 如果仍然没有结果，返回空结果
        if not segments:
            segments.append(ASRRecognitionSegment(
                text="",
                emotion=None,
                speaker=None,
                language="zh"
            ))
            
    except Exception as e:
        logger.error(f"解析FunASR输出失败: {e}")
        segments = [ASRRecognitionSegment(
            text=f"解析结果失败: {e}",
            emotion=None,
            speaker=None,
            language=None
        )]
    
    return segments


def cleanup_temp_file(file_path: str):
    """清理临时文件"""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        logger.warning(f"清理临时文件失败: {e}")
