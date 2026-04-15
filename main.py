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

app = FastAPI(title="智能售后客服系统", description="基于大模型的企业微信智能客服", version="1.0.0")

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== 企业微信回调接口 ====================
@app.get("/wechat/callback")
async def wechat_verify(msg_signature: str, timestamp: str, nonce: str, echostr: str, db: Session = Depends(get_db)):
    wechat_service = WeChatService(db)
    result = wechat_service.verify_signature(msg_signature, timestamp, nonce, echostr)
    return PlainTextResponse(content=result)

@app.post("/wechat/callback")
async def wechat_message(request: Request, db: Session = Depends(get_db)):
    wechat_service = WeChatService(db)
    reply = await wechat_service.handle_message(request)
    return PlainTextResponse(content=reply)

# ==================== 知识库管理接口 ====================
class KnowledgeCreate(BaseModel):
    title: str
    content: str
    category: str
    keywords: Optional[str] = ""

class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[str] = None

class KnowledgeResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    keywords: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    class Config:
        from_attributes = True

class PaginatedKnowledgeResponse(BaseModel):
    items: List[KnowledgeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# 获取知识列表（支持分页和搜索）
@app.get("/api/knowledge", response_model=PaginatedKnowledgeResponse)
async def list_knowledge(page: int = 1, page_size: int = 10, keyword: str = "", db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    result = service.get_knowledge_paginated(page=page, page_size=page_size, keyword=keyword)
    items = [KnowledgeResponse(
        id=item.id, title=item.title, content=item.content, category=item.category,
        keywords=item.keywords,
        created_at=item.created_at.isoformat() if item.created_at else None,
        updated_at=item.updated_at.isoformat() if item.updated_at else None
    ) for item in result["items"]]
    return PaginatedKnowledgeResponse(items=items, total=result["total"], page=result["page"], page_size=result["page_size"], total_pages=result["total_pages"])

# 添加知识
@app.post("/api/knowledge", response_model=KnowledgeResponse)
async def add_knowledge(knowledge: KnowledgeCreate, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    result = service.add_knowledge(title=knowledge.title, content=knowledge.content, category=knowledge.category, keywords=knowledge.keywords)
    return KnowledgeResponse(id=result.id, title=result.title, content=result.content, category=result.category, keywords=result.keywords, created_at=result.created_at.isoformat() if result.created_at else None, updated_at=result.updated_at.isoformat() if result.updated_at else None)

# 获取单条知识
@app.get("/api/knowledge/{knowledge_id}", response_model=KnowledgeResponse)
async def get_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    result = service.get_knowledge_by_id(knowledge_id)
    if not result:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    return KnowledgeResponse(id=result.id, title=result.title, content=result.content, category=result.category, keywords=result.keywords, created_at=result.created_at.isoformat() if result.created_at else None, updated_at=result.updated_at.isoformat() if result.updated_at else None)

# 更新知识
@app.put("/api/knowledge/{knowledge_id}", response_model=KnowledgeResponse)
async def update_knowledge(knowledge_id: int, knowledge: KnowledgeUpdate, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    result = service.update_knowledge(knowledge_id=knowledge_id, title=knowledge.title, content=knowledge.content, category=knowledge.category, keywords=knowledge.keywords)
    if not result:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    return KnowledgeResponse(id=result.id, title=result.title, content=result.content, category=result.category, keywords=result.keywords, created_at=result.created_at.isoformat() if result.created_at else None, updated_at=result.updated_at.isoformat() if result.updated_at else None)

# 删除知识
@app.delete("/api/knowledge/{knowledge_id}")
async def delete_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    service = KnowledgeService(db)
    success = service.delete_knowledge(knowledge_id)
    if not success:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    return {"message": "删除成功", "id": knowledge_id}

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
    from services.ticket_service import TicketService
    service = TicketService(db)
    tickets = service.get_pending_tickets()
    return [{"id": t.id, "title": t.title, "content": t.content, "ticket_type": t.ticket_type, "status": t.status.value} for t in tickets]

# ==================== 网页聊天接口 ====================
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "web_user"
    history: Optional[List[Dict[str, str]]] = []

@app.post("/api/chat")
async def chat_endpoint(chat_message: ChatMessage, db: Session = Depends(get_db)):
    print(f"\n{'='*60}")
    print(f"[聊天请求] 用户输入: {chat_message.message}")
    knowledge_service = KnowledgeService(db)
    relevant_knowledge = await knowledge_service.search(chat_message.message)
    print(f"[知识库检索] 找到 {len(relevant_knowledge)} 条相关知识")
    context = "\n".join([f"Q: {k.title}\nA: {k.content}" for k in relevant_knowledge[:3]]) if relevant_knowledge else ""
    messages = chat_message.history + [{"role": "user", "content": chat_message.message}]
    print(f"[对话历史] 消息数量: {len(messages)}")
    print(f"[LLM调用] 开始调用 DeepSeek API...")
    try:
        reply = await llm_service.chat(messages=messages, context=context)
        print(f"[LLM回复] 成功，回复长度: {len(reply)} 字符")
    except Exception as e:
        print(f"[LLM错误] {type(e).__name__}: {e}")
        reply = "抱歉，我遇到了一些问题，请稍后再试或联系人工客服。"
    print(f"{'='*60}\n")
    return {"reply": reply, "user_id": chat_message.user_id}

# ==================== 系统管理接口 ====================
@app.get("/")
async def root():
    return {"message": "智能售后客服系统运行中", "version": "1.0.0", "docs": "/docs", "chat": "/chat.html", "admin": "/admin.html"}

@app.get("/chat.html", response_class=HTMLResponse)
async def chat_page():
    try:
        with open("static/chat.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return HTMLResponse(content="<h1>聊天页面加载失败</h1>", status_code=404)

@app.get("/admin.html", response_class=HTMLResponse)
async def admin_page():
    try:
        with open("static/admin.html", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return HTMLResponse(content="<h1>管理后台页面加载失败</h1>", status_code=404)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ==================== 启动事件 ====================
@app.on_event("startup")
async def startup_event():
    print("🚀 正在初始化数据库...")
    init_db()
    print("📚 正在初始化知识库...")
    db = SessionLocal()
    try:
        service = KnowledgeService(db)
        existing = service.get_all_knowledge()
        if len(existing) == 0:
            import json
            with open('knowledge_sample.json', 'r', encoding='utf-8') as f:
                knowledge_data = json.load(f)
            for item in knowledge_data:
                service.add_knowledge(title=item['title'], content=item['content'], category=item['category'], keywords=item['keywords'])
            print(f"✅ 知识库初始化完成，导入{len(knowledge_data)}条数据")
        else:
            print(f"✅ 知识库已存在{len(existing)}条数据")
    except Exception as e:
        print(f"⚠️ 知识库初始化警告: {e}")
    finally:
        db.close()
    print("✅ 系统启动完成")

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.SERVER_HOST, port=settings.SERVER_PORT, reload=True)
