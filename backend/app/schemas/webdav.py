from pydantic import BaseModel, Field, HttpUrl


class WebDAVConfig(BaseModel):
    """WebDAV配置模型"""
    url: HttpUrl = Field(..., description="WebDAV服务器地址")
    username: str = Field(..., min_length=1, max_length=255, description="用户名")
    password: str = Field(..., min_length=1, max_length=255, description="密码")


class WebDAVConfigResponse(BaseModel):
    """WebDAV配置响应模型"""
    message: str
    url: str | None = None
    username: str | None = None 