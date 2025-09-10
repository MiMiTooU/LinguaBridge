FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 配置清华源
RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye main contrib non-free" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bullseye-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bullseye-security main contrib non-free" >> /etc/apt/sources.list

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    wget \
    curl \
    git \
    # 编译工具
    gcc \
    g++ \
    make \
    # FFmpeg和音频处理依赖
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    # PortAudio依赖（pyaudio需要）
    portaudio19-dev \
    libasound2-dev \
    # 其他必要依赖
    pkg-config \
    && rm -rf /var/lib/apt/lists/*


# 升级pip并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p output logs

# 设置权限
RUN chmod +x server.py

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "server.py"]
