# arXiv Paper Tracker

语音方向论文自动追踪和智能分析系统

## 功能特点

- 🔄 **自动获取**: 每天定时从 arXiv 获取语音相关论文（cs.SD, eess.AS, cs.CL）
- 🤖 **智能分析**: 使用 LLM 生成中文摘要、提取关键词、分类和评分
- 🎯 **个性化推荐**: 基于研究兴趣的相关性评分
- 🔍 **高级筛选**: 支持按分类、日期、相关性等多维度筛选
- ⭐ **收藏管理**: 标记和管理感兴趣的论文
- 📊 **统计看板**: 查看论文统计和分布情况

## 系统架构

```
后端: Python + FastAPI + SQLAlchemy + APScheduler
前端: Vue 3 + Vite + TailwindCSS
数据库: SQLite
LLM: OpenAI GPT-4o-mini / Anthropic Claude
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- OpenAI API Key 或 Anthropic API Key

### 2. 后端设置

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 启动服务
python -m app.main
```

后端将在 http://localhost:8000 运行

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 运行

### 4. 首次使用

1. 访问 http://localhost:5173
2. 点击 "立即获取论文" 按钮
3. 等待几分钟，系统会自动获取并分析论文
4. 刷新页面查看结果

## 配置说明

### backend/config.yaml

主要配置项：

```yaml
arxiv:
  categories: ["cs.SD", "eess.AS", "cs.CL"]
  days_back: 2  # 获取最近几天的论文

llm:
  provider: "openai"  # 或 "anthropic"
  model: "gpt-4o-mini"  # 推荐使用 mini 版本，性价比高

research_interests:
  primary:
    - "text-to-speech"
    - "TTS"
    # 添加你的研究兴趣...

scheduler:
  enabled: true
  fetch_time: "09:00"  # 每天执行时间
```

### LLM 选择

**推荐方案 (性价比):**
- OpenAI GPT-4o-mini: ~$0.02-0.05/天 (20篇论文)
- 速度快，成本低

**替代方案:**
- Anthropic Claude 3.5 Haiku: ~$0.01-0.03/天
- 质量稍好，成本更低

## API 接口

### 论文相关

- `GET /api/papers/` - 获取论文列表
- `GET /api/papers/{id}` - 获取论文详情
- `POST /api/papers/{id}/bookmark` - 切换收藏状态
- `GET /api/papers/stats/summary` - 获取统计信息

### 任务相关

- `POST /api/tasks/fetch-now` - 手动触发论文获取
- `POST /api/tasks/process-papers` - 手动触发 LLM 处理
- `GET /api/tasks/status` - 获取调度器状态

完整 API 文档: http://localhost:8000/docs

## 使用技巧

### 1. 定制研究兴趣

编辑 `config.yaml` 中的 `research_interests` 部分，添加你关注的关键词。系统会根据这些关键词给论文打分。

### 2. 禁用定时任务

如果只想手动获取论文，可以在 `config.yaml` 中设置:

```yaml
scheduler:
  enabled: false
```

### 3. 批量处理已有论文

如果数据库中有未处理的论文，可以调用:

```bash
curl -X POST http://localhost:8000/api/tasks/process-papers
```

### 4. 数据备份

数据库文件位于 `data/papers.db`，定期备份即可。

## 目录结构

```
arxiv-paper-tracker/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── core/          # 配置和数据库
│   │   ├── models/        # 数据模型
│   │   ├── services/      # 业务逻辑
│   │   └── main.py        # 应用入口
│   ├── config.yaml        # 配置文件
│   ├── requirements.txt
│   └── .env               # 环境变量
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   └── App.vue
│   └── package.json
├── data/                  # 数据库目录
└── logs/                  # 日志目录
```

## 常见问题

### Q: LLM 处理太慢怎么办？

A: 可以调整 `llm.max_tokens` 和 `llm.temperature` 参数，或者使用更快的模型。

### Q: 如何添加其他 arXiv 分类？

A: 编辑 `config.yaml` 中的 `arxiv.categories` 列表。

### Q: 数据库太大怎么办？

A: 可以定期清理旧论文，或使用 PostgreSQL 替代 SQLite。

### Q: 能否离线使用？

A: 论文获取和 LLM 分析需要网络，但浏览已有数据可以离线。

## 开发计划

- [ ] 支持更多论文来源（Hugging Face Papers, Google Scholar）
- [ ] 论文相似度推荐
- [ ] 导出功能（Markdown, PDF）
- [ ] 多用户支持
- [ ] 移动端适配

## 许可证

MIT License

## 致谢

- arXiv API
- OpenAI / Anthropic
- FastAPI
- Vue.js
