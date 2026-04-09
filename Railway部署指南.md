# 部署到Railway完整指南

## 🚀 5分钟快速部署

### 前提条件
- GitHub账号（免费注册）
- 企业微信应用已创建（有CorpID、AgentId、Secret）
- DeepSeek API密钥已申请

---

## 第一步：上传代码到GitHub

### 方法A：网页上传（最简单）

1. **创建GitHub仓库**
   - 访问 https://github.com/new
   - 仓库名：`customer-service`
   - 设为Private（私有）
   - 点击"Create repository"

2. **上传所有文件**
   - 在仓库页面点击"uploading an existing file"
   - 将以下所有文件拖拽上传：
     - main.py
     - config.py
     - database.py
     - models.py
     - init_data.py
     - requirements.txt
     - Procfile
     - runtime.txt
     - railway.json
     - .env.example
     - start.sh
     - knowledge_sample.json
     - services/ 文件夹下的所有.py文件
   - 点击"Commit changes"

### 方法B：使用Git命令（如果已安装Git）

```bash
# 在项目目录打开终端
git init
git add .
git commit -m "初始化客服系统"
git branch -M main
git remote add origin https://github.com/你的用户名/customer-service.git
git push -u origin main
```

---

## 第二步：在Railway创建项目

1. **登录Railway**
   - 访问 https://railway.app/
   - 点击"Start a New Project"
   - 选择"Login with GitHub"
   - 授权Railway访问你的GitHub

2. **部署代码**
   - 点击"Deploy from GitHub repo"
   - 选择你刚创建的 `customer-service` 仓库
   - 点击"Deploy Now"

3. **等待构建**
   - Railway会自动检测Python项目
   - 自动安装依赖
   - 构建过程约2-3分钟
   - 看到"SUCCESS"表示构建成功

---

## 第三步：添加PostgreSQL数据库

1. 在Railway项目页面，点击右上角"+ New"
2. 选择"Database" → "Add PostgreSQL"
3. Railway会自动创建数据库并生成连接字符串

---

## 第四步：配置环境变量

在Railway项目页面，点击你的服务（customer-service），进入"Variables"标签，添加以下变量：

### 必填项（从企业微信获取）：
```
WECHAT_CORP_ID=你的企业ID
WECHAT_AGENT_ID=你的应用AgentId
WECHAT_SECRET=你的应用Secret
WECHAT_TOKEN=你的回调Token
WECHAT_ENCODING_AES_KEY=你的回调EncodingAESKey
```

### 必填项（从DeepSeek获取）：
```
DEEPSEEK_API_KEY=你的DeepSeek API密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 自动生成（Railway已配置）：
```
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

**添加方式：**
- 点击"New Variable"
- 输入变量名和值
- 点击"Add"
- 重复以上步骤添加所有变量

---

## 第五步：获取公网地址

1. 在Railway项目页面，点击你的服务
2. 进入"Settings"标签
3. 点击"Generate Domain"
4. Railway会分配一个域名，如：`customer-service.up.railway.app`

你的服务地址就是：
```
https://customer-service.up.railway.app
```

---

## 第六步：初始化数据库

Railway部署后，需要手动初始化知识库数据：

**方法A：使用Railway CLI（推荐）**

```bash
# 安装Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 连接到你的项目
railway link

# 运行初始化脚本
railway run python init_data.py
```

**方法B：临时添加自动初始化代码**

修改 `main.py` 文件的 `startup_event` 函数：

```python
@app.on_event("startup")
async def startup_event():
    print("🚀 正在初始化数据库...")
    init_db()
    
    # 自动初始化知识库
    from init_data import init_knowledge_base
    init_knowledge_base()
    
    print("✅ 数据库初始化完成")
```

提交代码后Railway会自动重新部署。

---

## 第七步：配置企业微信回调

1. 登录企业微信管理后台
2. 进入你的应用 → 设置API接收
3. 填写回调URL：
   ```
   https://你的Railway域名/wechat/callback
   ```
4. 点击保存，验证通过后完成

---

## 第八步：测试功能

访问以下地址测试：

```bash
# 测试服务状态
https://你的Railway域名/

# 查看API文档
https://你的Railway域名/docs

# 查看知识库
https://你的Railway域名/api/knowledge
```

在企业微信中给你的应用发送消息，测试智能回复。

---

## 🎉 部署成功！

你的智能客服系统现在已经运行在云端，24小时在线。

### 查看日志
在Railway项目页面，点击服务 → "Deployments" → 点击最新部署 → "View Logs"

### 监控用量
Railway免费额度：
- 500小时运行时间/月
- 1GB数据库存储
- 查看用量：项目页面右上角显示

### 如何更新代码
```bash
# 修改代码后，提交到GitHub
git add .
git commit -m "更新功能"
git push

# Railway会自动检测并重新部署
```

---

## ⚠️ 常见问题

### 问题1：构建失败
**原因**：依赖安装失败或Python版本不兼容  
**解决**：检查 `requirements.txt` 和 `runtime.txt`

### 问题2：数据库连接失败
**原因**：DATABASE_URL未正确设置  
**解决**：在Variables中添加 `DATABASE_URL=${{Postgres.DATABASE_URL}}`

### 问题3：企业微信回调验证失败
**原因**：服务未启动或Token配置错误  
**解决**：
- 检查服务状态（访问根路径）
- 检查环境变量是否正确

### 问题4：大模型调用失败
**原因**：API密钥错误或余额不足  
**解决**：
- 检查DEEPSEEK_API_KEY是否正确
- 登录DeepSeek查看余额

---

## 💰 免费额度说明

Railway免费套餐包含：
- **$5额度/月**（约350小时运行时间）
- 1GB PostgreSQL数据库
- 100GB出站流量

对于你的使用场景（100单/日）：
- 运行时间：约200-300小时/月
- 数据库：对话记录约50MB/月
- **完全够用，不用担心超额**

如果超出免费额度：
- Railway会暂停服务
- 需要绑定信用卡继续使用（约$5/月）

---

## 🔄 其他免费平台备选

如果Railway不满足需求，可以尝试：

### Render（备选1）
- 750小时免费运行时间
- 更大额度，但冷启动慢
- https://render.com/

### Zeabur（备选2）
- 国内访问更快
- $5免费额度
- https://zeabur.com/

### Koyeb（备选3）
- 免费实例
- 欧洲服务器
- https://www.koyeb.com/

---

**现在开始部署吧！按照上面的步骤，5-10分钟就能完成。如果遇到问题随时问我！**
