from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse
import os

def setup_swagger_static(app: FastAPI):
    """配置Swagger UI使用本地静态资源"""
    
    # 创建swagger静态资源目录
    swagger_static_dir = "static/swagger"
    os.makedirs(swagger_static_dir, exist_ok=True)
    
    # 重写docs端点使用本地资源
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            swagger_js_url="/static/swagger/swagger-ui-bundle.js",
            swagger_css_url="/static/swagger/swagger-ui.css",
            swagger_ui_parameters={
                "deepLinking": True,
                "displayRequestDuration": True,
                "docExpansion": "none",
                "operationsSorter": "alpha",
                "filter": True,
                "tagsSorter": "alpha",
                "tryItOutEnabled": True,
            }
        )
    
    # 重写redoc端点使用本地资源
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=app.title + " - ReDoc",
            redoc_js_url="/static/swagger/redoc.standalone.js",
        )

def download_swagger_assets():
    """下载Swagger UI静态资源到本地"""
    import requests
    import os
    
    swagger_static_dir = "static/swagger"
    os.makedirs(swagger_static_dir, exist_ok=True)
    
    # Swagger UI 资源URL
    assets = {
        "swagger-ui-bundle.js": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        "swagger-ui.css": "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
        "redoc.standalone.js": "https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"
    }
    
    for filename, url in assets.items():
        filepath = os.path.join(swagger_static_dir, filename)
        if not os.path.exists(filepath):
            try:
                print(f"Downloading {filename}...")
                response = requests.get(url)
                response.raise_for_status()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"✓ Downloaded {filename}")
            except Exception as e:
                print(f"✗ Failed to download {filename}: {e}")
        else:
            print(f"✓ {filename} already exists")

if __name__ == "__main__":
    # 运行此脚本来下载静态资源
    download_swagger_assets()
