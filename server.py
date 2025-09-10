from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
from route import router
from swagger_config import setup_swagger_static
from logging_config import init_logging
from middleware import LoggingMiddleware, ErrorHandlingMiddleware

# 初始化日志系统
logger = init_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动事件
    logger.info("LinguaBridge API 服务启动")

    # 启动时预加载所有注册的服务
    try:
        from startup import initialize_services
        
        logger.info("开始预加载所有注册的服务...")
        
        # 初始化所有服务
        init_result = await initialize_services()
        
        # 记录初始化结果
        logger.info(f"服务预加载完成: {init_result['successful_services']}/{init_result['total_services']} 成功")
        
        if init_result['failed_services'] > 0:
            logger.warning(f"有 {init_result['failed_services']} 个服务初始化失败")
            for error in init_result['startup_errors']:
                logger.error(f"启动错误: {error}")
        
        # 存储初始化结果到应用状态
        app.state.service_init_result = init_result
        
    except Exception as e:
        logger.error(f"服务预加载失败: {e}")
        # 即使预加载失败，也不阻止应用启动
        app.state.service_init_result = {
            "total_services": 0,
            "successful_services": 0,
            "failed_services": 0,
            "startup_errors": [str(e)]
        }
    
    yield
    # 关闭事件
    logger.info("LinguaBridge API 服务关闭")

# 创建FastAPI实例
app = FastAPI(
    title="LinguaBridge API",
    description="语言桥接服务API",
    version="1.0.0",
    docs_url=None,  # 禁用默认docs
    redoc_url=None,  # 禁用默认redoc
    lifespan=lifespan
)

# 添加日志中间件（顺序很重要）
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置使用本地静态资源的Swagger UI
setup_swagger_static(app)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "method": request.method,
            "endpoint": str(request.url.path),
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "method": request.method,
            "endpoint": str(request.url.path),
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "服务器内部错误，请稍后重试"
        }
    )


# 根路径
@app.get("/")
async def root():
    logger.info("访问根路径")
    return {"message": "欢迎使用LinguaBridge API"}

# 健康检查端点
@app.get("/health")
async def health_check():
    logger.debug("健康检查")
    return {"status": "healthy", "service": "LinguaBridge API"}

# 包含路由器
app.include_router(router)

if __name__ == "__main__":
    logger.info("启动 LinguaBridge API 服务器")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_config=None,  # 禁用uvicorn默认日志配置，使用我们的配置
        access_log=False  # 禁用uvicorn访问日志，使用我们的中间件
    )