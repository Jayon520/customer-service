"""
知识库服务 - 管理和检索知识库内容
"""
from sqlalchemy.orm import Session
from models import Knowledge
from typing import List, Optional
import os
import json


class KnowledgeService:
    """知识库服务类"""
    
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
        # 分词查询
        keywords = query.split()
        
        # 构建查询
        results = self.db.query(Knowledge).filter(
            Knowledge.content.ilike(f"%{query}%")
        ).limit(top_k).all()
        
        return results
    
    def format_context(self, knowledge_list: List[Knowledge]) -> str:
        """
        格式化知识库内容为上下文
        
        Args:
            knowledge_list: 知识条目列表
        
        Returns:
            格式化后的文本
        """
        if not knowledge_list:
            return ""
        
        context_parts = []
        for idx, knowledge in enumerate(knowledge_list, 1):
            context_parts.append(f"【{idx}. {knowledge.title}】\n{knowledge.content}")
        
        return "\n\n".join(context_parts)
    
    def add_knowledge(
        self, 
        title: str, 
        content: str, 
        category: str, 
        keywords: str = ""
    ) -> Knowledge:
        """
        添加知识条目
        
        Args:
            title: 标题
            content: 内容
            category: 分类
            keywords: 关键词
        
        Returns:
            创建的知识条目
        """
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
    
    def import_from_json(self, json_file: str) -> int:
        """
        从JSON文件导入知识库
        
        Args:
            json_file: JSON文件路径
        
        Returns:
            导入的条目数量
        """
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for item in data:
            self.add_knowledge(
                title=item.get('title', ''),
                content=item.get('content', ''),
                category=item.get('category', '未分类'),
                keywords=item.get('keywords', '')
            )
            count += 1
        
        return count
    
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
