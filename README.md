# 智能售后客服系统

基于 **FastAPI + DeepSeek大模型 + 企业微信** 的智能客服系统。

## 🎯 功能特性

- ✅ 智能对话：基于DeepSeek大模型的智能问答
- ✅ 知识库管理：支持知识库检索，提升回答准确性
- ✅ 工单系统：自动创建退换货工单，支持查询
- ✅ 转人工：检测关键词自动转人工
- ✅ 多轮对话：记住上下文，支持连续对话
- ✅ 企业微信集成：完整的企业微信消息对接

## 📦 技术栈

- **后端框架**: FastAPI
- **数据库**: PostgreSQL
- **大模型**: DeepSeek V3
- **对接渠道**: 企业微信

## 🚀 快速开始

### 第一步：环境准备

1. **安装Python 3.9+**
   ```bash
   python --version
   ```

2. **安装PostgreSQL**
   - 下载地址: https://www.postgresql.org/download/
   - 安装后创建数据库:
     ```sql
     CREATE DATABASE customer_service;
     ```

### 第二步：项目安装

1. **克隆或下载项目**

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑.env文件，填入你的配置
   ```

### 第三步：申请企业微信应用

1. 登录企业微信管理后台: https://work.weixin.qq.com/

2. 进入「应用管理」→「自建应用」→「创建应用」

3. 获取应用信息:
   - **企业ID (CorpID)**: 在「我的企业」页面
   - **AgentId**: 应用的AgentId
   - **Secret**: 应用的Secret

4. 配置回调地址:
   - 进入应用详情页 → 「企业可信IP」和「接收消息」设置
   - 点击「设置API接收」
   - 填写回调URL: `http://你的服务器IP:8000/wechat/callback`
   - 设置Token和EncodingAESKey（自己定义或随机生成）
   - 点击保存（此时需要先启动服务器，否则验证不通过）

5. 将上述信息填入 `.env` 文件

### 第四步：申请DeepSeek API

1. 访问: https://platform.deepseek.com/

2. 注册账号并登录

3. 创建API密钥: https://platform.deepseek.com/api_keys

4. 将API密钥填入 `.env` 文件的 `DEEPSEEK_API_KEY`

### 第五步：初始化数据库

```bash
# 运行数据库初始化
python init_data.py
```

### 第六步：启动服务

```bash
# 开发模式启动（自动重载）
python main.py

# 或使用uvicorn启动
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 第七步：验证部署

1. 访问 `http://你的服务器IP:8000` 查看服务状态
2. 访问 `http://你的服务器IP:8000/docs` 查看API文档
3. 在企业微信中向应用发送消息测试

## 📁 项目结构

```
customer-service/
├── main.py                 # 主程序入口
├── config.py               # 配置文件
├── database.py             # 数据库连接
├── models.py               # 数据模型
├── init_data.py            # 初始化脚本
├── requirements.txt        # 依赖列表
├── .env.example           # 环境变量示例
├── README.md              # 说明文档
└── services/              # 服务层
    ├── llm_service.py     # 大模型服务
    ├── knowledge_service.py # 知识库服务
    ├── ticket_service.py  # 工单服务
    └── wechat_service.py  # 企业微信服务
```

## 🔧 配置说明

### .env 文件配置项

| 配置项 | 说明 | 获取方式 |
|--------|------|----------|
| WECHAT_CORP_ID | 企业微信企业ID | 企业微信后台「我的企业」 |
| WECHAT_AGENT_ID | 应用AgentId | 企业微信应用详情页 |
| WECHAT_SECRET | 应用Secret | 企业微信应用详情页 |
| WECHAT_TOKEN | 回调Token | 自己定义或随机生成 |
| WECHAT_ENCODING_AES_KEY | 回调加密密钥 | 自己定义或随机生成 |
| DEEPSEEK_API_KEY | DeepSeek API密钥 | DeepSeek平台创建 |
| DATABASE_URL | 数据库连接字符串 | PostgreSQL连接信息 |

## 💡 使用指南

### 1. 添加知识库

通过API添加知识库条目：

```bash
curl -X POST "http://localhost:8000/api/knowledge" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "如何重置密码",
    "content": "进入设置页面，点击重置密码，输入新密码即可",
    "category": "产品使用",
    "keywords": "密码,重置,设置"
  }'
```

或访问 `http://localhost:8000/docs` 使用可视化API界面。

### 2. 查看工单

```bash
curl "http://localhost:8000/api/tickets/pending"
```

### 3. 企业微信测试

- 发送文字消息，系统自动回复
- 发送"退货"、"换货"等关键词，自动创建工单
- 发送"人工"、"转人工"等关键词，提示转人工
- 发送"工单查询"，查看历史工单

## 🌐 部署到云服务器

### 1. 购买云服务器

推荐配置：
- 阿里云/腾讯云轻量服务器
- 2核4G内存
- Ubuntu 20.04 或 CentOS 7+
- 约 100元/月

### 2. 安装依赖

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python
sudo apt install python3 python3-pip -y

# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# 创建数据库
sudo -u postgres psql
CREATE DATABASE customer_service;
CREATE USER myuser WITH PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE customer_service TO myuser;
\q
```

### 3. 上传代码

```bash
# 使用scp或FTP工具上传项目文件到服务器
scp -r customer-service/ user@your-server-ip:/home/user/
```

### 4. 启动服务

```bash
# 进入项目目录
cd /home/user/customer-service

# 安装依赖
pip3 install -r requirements.txt

# 使用nohup后台运行
nohup python3 main.py > server.log 2>&1 &

# 或使用supervisor管理（推荐）
```

### 5. 配置域名和SSL（可选）

使用Nginx反向代理配置HTTPS：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 成本估算

以日咨询100单计算：

| 项目 | 成本 |
|------|------|
| 云服务器 | 100元/月 |
| DeepSeek API | ~150元/月（每单0.05元） |
| 域名+SSL | ~100元/年 |
| **总计** | **约250元/月** |

## 🐛 常见问题

### 1. 企业微信回调验证失败

**原因**: 服务器未启动或Token配置错误

**解决**: 
- 先启动服务器，再保存企业微信配置
- 检查Token和EncodingAESKey是否一致

### 2. DeepSeek API调用失败

**原因**: API密钥错误或余额不足

**解决**:
- 检查API密钥是否正确
- 登录DeepSeek平台查看余额

### 3. 数据库连接失败

**原因**: PostgreSQL未启动或连接信息错误

**解决**:
- 检查PostgreSQL服务状态
- 验证DATABASE_URL配置

### 4. 消息无法接收

**原因**: 防火墙未开放端口

**解决**:
```bash
# 开放8000端口
sudo ufw allow 8000
```

## 📚 学习资源

- FastAPI官方文档: https://fastapi.tiangolo.com/
- 企业微信开发文档: https://developers.work.weixin.qq.com/
- DeepSeek API文档: https://platform.deepseek.com/docs

## 🎉 下一步优化方向

1. **接入更多渠道**: 支持微信公众号、小程序
2. **增强知识库**: 使用向量数据库提升检索效果
3. **数据分析**: 客服数据统计和可视化
4. **工单流转**: 更复杂的工单分配和处理流程
5. **多租户**: 支持多个企业同时使用

## 📄 License

MIT License

---

**祝你的智能客服系统上线顺利！有问题随时问我。**
