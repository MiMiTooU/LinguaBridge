import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any


class AudioTranscoder:
    """音频转码器，使用ffmpeg将各种音频格式转换为wav格式"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化音频转码器
        
        Args:
            output_dir: 输出目录，默认为"output"
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def check_ffmpeg(self) -> bool:
        """
        检查ffmpeg是否可用
        
        Returns:
            bool: ffmpeg是否可用
        """
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def transcode_to_wav(
        self, 
        input_file: str, 
        wav_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        将音频文件转码为wav格式
        
        Args:
            input_file: 输入音频文件路径
            wav_params: wav转码参数字典，可包含:
                - sample_rate: 采样率 (默认: 16000)
                - channels: 声道数 (默认: 1)
                - bit_depth: 位深度 (默认: 16)
                - codec: 编码器 (默认: pcm_s16le)
        
        Returns:
            str: 输出文件路径
            
        Raises:
            FileNotFoundError: 输入文件不存在
            RuntimeError: ffmpeg不可用或转码失败
        """
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        if not self.check_ffmpeg():
            raise RuntimeError("ffmpeg不可用，请确保已安装ffmpeg并添加到PATH")
        
        # 设置默认参数
        default_params = {
            "sample_rate": 16000,
            "channels": 1,
            "bit_depth": 16,
            "codec": "pcm_s16le"
        }
        
        if wav_params:
            default_params.update(wav_params)
        
        # 生成输出文件路径
        output_filename = input_path.stem + ".wav"
        output_path = self.output_dir / output_filename
        
        # 构建ffmpeg命令
        cmd = self._build_ffmpeg_command(input_path, output_path, default_params)
        
        self.logger.info(f"开始转码: {input_file} -> {output_path}")
        self.logger.info(f"转码参数: {default_params}")
        
        return self._execute_ffmpeg(cmd, output_path)
    
    def _build_ffmpeg_command(self, input_path: Path, output_path: Path, params: Dict[str, Any]) -> list:
        """构建ffmpeg命令"""
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-ar", str(params["sample_rate"]),
            "-ac", str(params["channels"]),
            "-c:a", params["codec"],
            "-y",  # 覆盖输出文件
            str(output_path)
        ]
        
        # 根据位深度调整编码器
        if params["bit_depth"] == 24:
            cmd[cmd.index("-c:a") + 1] = "pcm_s24le"
        elif params["bit_depth"] == 32:
            cmd[cmd.index("-c:a") + 1] = "pcm_s32le"
        
        return cmd
    
    def _execute_ffmpeg(self, cmd: list, output_path: Path) -> str:
        """执行ffmpeg命令"""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode != 0:
            error_msg = f"转码失败: {result.stderr}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        self.logger.info(f"转码成功: {output_path}")
        return str(output_path)
    
    def batch_transcode(
        self, 
        input_dir: str, 
        wav_params: Optional[Dict[str, Any]] = None,
        supported_formats: Optional[list] = None
    ) -> list:
        """
        批量转码目录中的音频文件
        
        Args:
            input_dir: 输入目录路径
            wav_params: wav转码参数
            supported_formats: 支持的音频格式列表，默认支持常见格式
        
        Returns:
            list: 成功转码的文件路径列表
        """
        if supported_formats is None:
            supported_formats = [
                ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".wma", 
                ".amr", ".3gp", ".opus", ".webm", ".mp4"
            ]
        
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        success_files = []
        
        for file_path in input_path.iterdir():
            if not (file_path.is_file() and file_path.suffix.lower() in supported_formats):
                continue
                
            output_file = self._try_transcode_file(file_path, wav_params)
            if output_file:
                success_files.append(output_file)
        
        self.logger.info(f"批量转码完成，成功转码 {len(success_files)} 个文件")
        return success_files
    
    def _try_transcode_file(self, file_path: Path, wav_params: Optional[Dict[str, Any]]) -> Optional[str]:
        """尝试转码单个文件，失败时返回None"""
        try:
            return self.transcode_to_wav(str(file_path), wav_params)
        except Exception as e:
            self.logger.error(f"转码失败 {file_path}: {e}")
            return None


# 使用示例
if __name__ == "__main__":
    # 创建转码器实例
    transcoder = AudioTranscoder()
    
    # 示例1: 转码单个文件
    try:
        # 使用默认参数转码
        output_file = transcoder.transcode_to_wav("zh.wav")
        print(f"转码成功: {output_file}")
        
        # 使用自定义参数转码
        custom_params = {
            "sample_rate": 44100,
            "channels": 2,
            "bit_depth": 24
        }
        # output_file = transcoder.transcode_to_wav("input.mp3", custom_params)
        # print(f"转码成功: {output_file}")
        
    except Exception as e:
        print(f"转码失败: {e}")
    
    # 示例2: 批量转码
    # try:
    #     success_files = transcoder.batch_transcode("input_folder")
    #     print(f"批量转码成功，共 {len(success_files)} 个文件")
    # except Exception as e:
    #     print(f"批量转码失败: {e}")