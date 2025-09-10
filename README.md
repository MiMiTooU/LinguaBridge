# LinguaBridge - 语言桥接服务

LinguaBridge是一个基于FunASR的ASR语音识别和LLM文本总结服务，支持多种音频格式的语音识别和智能文本摘要。

## 功能特性

- 🎵 支持多种音频格式（MP3, WAV, M4A, AAC, FLAC等）
- 🔄 自动音频转码（使用FFmpeg）
- 🗣️ ASR语音识别（基于FunASR WebSocket客户端）
- 🤖 LLM文本总结（基于百度文心一言）
- 🌐 RESTful API接口
- 🐳 Docker容器化部署
- 📊 完整的日志记录和错误处理

## 快速开始

### 使用Docker（推荐）

1. **构建镜像**
   ```bash
   # 使用构建脚本
   chmod +x build.sh
   ./build.sh

   # 或手动构建
   docker build -t linguabridge-app .
   ```

2. **运行容器**
   ```bash
   # 使用docker-compose（推荐）
   docker-compose up -d

   # 或直接运行
   docker run -p 8000:8000 -v ./output:/app/output linguabridge-app
   ```

3. **访问服务**
   - API文档: http://localhost:8000/docs
   - 健康检查: http://localhost:8000/health

### 本地开发

1. **环境变量配置**
   ```bash
   # 创建 .env 文件或设置环境变量
   export BAIDU_API_KEY="your_baidu_api_key"
   export BAIDU_SECRET_KEY="your_baidu_secret_key"
   
   # FunASR服务器配置
   export FUNASR_HOST="127.0.0.1"
   export FUNASR_PORT="10095"
   export FUNASR_USE_SSL="true"
   export FUNASR_MODE="offline"
   ```

2. **安装依赖**
   ```bash
   # 安装FFmpeg
   # Ubuntu/Debian: sudo apt-get install ffmpeg
   # macOS: brew install ffmpeg
   # Windows: 下载并添加到PATH

   # 安装Python依赖
   pip install -r requirements.txt
   ```

3. **启动服务**
   ```bash
   python server.py
   ```

## API接口

### ASR语音识别

#### 上传音频文件进行识别
```http
POST /api/upload-audio
Content-Type: multipart/form-data

参数:
- file: 音频文件（必需）
- host: FunASR服务器地址（可选，默认: 127.0.0.1）
- port: FunASR服务器端口（可选，默认: 10095）
- use_ssl: 是否使用SSL（可选，默认: true）
- mode: 识别模式（可选，默认: offline）
- chunk_size: 分块配置（可选，默认: "5,10,5"）
```

#### 获取支持的模型列表
```http
GET /api/models
```

### LLM文本总结

#### 单文本总结
```http
POST /api/summarize
Content-Type: application/json

{
  "text": "要总结的文本内容",
  "summary_type": "general",
  "max_length": 200
}
```

#### 批量文本总结
```http
POST /api/batch-summarize
Content-Type: application/json

{
  "texts": ["文本1", "文本2"],
  "summary_type": "general",
  "max_length": 200
}
```

#### 获取支持的总结类型
```http
GET /api/summary-types
```

#### ASR识别+文本总结组合服务
```http
POST /api/asr-and-summarize
Content-Type: multipart/form-data

参数:
- file: 音频文件（必需）
- summary_type: 总结类型（可选，默认: general）
- max_length: 总结最大长度（可选，默认: 200）
- 其他ASR参数...
```

## 支持的音频格式

- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- AAC (.aac)
- FLAC (.flac)
- OGG (.ogg)
- WMA (.wma)
- AMR (.amr)
- 3GP (.3gp)
- OPUS (.opus)
- WebM (.webm)
- MP4 (.mp4)

## 支持的服务配置

### FunASR识别模式
- `offline` - 离线识别模式（默认）
- `online` - 在线识别模式
- `2pass` - 两遍识别模式

### LLM总结类型
- `general` - 通用总结（默认）
- `key_points` - 关键要点总结
- `brief` - 简要概括

## Docker配置

### 环境变量
- `PYTHONPATH`: Python路径（默认: /app）
- `LOG_LEVEL`: 日志级别（默认: INFO）
- `BAIDU_API_KEY`: 百度文心一言API密钥（必需）
- `BAIDU_SECRET_KEY`: 百度文心一言密钥（必需）

### 挂载卷
- `./output:/app/output` - 转码文件输出目录
- `./logs:/app/logs` - 日志文件目录

### 资源限制
- 内存限制: 2GB
- CPU限制: 1核心
- 内存预留: 512MB
- CPU预留: 0.5核心

## 项目结构

```
LinguaBridge/
├── client/             # FunASR客户端
│   ├── funasr_client_api.py
│   ├── funasr_wss_client.py
│   └── requirements_client.txt
├── config/             # 配置文件
│   └── prompts.json   # LLM提示词配置
├── services/           # 服务模块
│   ├── asr_dialect.py # ASR识别服务
│   ├── audio_recoder.py # 音频转码服务
│   └── llm_summary.py # LLM文本总结服务
├── logs/              # 日志目录
├── output/            # 输出目录
├── server.py          # FastAPI服务器
├── route.py           # API路由
├── auth.py            # 认证模块
├── middleware.py      # 中间件
├── logging_config.py  # 日志配置
├── swagger_config.py  # Swagger配置
├── requirements.txt   # Python依赖
├── Dockerfile         # Docker构建文件
├── docker-compose.yml # Docker Compose配置
├── build.sh          # 构建脚本（Linux）
├── build.bat         # 构建脚本（Windows）
└── README.md         # 项目说明
```

## 环境变量配置详解

### 必需环境变量

#### 百度文心一言配置
```bash
# 百度智能云控制台获取
BAIDU_API_KEY="your_api_key_here"
BAIDU_SECRET_KEY="your_secret_key_here"
```

**获取步骤：**
1. 访问 [百度智能云控制台](https://console.bce.baidu.com/)
2. 创建应用并获取API Key和Secret Key
3. 确保已开通千帆大模型平台服务

### 可选环境变量
```bash
# 日志级别
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Python路径（Docker环境）
PYTHONPATH="/app"
```

## 开发说明

### 添加新的总结类型
1. 在 `config/prompts.json` 中添加新的提示词模板
2. 在 `services/llm_summary.py` 中更新总结类型配置

### 添加新的音频格式
1. 在 `route.py` 中的 `allowed_types` 列表添加MIME类型
2. 确保FFmpeg支持该格式

### 自定义FunASR服务器
1. 修改ASR请求中的host和port参数
2. 确保FunASR服务器正常运行

## 故障排除

### 常见问题

1. **FFmpeg未找到**
   - 确保FFmpeg已安装并在PATH中
   - Docker镜像已包含FFmpeg

2. **百度文心API调用失败**
   - 检查BAIDU_API_KEY和BAIDU_SECRET_KEY是否正确设置
   - 确认百度智能云账户余额充足
   - 检查网络连接和API配额

3. **FunASR连接失败**
   - 确保FunASR服务器正常运行
   - 检查host和port配置是否正确
   - 验证WebSocket连接是否可用

4. **内存不足**
   - 增加Docker容器内存限制
   - 处理较大音频文件时可能需要更多内存

5. **环境变量未生效**
   - 确保在启动服务前设置了环境变量
   - Docker环境中需要在docker-compose.yml中配置
   - 可以创建.env文件来管理环境变量

### 日志查看
```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs linguabridge-app -f

# 本地开发
tail -f logs/app.log      # 应用日志
tail -f logs/error.log    # 错误日志
tail -f logs/access.log   # 访问日志
```

## Docker环境变量配置示例

在docker-compose.yml中添加环境变量：
```yaml
services:
  linguabridge:
    environment:
      - BAIDU_API_KEY=your_api_key_here
      - BAIDU_SECRET_KEY=your_secret_key_here
      - LOG_LEVEL=INFO
```

或创建.env文件：
```bash
# .env文件
BAIDU_API_KEY=your_api_key_here
BAIDU_SECRET_KEY=your_secret_key_here
LOG_LEVEL=INFO
```

## 许可证

本项目采用MIT许可证。
