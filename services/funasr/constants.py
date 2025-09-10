"""
FunASR服务常量定义
"""

# 默认配置常量
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 10095
DEFAULT_USE_SSL = True
DEFAULT_MODE = "offline"
DEFAULT_CHUNK_SIZE = "5,10,5"

# 支持的音频格式
SUPPORTED_FORMATS = ["wav", "mp3", "flac", "aac"]

# 支持的采样率
SUPPORTED_SAMPLE_RATES = [8000, 16000, 22050, 44100]

# 识别模式
RECOGNITION_MODES = {
    "offline": "离线模式，完整音频处理后返回结果，准确度最高",
    "online": "在线模式，实时流式识别，延迟最低", 
    "2pass": "两遍模式，平衡延迟和准确度"
}

# 超时设置
PING_TIMEOUT = 10  # ping测试超时时间（秒）
RECOGNITION_TIMEOUT = 300  # 识别超时时间（秒）

# 测试音频参数
TEST_AUDIO_DURATION = 0.1  # 测试音频时长（秒）
TEST_AUDIO_CHANNELS = 1  # 测试音频声道数
TEST_AUDIO_SAMPLE_WIDTH = 2  # 测试音频位深（字节）
TEST_AUDIO_FRAME_RATE = 16000  # 测试音频采样率

# 服务信息
SERVICE_NAME = "FunASR WebSocket"
SERVICE_VERSION = "1.0"
SERVICE_DESCRIPTION = "基于FunASR WebSocket的语音识别服务"
