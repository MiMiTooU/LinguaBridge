#!/bin/bash

# LinguaBridge Docker构建脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目信息
REPO="mimitoou114"
PROJECT_NAME="linguabridge"
IMAGE_NAME="linguabridge-app"
VERSION=${1:-"latest"}

echo -e "${GREEN}=== LinguaBridge Docker构建脚本 ===${NC}"
echo -e "${YELLOW}项目名称: ${PROJECT_NAME}${NC}"
echo -e "${YELLOW}镜像名称: ${IMAGE_NAME}${NC}"
echo -e "${YELLOW}版本标签: ${VERSION}${NC}"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装或不在PATH中${NC}"
    exit 1
fi

# 检查docker-compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}警告: docker-compose未安装，将只构建镜像${NC}"
    COMPOSE_AVAILABLE=false
else
    COMPOSE_AVAILABLE=true
fi

# 创建必要的目录
echo -e "${GREEN}创建必要的目录...${NC}"
mkdir -p output logs

# 构建Docker镜像
echo -e "${GREEN}开始构建Docker镜像...${NC}"
docker build -t ${REPO}/${IMAGE_NAME}:${VERSION} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker镜像构建成功${NC}"
else
    echo -e "${RED}✗ Docker镜像构建失败${NC}"
    exit 1
fi

# 标记为latest
if [ "$VERSION" != "latest" ]; then
    docker tag ${REPO}/${IMAGE_NAME}:${VERSION} ${REPO}/${IMAGE_NAME}:latest
    echo -e "${GREEN}✓ 镜像已标记为latest${NC}"
fi

# 显示镜像信息
echo -e "${GREEN}镜像信息:${NC}"
docker images | grep ${IMAGE_NAME}

echo ""
echo -e "${GREEN}=== 构建完成 ===${NC}"
echo -e "${YELLOW}使用以下命令运行容器:${NC}"
echo -e "  docker run -p 8000:8000 ${REPO}/${IMAGE_NAME}:${VERSION}"
echo ""

if [ "$COMPOSE_AVAILABLE" = true ]; then
    echo -e "${YELLOW}或使用docker-compose:${NC}"
    echo -e "  docker-compose up -d"
    echo ""
fi

echo -e "${YELLOW}API文档地址: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}健康检查地址: http://localhost:8000/health${NC}"
