"""
FastAPI主程序
"""
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, SessionLocal, init_db, Base
from services.wechat_service import WeChatService
from services.knowledge_service import KnowledgeService
from services.llm_service import llm_service
from models import Knowledge
from config import settings
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import os

# 创建FastAPI应用
app = FastAPI(
    title="智能售后客服系统",
    description="基于大模型的企业微信智能客服",
    version="1.0.0"
)

# 挂载静态文件目录
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 企业微信回调接口 ====================

@app.get("/wechat/callback")
async def wechat_verify(
    msg_signature: str,
    timestamp: str,
    nonce: str,
    echostr: str,
    db: Session = Depends(get_db)
):
    """企业微信回调验证"""
    wechat_service = WeChatService(db)
    # 企业微信使用 msg_signature 参数名，但验证逻辑中使用 signature
    result = wechat_service.verify_signature(msg_signature, timestamp, nonce, echostr)
    return PlainTextResponse(content=result)


@app.post("/wechat/callback")
async def wechat_message(
    request: Request,
    db: Session = Depends(get_db)
):
    """企业微信消息接收"""
    wechat_service = WeChatService(db)
    reply = await wechat_service.handle_message(request)
    return PlainTextResponse(content=reply)


# ==================== 知识库管理接口 ====================

class KnowledgeCreate(BaseModel):
    title: str
    content: str
    category: str
    keywords: Optional[str] = ""


class KnowledgeResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    keywords: str
    
    class Config:
        from_attributes = True


@app.post("/api/knowledge", response_model=KnowledgeResponse)
async def add_knowledge(
    knowledge: KnowledgeCreate,
    db: Session = Depends(get_db)
):
    """添加知识条目"""
    service = KnowledgeService(db)
    result = service.add_knowledge(
        title=knowledge.title,
        content=knowledge.content,
        category=knowledge.category,
        keywords=knowledge.keywords
    )
    return result


@app.get("/api/knowledge", response_model=List[KnowledgeResponse])
async def list_knowledge(db: Session = Depends(get_db)):
    """获取所有知识条目"""
    service = KnowledgeService(db)
    return service.get_all_knowledge()


@app.delete("/api/knowledge/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db)
):
    """删除知识条目"""
    service = KnowledgeService(db)
    success = service.delete_knowledge(knowledge_id)
    if not success:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    return {"message": "删除成功"}


# ==================== 工单管理接口 ====================

class TicketResponse(BaseModel):
    id: int
    title: str
    content: str
    ticket_type: str
    status: str
    
    class Config:
        from_attributes = True


@app.get("/api/tickets/pending", response_model=List[TicketResponse])
async def get_pending_tickets(db: Session = Depends(get_db)):
    """获取待处理工单"""
    from services.ticket_service import TicketService
    from models import TicketStatus
    
    service = TicketService(db)
    tickets = service.get_pending_tickets()
    
    return [
        {
            "id": t.id,
            "title": t.title,
            "content": t.content,
            "ticket_type": t.ticket_type,
            "status": t.status.value
        }
        for t in tickets
    ]


# ==================== 网页聊天接口 ====================

class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "web_user"
    history: Optional[List[Dict[str, str]]] = []

@app.post("/api/chat")
async def chat_endpoint(
    chat_message: ChatMessage,
    db: Session = Depends(get_db)
):
    """网页聊天接口"""
    print(f"\n{'='*60}")
    print(f"[聊天请求] 用户输入: {chat_message.message}")
    
    # 检索相关知识点
    knowledge_service = KnowledgeService(db)
    relevant_knowledge = await knowledge_service.search(chat_message.message)
    print(f"[知识库检索] 找到 {len(relevant_knowledge)} 条相关知识")
    
    # 构建上下文
    context = ""
    if relevant_knowledge:
        context = "\n".join([f"Q: {k.title}\nA: {k.content}" for k in relevant_knowledge[:3]])
        print(f"[上下文] 已构建上下文，长度: {len(context)} 字符")
    else:
        print(f"[上下文] 未找到相关知识")
    
    # 构建对话历史
    messages = chat_message.history + [{"role": "user", "content": chat_message.message}]
    print(f"[对话历史] 消息数量: {len(messages)}")
    
    # 调用大模型
    print(f"[LLM调用] 开始调用 DeepSeek API...")
    try:
        reply = await llm_service.chat(messages=messages, context=context)
        print(f"[LLM回复] 成功，回复长度: {len(reply)} 字符")
        print(f"[LLM回复内容] {reply[:100]}...")
    except Exception as e:
        print(f"[LLM错误] {type(e).__name__}: {e}")
        reply = "抱歉，我遇到了一些问题，请稍后再试或联系人工客服。"
    
    print(f"{'='*60}\n")
    
    return {
        "reply": reply,
        "user_id": chat_message.user_id
    }


# ==================== 系统管理接口 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "智能售后客服系统运行中",
        "version": "1.0.0",
        "docs": "/docs",
        "chat": "/chat.html"
    }


@app.get("/chat.html", response_class=HTMLResponse)
async def chat_page():
    """聊天页面"""
    try:
        with open("static/chat.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return HTMLResponse(content="<h1>聊天页面加载失败</h1>", status_code=404)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    print("🚀 正在初始化数据库...")
    init_db()
    
    # 自动初始化知识库数据
    print("📚 正在初始化知识库...")
    db = SessionLocal()
    try:
        from services.knowledge_service import KnowledgeService
        service = KnowledgeService(db)
        
        # 检查知识库是否为空
        existing = service.get_all_knowledge()
        if len(existing) == 0:
            # 导入示例数据
            import json
            with open('knowledge_sample.json', 'r', encoding='utf-8') as f:
                knowledge_data = json.load(f)
            
            for item in knowledge_data:
                service.add_knowledge(
                    title=item['title'],
                    content=item['content'],
                    category=item['category'],
                    keywords=item['keywords']
                )
            print(f"✅ 知识库初始化完成，导入{len(knowledge_data)}条数据")
        else:
            print(f"✅ 知识库已存在{len(existing)}条数据")
    except Exception as e:
        print(f"⚠️ 知识库初始化警告: {e}")
    finally:
        db.close()
    
    print("✅ 系统启动完成")


# ==================== 主程序入口 ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=True
    )
