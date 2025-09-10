"""
百度文心大模型服务常量定义
"""

# 默认模型配置
DEFAULT_MODEL_NAME = "ERNIE-Bot-turbo"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_TOP_P = 0.7
DEFAULT_PENALTY_SCORE = 1.0

# 支持的模型列表
SUPPORTED_MODELS = [
    "ERNIE-Bot",
    "ERNIE-Bot-turbo", 
    "ERNIE-Bot-4",
    "ERNIE-Speed-8K",
    "ERNIE-Speed-128K",
    "ERNIE-Lite-8K"
]

# 总结类型配置
SUMMARY_TYPES = {
    "general": {
        "name": "通用总结",
        "description": "对文本进行全面的总结，保留主要信息和关键细节",
        "prompt_template": "请对以下文本进行总结，保留主要信息和关键细节：\n\n{text}\n\n总结："
    },
    "key_points": {
        "name": "关键要点",
        "description": "提取文本中的关键要点和核心观点",
        "prompt_template": "请提取以下文本的关键要点和核心观点：\n\n{text}\n\n关键要点："
    },
    "brief": {
        "name": "简要概括",
        "description": "用简洁的语言概括文本的主要内容",
        "prompt_template": "请用简洁的语言概括以下文本的主要内容：\n\n{text}\n\n简要概括："
    }
}

# 长度限制
DEFAULT_MAX_LENGTH = 500
MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 10000

# 批量处理限制
MAX_BATCH_SIZE = 10

# 服务信息
SERVICE_NAME = "百度文心大模型"
SERVICE_VERSION = "1.0"
SERVICE_DESCRIPTION = "基于LangChain的百度文心大模型总结服务"

# API配置
API_TIMEOUT = 30  # API调用超时时间（秒）
MAX_RETRIES = 3   # 最大重试次数
