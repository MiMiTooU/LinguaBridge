import time
import uuid
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from logging import getLogger as get_logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """日志记录中间件"""
    
    def __init__(self, app, logger_name: str = "linguabridge.access"):
        super().__init__(app)
        self.logger = get_logger(logger_name)
        self.app_logger = get_logger("linguabridge")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 获取用户代理
        user_agent = request.headers.get("user-agent", "unknown")
        
        # 记录请求开始
        self.app_logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "endpoint": str(request.url.path),
                "client_ip": client_ip,
                "user_agent": user_agent,
                "query_params": str(request.query_params) if request.query_params else None
            }
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录访问日志
            self.logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "endpoint": str(request.url.path),
                    "status_code": response.status_code,
                    "duration": round(process_time * 1000, 2),  # 毫秒
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "query_params": str(request.query_params) if request.query_params else None
                }
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误
            self.app_logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "endpoint": str(request.url.path),
                    "duration": round(process_time * 1000, 2),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "error": str(e)
                },
                exc_info=True
            )
            
            # 返回500错误
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "request_id": request_id,
                    "message": "服务器内部错误，请稍后重试"
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": str(round(process_time * 1000, 2))
                }
            )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("linguabridge")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 记录未捕获的异常
            self.logger.error(
                f"Unhandled exception: {str(e)}",
                extra={
                    "method": request.method,
                    "endpoint": str(request.url.path),
                    "client_ip": request.client.host if request.client else "unknown"
                },
                exc_info=True
            )
            
            # 返回通用错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "服务器内部错误，请稍后重试"
                }
            )
