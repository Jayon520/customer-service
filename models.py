"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class MessageRole(enum.Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class TicketStatus(enum.Enum):
    """工单状态"""
    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    wechat_user_id = Column(String(100), unique=True, index=True, comment="企业微信用户ID")
    name = Column(String(100), comment="用户姓名")
    phone = Column(String(20), comment="手机号")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    conversations = relationship("Conversation", back_populates="user")
    tickets = relationship("Ticket", back_populates="user")


class Conversation(Base):
    """对话会话表"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), comment="用户ID")
    title = Column(String(200), comment="会话标题")
    is_active = Column(Boolean, default=True, comment="是否活跃")
    is_transferred = Column(Boolean, default=False, comment="是否已转人工")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    """消息表"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), comment="会话ID")
    role = Column(Enum(MessageRole), comment="消息角色")
    content = Column(Text, comment="消息内容")
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    conversation = relationship("Conversation", back_populates="messages")


class Ticket(Base):
    """工单表"""
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), comment="用户ID")
    conversation_id = Column(Integer, ForeignKey("conversations.id"), comment="关联会话ID")
    title = Column(String(200), comment="工单标题")
    content = Column(Text, comment="工单内容")
    ticket_type = Column(String(50), comment="工单类型：退货/换货/维修等")
    status = Column(Enum(TicketStatus), default=TicketStatus.PENDING, comment="工单状态")
    assignee = Column(String(100), comment="处理人")
    resolution = Column(Text, comment="处理结果")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("User", back_populates="tickets")


class Knowledge(Base):
    """知识库表"""
    __tablename__ = "knowledge"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), comment="标题")
    category = Column(String(50), comment="分类：产品使用/退换货/常见问题等")
    content = Column(Text, comment="内容")
    keywords = Column(String(500), comment="关键词，逗号分隔")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
