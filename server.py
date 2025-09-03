from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from route import router

# 创建FastAPI实例
app = FastAPI(
    title="LinguaBridge API",
    description="语言桥接服务API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径
@app.get("/")
async def root():
    return {"message": "欢迎使用LinguaBridge API"}

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 包含路由器
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)