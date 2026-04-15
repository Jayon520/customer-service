"""知识库服务"""
from sqlalchemy.orm import Session
from models import Knowledge
from typing import List, Optional, Dict


class KnowledgeService:
    def __init__(self, db: Session):
        self.db = db
    
    async def search(self, query: str, top_k: int = 3) -> List[Knowledge]:
        """
        搜索知识库（简单关键词匹配）
        
        Args:
            query: 查询文本
            top_k: 返回前k个结果
            
        Returns:
            匹配的知识条目列表
        """
        # 构建查询 - 搜索标题、内容、关键词三个字段
        results = self.db.query(Knowledge).filter(
            (Knowledge.title.ilike(f"%{query}%")) |
            (Knowledge.content.ilike(f"%{query}%")) |
            (Knowledge.keywords.ilike(f"%{query}%"))
        ).limit(top_k).all()
        
        return results
    
    def add_knowledge(self, title: str, content: str, category: str, keywords: str = "") -> Knowledge:
        """添加知识条目"""
        knowledge = Knowledge(
            title=title,
            content=content,
            category=category,
            keywords=keywords
        )
        self.db.add(knowledge)
        self.db.commit()
        self.db.refresh(knowledge)
        return knowledge
    
    def update_knowledge(self, knowledge_id: int, title: Optional[str] = None, 
                         content: Optional[str] = None, category: Optional[str] = None,
                         keywords: Optional[str] = None) -> Optional[Knowledge]:
        """更新知识条目"""
        knowledge = self.db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if not knowledge:
            return None
        
        if title is not None:
            knowledge.title = title
        if content is not None:
            knowledge.content = content
        if category is not None:
            knowledge.category = category
        if keywords is not None:
            knowledge.keywords = keywords
        
        self.db.commit()
        self.db.refresh(knowledge)
        return knowledge
    
    def get_knowledge_by_id(self, knowledge_id: int) -> Optional[Knowledge]:
        """根据ID获取知识条目"""
        return self.db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    
    def get_all_knowledge(self) -> List[Knowledge]:
        """获取所有知识条目"""
        return self.db.query(Knowledge).all()
    
    def delete_knowledge(self, knowledge_id: int) -> bool:
        """删除知识条目"""
        knowledge = self.db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
        if knowledge:
            self.db.delete(knowledge)
            self.db.commit()
            return True
        return False
    
    def get_knowledge_paginated(self, page: int = 1, page_size: int = 10, keyword: str = "") -> Dict:
        """
        分页获取知识列表
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            keyword: 搜索关键词
            
        Returns:
            包含 items, total, page, page_size, total_pages 的字典
        """
        query = self.db.query(Knowledge)
        
        # 如果有搜索关键词
        if keyword:
            query = query.filter(
                (Knowledge.title.ilike(f"%{keyword}%")) |
                (Knowledge.content.ilike(f"%{keyword}%")) |
                (Knowledge.keywords.ilike(f"%{keyword}%"))
            )
        
        # 获取总数
        total = query.count()
        
        # 计算分页
        offset = (page - 1) * page_size
        items = query.order_by(Knowledge.updated_at.desc()).offset(offset).limit(page_size).all()
        
        # 计算总页数
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
