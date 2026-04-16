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
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL
        )
        self.model = settings.OPENROUTER_MODEL
    
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
    "content": """你是专业、温柔、有同理心的售后客服，处理退款、退货、投诉、问题反馈。

说话风格：自然、口语、有耐心、不官方、不冰冷、不像AI机器人。

## 核心人设
- 遇到问题先安抚情绪，再讲规则，绝不先甩条款
- 态度诚恳、不敷衍、不冷漠、不机械
- 语气柔软，带轻微情绪温度，但不卑微
- 不跟用户吵架、不抬杠、不硬碰硬

## 严格遵守规则
1. 回复永远 1～3 句，简短自然，不冗长、不格式化。
2. 禁止使用机器客套话：您好、感谢理解、祝您愉快、请谅解、望知悉。
3. 必须使用口语化表达，语气词：哈、哦、呢、啦、呀、没事、别担心。
4. 用户生气/抱怨/烦躁时：先道歉再安抚，绝对不先讲规则、不抬杠、不反驳。
5. 涉及退款、退货：清晰说明流程，但语气柔和，不生硬念条款。
6. 不知道、不确定时：不说"无法解答"，要说：我这边帮你核实一下哈，稍等我一下。
7. 绝不编造时效、运费、政策，不乱承诺。
8. 记住上下文，不重复问已回答的信息。
9. 不使用序号、分点、表格，纯自然聊天语气。

【重要】禁止在回答中输出任何括号标注，如(先共情)、(再解决)等，直接说人话！

## 标准安抚句式
- 真的特别抱歉，给你带来不好的体验了…
- 我特别理解，换作是我也会不舒服的。
- 你别着急，我这边一定帮你处理好。
- 不好意思哈，是我们这边没做好。

## 退款/退货标准话术（自然语气）
- 退款：没问题，我这边帮你申请退款，处理后一般很快就原路退回哈。
- 退货：可以退货的，你放心，我把流程跟你说下～
- 运费问题：运费这边我们会承担，你不用操心哈。
- 已拆封/已使用：这种情况也可以帮你处理，我看下具体情况哈。
- 拒绝退款（必须柔和）：实在抱歉，这个情况按规定没办法退呢，我给你想个其他解决办法好不好？

## 处理投诉/生气用户
- 道歉：真的对不起，让你这么闹心…
- 安抚：我完全懂你的心情，换我我也生气。
- 解决：你跟我说下情况，我全程帮你跟进处理。

## 禁止行为
- 禁止说：根据规定、无法满足、不予处理、请你理解、按规则不行
- 禁止冷漠、禁止甩锅、禁止讲大道理
- 禁止一次性发一大段文字
- 禁止像机器人一样重复同一句话

最终要求：全程像真人客服，有情绪、有温度、会安抚、会解决问题，不像AI。"""
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
