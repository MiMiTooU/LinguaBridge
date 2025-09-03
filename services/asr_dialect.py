import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from paddlespeech.cli.asr.infer import ASRExecutor
from audio_recoder import AudioTranscoder


class ASRDialectService:
    """
    ASR方言识别服务
    使用PaddleSpeech的ASR功能进行语音识别
    """
    
    def __init__(self, 
                 model: str = "conformer_wenetspeech",
                 lang: str = "zh",
                 sample_rate: int = 16000,
                 output_dir: str = "output"):
        """
        初始化ASR方言识别服务
        
        Args:
            model: ASR模型名称，默认使用conformer_wenetspeech
            lang: 语言，默认为zh(中文)
            sample_rate: 采样率，默认16000Hz
            output_dir: 输出目录
        """
        self.model = model
        self.lang = lang
        self.sample_rate = sample_rate
        
        # 初始化音频转码器
        self.audio_transcoder = AudioTranscoder(output_dir=output_dir)
        
        # 初始化ASR执行器
        self.asr_executor = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_asr(self):
        """
        懒加载初始化ASR执行器
        """
        if self.asr_executor is None:
            try:
                self.logger.info(f"初始化ASR模型: {self.model}")
                self.asr_executor = ASRExecutor()
                self.logger.info("ASR模型初始化成功")
            except Exception as e:
                self.logger.error(f"ASR模型初始化失败: {e}")
                raise RuntimeError(f"ASR模型初始化失败: {e}")
    
    def recognize_audio(self, 
                       audio_file: str, 
                       wav_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        识别音频文件中的语音
        
        Args:
            audio_file: 输入音频文件路径
            wav_params: 音频转码参数，可选
        
        Returns:
            Dict[str, Any]: 识别结果，包含文本和元数据
            
        Raises:
            FileNotFoundError: 音频文件不存在
            RuntimeError: ASR识别失败
        """
        try:
            # 检查输入文件
            if not Path(audio_file).exists():
                raise FileNotFoundError(f"音频文件不存在: {audio_file}")
            
            self.logger.info(f"开始处理音频文件: {audio_file}")
            
            # 设置默认转码参数，保证与ASR模型兼容
            default_wav_params = {
                "sample_rate": self.sample_rate,
                "channels": 1,
                "bit_depth": 16,
                "codec": "pcm_s16le"
            }
            
            if wav_params:
                default_wav_params.update(wav_params)
            
            # 步骤1: 转码音频文件
            self.logger.info("步骤1: 转码音频文件")
            transcoded_file = self.audio_transcoder.transcode_to_wav(
                audio_file, 
                default_wav_params
            )
            self.logger.info(f"音频转码完成: {transcoded_file}")
            
            # 步骤2: 初始化ASR模型（懒加载）
            self._initialize_asr()
            
            # 步骤3: 执行ASR识别
            self.logger.info("步骤3: 执行ASR识别")
            recognition_result = self.asr_executor(
                audio_file=transcoded_file,
                model=self.model,
                lang=self.lang,
                sample_rate=self.sample_rate
            )
            
            # 整理返回结果
            result = {
                "success": True,
                "text": recognition_result,
                "original_file": audio_file,
                "transcoded_file": transcoded_file,
                "model": self.model,
                "language": self.lang,
                "sample_rate": self.sample_rate,
                "wav_params": default_wav_params
            }
            
            self.logger.info(f"ASR识别成功: {recognition_result}")
            return result
            
        except FileNotFoundError:
            raise
        except Exception as e:
            error_msg = f"ASR识别失败: {e}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "original_file": audio_file,
                "model": self.model,
                "language": self.lang
            }
    
    def batch_recognize(self, 
                       input_dir: str, 
                       wav_params: Optional[Dict[str, Any]] = None,
                       supported_formats: Optional[list] = None) -> list:
        """
        批量识别目录中的音频文件
        
        Args:
            input_dir: 输入目录路径
            wav_params: 音频转码参数
            supported_formats: 支持的音频格式列表
        
        Returns:
            list: 批量识别结果列表
        """
        if supported_formats is None:
            supported_formats = [
                ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".wma", 
                ".amr", ".3gp", ".opus", ".webm", ".mp4", ".wav"
            ]
        
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        results = []
        
        for file_path in input_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                try:
                    result = self.recognize_audio(str(file_path), wav_params)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"批量识别失败 {file_path}: {e}")
                    results.append({
                        "success": False,
                        "error": str(e),
                        "original_file": str(file_path)
                    })
        
        self.logger.info(f"批量识别完成，处理 {len(results)} 个文件")
        return results
    
    def get_supported_models(self) -> list:
        """
        获取支持的ASR模型列表
        
        Returns:
            list: 支持的模型列表
        """
        # PaddleSpeech支持的主要ASR模型
        return [
            "conformer_wenetspeech",  # 中文通用模型
            "conformer_aishell",      # 中文模型
            "deepspeech2_aishell",    # 中文模型
            "conformer_librispeech",  # 英文模型
            "deepspeech2_librispeech" # 英文模型
        ]


# 使用示例
if __name__ == "__main__":
    # 创建服务实例
    asr_service = ASRDialectService()
    
    # 示例1: 识别单个音频文件
    try:
        result = asr_service.recognize_audio("zh.wav")
        if result["success"]:
            print(f"识别成功: {result['text']}")
        else:
            print(f"识别失败: {result['error']}")
    except Exception as e:
        print(f"处理失败: {e}")
    
    # 示例2: 查看支持的模型
    print(f"支持的模型: {asr_service.get_supported_models()}")
    
    # 示例3: 批量识别
    # try:
    #     results = asr_service.batch_recognize("input_folder")
    #     for result in results:
    #         if result["success"]:
    #             print(f"文件: {result['original_file']}, 识别结果: {result['text']}")
    #         else:
    #             print(f"文件: {result['original_file']}, 识别失败: {result['error']}")
    # except Exception as e:
    #     print(f"批量识别失败: {e}")