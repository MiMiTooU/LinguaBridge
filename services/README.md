# 服务模块化架构文档

## 概述

LinguaBridge项目采用模块化的服务架构，每个服务类型都有独立的模块文件夹，包含其所需的常量、环境变量、静态文件和实现代码。

## 目录结构

```
services/
├── funasr/                    # FunASR语音识别服务模块
│   ├── __init__.py           # 模块初始化文件
│   ├── constants.py          # 服务常量定义
│   ├── config.py             # 环境变量配置
│   ├── utils.py              # 工具函数
│   └── service.py            # 服务实现
├── baidu_wenxin/             # 百度文心大模型服务模块
│   ├── __init__.py           # 模块初始化文件
│   ├── constants.py          # 服务常量定义
│   ├── config.py             # 环境变量配置
│   ├── utils.py              # 工具函数
│   └── service.py            # 服务实现
├── asr/                      # ASR服务注册模块
│   └── __init__.py           # 导入所有ASR服务
├── summary/                  # LLM总结服务注册模块
│   └── __init__.py           # 导入所有LLM服务
├── asr_dialect.py            # ASR服务抽象基类
├── llm_summary.py            # LLM服务抽象基类
└── README.md                 # 本文档
```

## 模块化设计原则

### 1. 分离关注点
每个服务模块包含以下文件：

- **constants.py**: 服务相关的常量定义
- **config.py**: 环境变量配置和获取函数
- **utils.py**: 工具函数和辅助方法
- **service.py**: 具体的服务实现类
- **__init__.py**: 模块导出和初始化

### 2. 环境变量管理
所有环境变量配置集中在各模块的`config.py`文件中，提供默认值和类型转换。

### 3. 常量集中管理
服务相关的常量（如默认配置、支持的格式等）统一定义在`constants.py`中。

### 4. 工具函数复用
通用的工具函数和辅助方法放在`utils.py`中，避免代码重复。

## FunASR服务模块

### 文件说明

#### constants.py
- 默认配置常量（主机、端口、SSL等）
- 支持的音频格式和采样率
- 识别模式定义
- 超时设置
- 服务信息

#### config.py
- 环境变量获取函数
- 配置参数类型转换
- 客户端脚本路径配置

#### utils.py
- 测试音频文件创建
- FunASR命令构建
- 客户端执行
- 输出结果解析
- 临时文件清理

#### service.py
- FunASRService类实现
- 服务注册装饰器
- ping检查
- 音频识别功能
- 批量处理

### 环境变量

```bash
FUNASR_HOST=127.0.0.1
FUNASR_PORT=10095
FUNASR_USE_SSL=true
FUNASR_MODE=offline
FUNASR_CHUNK_SIZE=5,10,5
FUNASR_CLIENT_SCRIPT=/path/to/client/script
```

## 百度文心服务模块

### 文件说明

#### constants.py
- 默认模型配置
- 支持的模型列表
- 总结类型配置
- 长度限制
- API配置

#### config.py
- API密钥获取
- 模型参数配置
- 超时设置

#### utils.py
- 输入验证
- 提示词生成
- 结果格式化
- 重试机制
- 错误处理

#### service.py
- BaiduWenxinSummaryService类实现
- 服务注册装饰器
- LangChain模型集成
- 文本总结功能
- 批量处理

### 环境变量

```bash
BAIDU_API_KEY=your_api_key
BAIDU_SECRET_KEY=your_secret_key
BAIDU_MODEL_NAME=ERNIE-Bot-turbo
BAIDU_TEMPERATURE=0.1
BAIDU_TOP_P=0.7
BAIDU_PENALTY_SCORE=1.0
BAIDU_MAX_LENGTH=500
BAIDU_API_TIMEOUT=30
```

## 服务注册机制

### ASR服务注册
```python
from services.asr_dialect import register_asr_service

@register_asr_service("service_name")
class MyASRService(ASRDialectService):
    pass
```

### LLM服务注册
```python
from services.llm_summary import register_llm_service

@register_llm_service("service_name")
class MyLLMService(LLMSummaryService):
    pass
```

## 使用示例

### 导入服务
```python
from services.funasr import FunASRService
from services.baidu_wenxin import BaiduWenxinSummaryService
```

### 创建服务实例
```python
# 使用默认配置（从环境变量）
asr_service = FunASRService()
llm_service = BaiduWenxinSummaryService()

# 使用自定义配置
asr_service = FunASRService(host="192.168.1.100", port=8080)
llm_service = BaiduWenxinSummaryService(model_name="ERNIE-Bot-4")
```

### 服务发现
```python
from services.asr_dialect import get_registered_asr_services, get_available_asr_services
from services.llm_summary import get_registered_llm_services, get_available_llm_services

# 获取已注册的服务
asr_services = get_registered_asr_services()
llm_services = get_registered_llm_services()

# 获取可用的服务（带健康检查）
available_asr = get_available_asr_services()
available_llm = get_available_llm_services()
```

## 扩展新服务

### 添加新的ASR服务
1. 在`services/`下创建新的服务模块文件夹
2. 按照模块化结构创建相应文件
3. 在`services/asr/__init__.py`中导入新服务
4. 使用`@register_asr_service`装饰器注册

### 添加新的LLM服务
1. 在`services/`下创建新的服务模块文件夹
2. 按照模块化结构创建相应文件
3. 在`services/summary/__init__.py`中导入新服务
4. 使用`@register_llm_service`装饰器注册

## 优势

1. **模块化**: 每个服务独立管理，便于维护和扩展
2. **配置集中**: 环境变量和常量统一管理
3. **代码复用**: 工具函数避免重复实现
4. **易于测试**: 模块化结构便于单元测试
5. **插件化**: 新服务可以轻松添加和移除
6. **类型安全**: 配置参数有明确的类型定义
