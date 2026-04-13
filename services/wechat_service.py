"""
企业微信消息处理服务
"""
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from models import User, Conversation, Message, MessageRole
from services.llm_service import llm_service
from services.knowledge_service import KnowledgeService
from services.ticket_service import TicketService
from config import settings
import xml.etree.ElementTree as ET
import hashlib
import time
from typing import Optional


class WeChatService:
    """企业微信服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.knowledge_service = KnowledgeService(db)
        self.ticket_service = TicketService(db)
    
    def verify_signature(self, signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        """验证企业微信回调签名"""
        token = settings.WECHAT_TOKEN
    
        # 使用 sorted() 并明确编码
        arr = sorted([token, timestamp, nonce])
        sign_str = "".join(arr)
        sha1 = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()
    
        # 添加调试日志
        print(f"======== 签名验证调试 ========")
        print(f"Token: {token}")
        print(f"Token类型: {type(token)}")
        print(f"排序后数组: {arr}")
        print(f"拼接字符串: {sign_str}")
        print(f"拼接字符串(bytes): {sign_str.encode('utf-8')}")
        print(f"计算签名(sha1): {sha1}")
        print(f"企业微信签名: {signature}")
        print(f"签名匹配: {sha1 == signature}")
        print(f"============================")
    
        if sha1 == signature:
            return echostr
        return ""
    
    async def handle_message(self, request: Request) -> str:
        """
        处理企业微信消息
        
        Args:
            request: FastAPI请求对象
        
        Returns:
            回复消息XML
        """
        # 读取请求体
        body = await request.body()
        
        try:
            # 解析XML
            root = ET.fromstring(body.decode('utf-8'))
            
            # 提取消息信息
            from_user = root.find('FromUserName').text
            to_user = root.find('ToUserName').text
            msg_type = root.find('MsgType').text
            msg_id = root.find('MsgId').text if root.find('MsgId') is not None else None
            
            # 处理不同类型的消息
            if msg_type == 'text':
                content = root.find('Content').text
                reply = await self._process_text_message(from_user, content)
            else:
                reply = "暂不支持此类型消息，请发送文字消息。"
            
            # 构建回复XML
            return self._build_text_reply(from_user, to_user, reply)
            
        except Exception as e:
            print(f"❌ 处理消息失败: {e}")
            return ""
    
    async def _process_text_message(self, wechat_user_id: str, content: str) -> str:
        """
        处理文本消息
        
        Args:
            wechat_user_id: 企业微信用户ID
            content: 消息内容
        
        Returns:
            回复内容
        """
        # 1. 获取或创建用户
        user = self._get_or_create_user(wechat_user_id)
        
        # 2. 检查是否包含转人工关键词
        if any(keyword in content for keyword in settings.TRANSFER_KEYWORDS):
            return "好的，我正在为您转接人工客服，请稍候...如需查看历史工单，请回复'工单查询'。"
        
        # 3. 检查是否查询工单
        if "工单查询" in content or "查工单" in content:
            return await self._handle_ticket_query(user.id)
        
        # 4. 检查是否创建退换货工单
        if any(kw in content for kw in ["退货", "换货", "退款"]):
            return await self._handle_return_exchange(user.id, content)
        
        # 5. 获取或创建活跃会话
        conversation = self._get_or_create_conversation(user.id)
        
        # 6. 保存用户消息
        self._save_message(conversation.id, MessageRole.USER, content)
        
        # 7. 搜索知识库
        knowledge_list = await self.knowledge_service.search(content, top_k=3)
        context = self.knowledge_service.format_context(knowledge_list)
        
        # 8. 构建对话历史
        messages = self._build_conversation_history(conversation)
        
        # 9. 调用大模型
        reply = await llm_service.chat(messages, context)
        
        # 10. 保存助手回复
        self._save_message(conversation.id, MessageRole.ASSISTANT, reply)
        
        return reply
    
    def _get_or_create_user(self, wechat_user_id: str) -> User:
        """获取或创建用户"""
        user = self.db.query(User).filter(
            User.wechat_user_id == wechat_user_id
        ).first()
        
        if not user:
            user = User(wechat_user_id=wechat_user_id)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        
        return user
    
    def _get_or_create_conversation(self, user_id: int) -> Conversation:
        """获取或创建活跃会话"""
        conversation = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).first()
        
        if not conversation:
            conversation = Conversation(user_id=user_id)
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
        
        return conversation
    
    def _save_message(self, conversation_id: int, role: MessageRole, content: str):
        """保存消息"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
    
    def _build_conversation_history(self, conversation: Conversation, max_messages: int = 10):
        """构建对话历史"""
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.created_at.desc()).limit(max_messages).all()
        
        # 反转顺序，保持时间顺序
        messages = messages[::-1]
        
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]
    
    async def _handle_ticket_query(self, user_id: int) -> str:
        """处理工单查询"""
        tickets = self.ticket_service.get_user_tickets(user_id)
        
        if not tickets:
            return "您暂无工单记录。如需申请退换货，请描述您的需求。"
        
        reply = "您的工单记录：\n\n"
        for ticket in tickets[:5]:  # 只显示最近5条
            reply += self.ticket_service.get_ticket_summary(ticket) + "\n---\n"
        
        return reply
    
    async def _handle_return_exchange(self, user_id: int, content: str) -> str:
        """处理退换货申请"""
        # 创建工单
        ticket = self.ticket_service.create_ticket(
            user_id=user_id,
            title=f"用户申请-{content[:30]}",
            content=content,
            ticket_type="退换货"
        )
        
        return f"""您的退换货申请已提交，工单号：{ticket.id}
我们会在1-2个工作日内处理，请耐心等待。

如需查看工单进度，请回复"工单查询"。"""
    
    def _build_text_reply(self, to_user: str, from_user: str, content: str) -> str:
        """构建文本回复XML"""
        timestamp = str(int(time.time()))
        return f"""<xml>
<ToUserName><![CDATA[{to_user}]]></ToUserName>
<FromUserName><![CDATA[{from_user}]]></FromUserName>
<CreateTime>{timestamp}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
