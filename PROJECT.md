# arXiv Paper Tracker - 项目说明

## 📋 项目概览

这是一个完整的语音论文追踪系统，已经为你创建好所有核心功能。

### 🎯 核心功能

✅ **自动获取** - 每天定时从 arXiv 获取 cs.SD, eess.AS, cs.CL 分类的论文
✅ **智能分析** - 使用 GPT/Claude 生成中文摘要、提取关键词、分类
✅ **相关性评分** - 基于你的研究兴趣自动打分
✅ **Web 界面** - 现代化的论文浏览、筛选、收藏功能
✅ **统计看板** - 论文数量、分类分布、收藏统计

### 💻 技术栈

**后端:**
- FastAPI (Web 框架)
- SQLAlchemy (ORM)
- APScheduler (定时任务)
- arxiv (官方 Python 库)
- OpenAI/Anthropic SDK

**前端:**
- Vue 3
- Vite
- TailwindCSS
- Axios

**数据库:**
- SQLite (轻量级，无需额外配置)

## 📁 项目结构

```
arxiv-paper-tracker/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   ├── papers.py      # 论文相关接口
│   │   │   └── tasks.py       # 任务触发接口
│   │   ├── core/              # 核心配置
│   │   │   ├── config.py      # 配置加载
│   │   │   └── database.py    # 数据库连接
│   │   ├── models/            # 数据模型
│   │   │   └── paper.py       # Paper, PaperAnalysis, UserPreference
│   │   ├── services/          # 业务逻辑
│   │   │   ├── arxiv_fetcher.py    # arXiv 数据获取
│   │   │   ├── llm_processor.py    # LLM 分析处理
│   │   │   └── scheduler.py        # 定时调度器
│   │   └── main.py            # FastAPI 应用入口
│   ├── config.yaml            # 主配置文件 ⚙️
│   ├── .env                   # 环境变量（API Key）🔑
│   └── requirements.txt       # Python 依赖
│
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── views/
│   │   │   ├── PaperList.vue      # 论文列表页
│   │   │   └── PaperDetail.vue    # 论文详情页
│   │   ├── App.vue            # 根组件
│   │   └── main.js            # 应用入口
│   └── package.json           # npm 依赖
│
├── data/                      # 数据目录
│   └── papers.db              # SQLite 数据库
│
├── logs/                      # 日志目录
│   └── app.log
│
├── setup.sh                   # 一键安装脚本
├── run.sh                     # 启动脚本
├── test_fetch.py              # 快速测试脚本
├── README.md                  # 完整文档
└── QUICKSTART.md              # 快速开始指南
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 自动安装（推荐）
./setup.sh

# 或手动安装
cd backend && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..
```

### 2. 配置 API Key

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY
```

### 3. 启动服务

```bash
# 方式 1: 使用脚本
./run.sh

# 方式 2: 手动启动
# 终端 1
cd backend && source venv/bin/activate && python -m app.main

# 终端 2
cd frontend && npm run dev
```

### 4. 访问应用

- 前端: http://localhost:5173
- 后端: http://localhost:8000
- API 文档: http://localhost:8000/docs

## ⚙️ 重要配置文件

### backend/config.yaml

这是核心配置文件，你需要根据自己的需求修改：

```yaml
# 1. arXiv 配置
arxiv:
  categories:           # 要获取的分类
    - "cs.SD"
    - "eess.AS"
    - "cs.CL"
  days_back: 2         # 获取最近几天的论文

# 2. LLM 配置
llm:
  provider: "openai"   # 选择 LLM 提供商
  model: "gpt-4o-mini" # 模型名称

# 3. 研究兴趣（重要！）
research_interests:
  primary:             # 主要关注（权重高）
    - "text-to-speech"
    - "TTS"
    - "voice cloning"
  secondary:           # 次要关注
    - "ASR"
    - "speech recognition"

# 4. 定时任务
scheduler:
  enabled: true
  fetch_time: "09:00" # 每天执行时间
```

### backend/.env

```env
# OpenAI API Key
OPENAI_API_KEY=sk-xxxxxxxxxx

# 或 Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxx
```

## 📊 数据库设计

### papers 表
- 论文基本信息（标题、作者、摘要、PDF 链接等）

### paper_analysis 表
- LLM 分析结果（中文摘要、关键词、分类、评分）
- 用户交互（收藏、已读）

### user_preferences 表
- 用户偏好设置

## 🔄 工作流程

```
1. 定时触发 (每天 9:00)
   ↓
2. ArxivFetcher 获取论文
   ↓
3. 保存到 papers 表
   ↓
4. LLMProcessor 逐篇分析
   ↓
5. 保存到 paper_analysis 表
   ↓
6. Web 界面展示
```

## 🎨 前端页面

### 首页 (PaperList.vue)
- 统计卡片（总数、收藏、最近）
- 筛选栏（排序、分类、时间、收藏）
- 论文卡片列表
- 分页

### 详情页 (PaperDetail.vue)
- 完整论文信息
- 中文摘要
- 关键词标签
- 跳转到 PDF/arXiv

## 🔌 API 接口

### 论文相关
- `GET /api/papers/` - 获取论文列表
  - 参数: page, page_size, sort_by, subcategory, bookmarked_only, days
- `GET /api/papers/{id}` - 获取论文详情
- `POST /api/papers/{id}/bookmark` - 切换收藏
- `POST /api/papers/{id}/read` - 标记已读
- `GET /api/papers/stats/summary` - 获取统计

### 任务相关
- `POST /api/tasks/fetch-now` - 手动获取论文
- `POST /api/tasks/process-papers` - 手动处理论文
- `GET /api/tasks/status` - 获取调度器状态

## 💡 使用技巧

### 1. 个性化研究兴趣
修改 `config.yaml` 中的 `research_interests`，系统会据此给论文打分。

### 2. 禁用定时任务
如果只想手动获取：
```yaml
scheduler:
  enabled: false
```

### 3. 批量处理历史论文
```bash
curl -X POST http://localhost:8000/api/tasks/process-papers?limit=50
```

### 4. 查看日志
```bash
tail -f logs/app.log
```

## 💰 成本估算

假设每天 20 篇论文：

**OpenAI GPT-4o-mini:**
- 每篇约 $0.001-0.002
- 每天约 $0.02-0.04
- 每月约 $0.6-1.2

**Anthropic Claude 3.5 Haiku:**
- 每篇约 $0.0005-0.001
- 每天约 $0.01-0.02
- 每月约 $0.3-0.6

## 🐛 常见问题

### Q: 获取论文失败？
A: 检查网络连接，arXiv 可能有 API 限流

### Q: LLM 分析太慢？
A: 调整 `llm.max_tokens` 参数，或使用 mini 模型

### Q: 如何添加其他分类？
A: 在 `config.yaml` 的 `arxiv.categories` 中添加

### Q: 数据库在哪里？
A: `data/papers.db`，可以直接用 SQLite 工具打开

## 🔮 扩展建议

### 短期
- [ ] 添加搜索功能（标题、作者、关键词）
- [ ] 导出功能（Markdown、CSV）
- [ ] 论文笔记功能

### 中期
- [ ] 相似论文推荐
- [ ] 邮件通知
- [ ] RSS 订阅

### 长期
- [ ] 多用户支持
- [ ] 更多论文源（Hugging Face Papers）
- [ ] 移动端 App

## 📝 开发说明

### 添加新的子领域分类
1. 修改 `config.yaml` 中的 `subcategories`
2. LLM 会自动使用新的分类

### 修改 LLM Prompt
编辑 `backend/app/services/llm_processor.py` 中的 `_build_prompt` 方法

### 自定义前端样式
- 使用 TailwindCSS utility classes
- 或编辑 `frontend/src/style.css`

## 🙏 依赖项

- arxiv - arXiv API 客户端
- fastapi - Web 框架
- sqlalchemy - ORM
- apscheduler - 定时任务
- openai / anthropic - LLM SDK
- vue - 前端框架
- tailwindcss - CSS 框架

## 📄 许可证

MIT License

---

**祝你使用愉快！如有问题，请查看日志文件或 API 文档。**
