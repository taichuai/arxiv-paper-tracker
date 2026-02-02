# arXiv Paper Tracker

语音方向论文自动追踪和智能分析系统

## 功能特点

- 🔄 **自动获取**: 每天定时从 arXiv 获取语音相关论文
- 🤖 **智能分析**: LLM 生成中文摘要、提取关键词、分类和评分
- 🏆 **每周精选**: 自动推荐创新性最高的论文
- 🔍 **高级搜索**: 全文搜索 + 机构/评分/日期多维度筛选
- 📱 **消息推送**: 支持飞书和微信推送
- 📚 **BibTeX 导出**: 一键复制或批量导出引用
- 💻 **代码链接**: 自动提取 GitHub 仓库地址

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourname/arxiv-paper-tracker.git
cd arxiv-paper-tracker

# 2. 配置环境变量（重要！）
cd backend
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 3. 启动后端
pip install -r requirements.txt
python -m app.main

# 4. 启动前端（新终端）
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 开始使用

---

## ⚠️ 配置说明（重要）

本项目有两个配置文件，请务必区分：

| 文件 | 内容 | 是否提交 Git |
|------|------|-------------|
| `backend/.env` | **敏感凭证**（API Keys, Webhook URLs） | ❌ 不提交 |
| `backend/config.yaml` | **业务配置**（分类、关键词、机构列表） | ✅ 可提交 |

### 1. 环境变量配置 (`backend/.env`)

**此文件包含敏感信息，不会被 Git 提交**

```bash
# 复制模板
cp .env.example .env
```

然后编辑 `.env` 文件：

```bash
# ============================================================
# LLM API Keys（至少配置一个）
# ============================================================

# Groq（免费，推荐）
# 获取: https://console.groq.com/keys
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx

# Anthropic Claude（可选）
# 获取: https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 或你的代理地址

# OpenAI（可选）
# 获取: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-xxxxxxxx

# ============================================================
# 消息推送凭证（可选）
# ============================================================

# 飞书机器人
# 获取: 飞书群 -> 设置 -> 机器人 -> 添加自定义机器人 -> 复制 Webhook
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxx

# 微信推送（三选一）
# - PushPlus: https://pushplus.plus 获取 Token
# - Server酱: https://sct.ftqq.com 获取 SendKey
# - 企业微信: 群机器人 Webhook URL
WECHAT_PUSH_TOKEN=your_token
```

### 2. 业务配置 (`backend/config.yaml`)

**此文件可以提交 Git，用于共享配置**

主要配置项：

```yaml
# arXiv 分类
arxiv:
  categories: ["cs.SD", "eess.AS", "cs.CL"]
  days_back: 7  # 获取最近几天的论文

# LLM Provider（按优先级排序，自动切换）
llm:
  providers:
    - name: "groq"           # 免费，优先使用
      model: "llama-3.3-70b-versatile"
      enabled: true
    - name: "anthropic"      # 备选
      model: "claude-sonnet-4-5-20250514"
      enabled: true

# 研究兴趣（影响论文评分）
research_interests:
  primary:
    - "text-to-speech"
    - "TTS"
    - "speech synthesis"

# 消息推送（凭证在 .env 中配置）
notification:
  enabled: true
  push_time: "09:30"
  keywords:              # 匹配这些关键词的论文会推送
    - "TTS"
    - "speech synthesis"
  min_score: 7.0         # 只推送评分 >= 7 的论文
  feishu:
    enabled: true        # 开关，Webhook 在 .env 中
  wechat:
    enabled: false
    channel: "pushplus"  # serverchan | pushplus | wecom

# 头部机构（用于高亮显示）
top_institutions:
  - "Google"
  - "OpenAI"
  - "MIT"
  - "Tsinghua"
  # ... 完整列表见 config.yaml
```

---

## 消息推送配置

### 飞书机器人

1. 打开飞书群 → 设置 → 机器人
2. 添加「自定义机器人」
3. 复制 Webhook 地址
4. 填入 `.env` 的 `FEISHU_WEBHOOK_URL`
5. 在 `config.yaml` 中设置 `notification.feishu.enabled: true`

### 微信推送

支持三种渠道：

| 渠道 | 获取地址 | .env 配置 |
|------|----------|-----------|
| **PushPlus**（推荐） | https://pushplus.plus | Token |
| Server酱 | https://sct.ftqq.com | SendKey |
| 企业微信 | 群机器人 Webhook | 完整 URL |

配置步骤：
1. 注册并获取 Token
2. 填入 `.env` 的 `WECHAT_PUSH_TOKEN`
3. 在 `config.yaml` 中设置：
   ```yaml
   notification:
     wechat:
       enabled: true
       channel: "pushplus"  # 或 serverchan / wecom
   ```

### 测试推送

```bash
# 预览将推送的论文
curl http://localhost:8000/api/tasks/notify-preview

# 手动触发推送
curl -X POST http://localhost:8000/api/tasks/notify-now
```

---

## API 接口

| 接口 | 说明 |
|------|------|
| `GET /api/papers/` | 论文列表 |
| `GET /api/papers/search?q=TTS` | 搜索论文 |
| `GET /api/papers/featured/weekly` | 每周精选 |
| `GET /api/papers/{id}/bibtex` | 获取 BibTeX |
| `GET /api/papers/export/bibtex?bookmarked_only=true` | 导出收藏 |
| `POST /api/tasks/fetch-now` | 手动获取论文 |
| `POST /api/tasks/notify-now` | 手动推送 |
| `GET /api/config/` | 获取配置 |

完整文档: http://localhost:8000/docs

---

## 目录结构

```
arxiv-paper-tracker/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── services/      # 业务逻辑
│   │   └── models/        # 数据模型
│   ├── config.yaml        # 业务配置 ✅ 可提交
│   ├── .env.example       # 环境变量模板 ✅ 可提交
│   └── .env               # 环境变量 ❌ 不提交
├── frontend/
│   └── src/
├── data/
│   └── papers.db          # SQLite 数据库
└── README.md
```

---

## 开源前检查清单

如果你要 fork 或开源此项目：

- [ ] **不要提交 `backend/.env`**（已在 .gitignore 中）
- [ ] 确认 `config.yaml` 中没有敏感信息
- [ ] 可选：清空 `data/papers.db`

---

## 常见问题

### Q: LLM 配额用完了怎么办？
A: 系统会自动切换到下一个 Provider。建议同时配置 Groq（免费）+ Claude。

### Q: 推送没收到？
A: 检查：
1. `.env` 中的 Webhook/Token 是否正确
2. `config.yaml` 中对应渠道的 `enabled` 是否为 `true`
3. 调用 `/api/tasks/notify-preview` 查看是否有匹配的论文

### Q: 如何修改头部机构列表？
A: 编辑 `config.yaml` 中的 `top_institutions`，前端会自动同步。

### Q: 如何添加新的 arXiv 分类？
A: 编辑 `config.yaml` 中的 `arxiv.categories`。

---

## 许可证

MIT License
