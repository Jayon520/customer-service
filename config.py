"""
配置文件 - 所有敏感信息都放在 .env 文件中
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 企业微信配置
    WECHAT_CORP_ID: str = ""  # 企业ID
    WECHAT_AGENT_ID: str = ""  # 应用AgentId
    WECHAT_SECRET: str = ""  # 应用Secret
    WECHAT_TOKEN: str = ""  # 回调配置Token
    WECHAT_ENCODING_AES_KEY: str = ""  # 回调配置EncodingAESKey
    
    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:password@localhost/customer_service"
    
    # 服务器配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # 知识库配置
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    MAX_CONTEXT_LENGTH: int = 4000  # 最大上下文长度
    
    # 转人工关键词
    TRANSFER_KEYWORDS: list = ["人工", "转人工", "投诉", "退款", "人工客服", "真人"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
