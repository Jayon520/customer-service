"""
数据库初始化脚本
"""
from database import SessionLocal
from services.knowledge_service import KnowledgeService


def init_knowledge_base():
    """初始化知识库示例数据"""
    db = SessionLocal()
    service = KnowledgeService(db)
    
    # 示例知识库数据
    knowledge_data = [
        {
            "title": "产品保修政策",
            "content": "所有产品自购买之日起享受12个月保修服务。保修期内，非人为损坏可免费维修或更换。需要提供购买凭证。",
            "category": "产品使用",
            "keywords": "保修,售后,维修"
        },
        {
            "title": "退货流程",
            "content": "退货流程：1. 提交退货申请，说明退货原因；2. 客服审核通过后发送退货地址；3. 寄回商品并上传快递单号；4. 收到商品确认无误后3-5个工作日退款。",
            "category": "退换货",
            "keywords": "退货,退款,流程"
        },
        {
            "title": "换货流程",
            "content": "换货流程：1. 提交换货申请，说明换货原因和需要的商品规格；2. 客服确认库存后发送换货地址；3. 寄回原商品；4. 收到商品后发出新商品。",
            "category": "退换货",
            "keywords": "换货,更换,流程"
        },
        {
            "title": "退款到账时间",
            "content": "退款时间：支付宝/微信支付1-3个工作日到账，银行卡3-7个工作日到账。如有延迟请联系客服。",
            "category": "退换货",
            "keywords": "退款,到账,时间"
        },
        {
            "title": "产品使用问题排查",
            "content": "如果产品无法正常使用，请尝试：1. 检查电源是否连接正常；2. 确认操作步骤是否正确；3. 重启设备；4. 查看说明书常见问题部分。如仍无法解决，请联系人工客服。",
            "category": "产品使用",
            "keywords": "故障,问题,排查,无法使用"
        }
    ]
    
    print("📚 正在导入知识库数据...")
    for item in knowledge_data:
        service.add_knowledge(
            title=item["title"],
            content=item["content"],
            category=item["category"],
            keywords=item["keywords"]
        )
    
    print("✅ 知识库初始化完成，共导入5条数据")
    db.close()


if __name__ == "__main__":
    init_knowledge_base()
