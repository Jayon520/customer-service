"""
工单服务 - 处理退换货工单
"""
from sqlalchemy.orm import Session
from models import Ticket, TicketStatus, User, Conversation
from typing import Optional, List
from datetime import datetime


class TicketService:
    """工单服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_ticket(
        self,
        user_id: int,
        title: str,
        content: str,
        ticket_type: str,
        conversation_id: Optional[int] = None
    ) -> Ticket:
        """
        创建工单
        
        Args:
            user_id: 用户ID
            title: 工单标题
            content: 工单内容
            ticket_type: 工单类型
            conversation_id: 关联会话ID
        
        Returns:
            创建的工单
        """
        ticket = Ticket(
            user_id=user_id,
            title=title,
            content=content,
            ticket_type=ticket_type,
            status=TicketStatus.PENDING,
            conversation_id=conversation_id
        )
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
    
    def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """获取工单"""
        return self.db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    def get_user_tickets(self, user_id: int) -> List[Ticket]:
        """获取用户的所有工单"""
        return self.db.query(Ticket).filter(
            Ticket.user_id == user_id
        ).order_by(Ticket.created_at.desc()).all()
    
    def update_ticket_status(
        self,
        ticket_id: int,
        status: TicketStatus,
        assignee: Optional[str] = None,
        resolution: Optional[str] = None
    ) -> Optional[Ticket]:
        """
        更新工单状态
        
        Args:
            ticket_id: 工单ID
            status: 新状态
            assignee: 处理人
            resolution: 处理结果
        
        Returns:
            更新后的工单
        """
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None
        
        ticket.status = status
        if assignee:
            ticket.assignee = assignee
        if resolution:
            ticket.resolution = resolution
        
        self.db.commit()
        self.db.refresh(ticket)
        return ticket
    
    def get_pending_tickets(self) -> List[Ticket]:
        """获取所有待处理工单"""
        return self.db.query(Ticket).filter(
            Ticket.status == TicketStatus.PENDING
        ).order_by(Ticket.created_at.asc()).all()
    
    def get_ticket_summary(self, ticket: Ticket) -> str:
        """
        生成工单摘要信息
        
        Args:
            ticket: 工单对象
        
        Returns:
            格式化的摘要文本
        """
        status_map = {
            TicketStatus.PENDING: "待处理",
            TicketStatus.PROCESSING: "处理中",
            TicketStatus.RESOLVED: "已解决",
            TicketStatus.CLOSED: "已关闭"
        }
        
        summary = f"""工单号：{ticket.id}
类型：{ticket.ticket_type}
标题：{ticket.title}
状态：{status_map.get(ticket.status, "未知")}
创建时间：{ticket.created_at.strftime('%Y-%m-%d %H:%M')}"""
        
        if ticket.assignee:
            summary += f"\n处理人：{ticket.assignee}"
        
        if ticket.resolution:
            summary += f"\n处理结果：{ticket.resolution}"
        
        return summary
