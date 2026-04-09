"""
大模型服务 - 封装DeepSeek API调用
"""
from openai import AsyncOpenAI
from config import settings
from typing import List, Dict, Optional
import httpx


class LLMService:
    """大模型服务类"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        self.model = settings.DEEPSEEK_MODEL
    
    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        调用大模型进行对话
        
        Args:
            messages: 对话历史
            context: 知识库上下文
            temperature: 温度参数，越高越随机
            max_tokens: 最大生成token数
        
        Returns:
            模型回复
        """
        # 如果有知识库上下文，添加到系统提示
        system_message = {
            "role": "system",
            "content": """你是一个专业的售后客服助手。你的职责是：
1. 热情、耐心地回答客户关于产品使用的问题
2. 帮助客户处理退换货申请
3. 如果客户明确要求转人工，请回复："好的，我正在为您转接人工客服，请稍候..."
4. 如果遇到无法确定的问题，不要编造答案，建议客户联系人工客服

请用简洁、友好的语言回复，避免过长的解释。"""
        }
        
        # 如果有知识库上下文，添加到系统消息
        if context:
            system_message["content"] += f"\n\n以下是相关的知识库内容，请参考：\n{context}"
        
        # 构建完整的消息列表
        full_messages = [system_message] + messages
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ 调用大模型失败: {e}")
            return "抱歉，我暂时无法回答您的问题，请稍后再试或联系人工客服。"
    
    async def detect_intent(self, message: str) -> Dict[str, str]:
        """
        检测用户意图
        
        Returns:
            {
                "intent": "consult/return_exchange/complaint/transfer_human/other",
                "confidence": "0.9"
            }
        """
        prompt = f"""分析以下用户消息的意图，只返回JSON格式：
消息："{message}"

可能的意图：
- consult: 产品使用咨询
- return_exchange: 退换货申请
- complaint: 投诉
- transfer_human: 要求转人工
- other: 其他

返回格式：{{"intent": "意图类型", "confidence": "置信度0-1"}}
只返回JSON，不要其他内容。"""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"❌ 意图检测失败: {e}")
            return {"intent": "other", "confidence": "0.5"}


# 创建全局实例
llm_service = LLMService()
