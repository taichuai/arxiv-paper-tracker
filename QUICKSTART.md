# 快速开始指南

## 第一步：安装依赖

### 后端依赖
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### 前端依赖
```bash
cd frontend
npm install
cd ..
```

## 第二步：配置 API Key

1. 复制环境变量模板：
```bash
cd backend
cp .env.example .env
```

2. 编辑 `backend/.env`，填入你的 API Key：

**使用 OpenAI (推荐):**
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxx
```

**或使用 Anthropic:**
```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxx
```

如果使用 Anthropic，还需要修改 `backend/config.yaml`:
```yaml
llm:
  provider: "anthropic"
  model: "claude-3-5-haiku-20241022"
```

## 第三步：测试系统（可选）

运行快速测试（不需要 API Key）：
```bash
cd backend
source venv/bin/activate
cd ..
python3 test_fetch.py
```

这将：
- 初始化数据库
- 从 arXiv 获取最新论文
- 显示前 3 篇论文预览
- 保存到数据库

## 第四步：启动服务

### 方式 1: 手动启动（推荐用于开发）

**终端 1 - 启动后端:**
```bash
cd backend
source venv/bin/activate
python -m app.main
```

**终端 2 - 启动前端:**
```bash
cd frontend
npm run dev
```

### 方式 2: 使用启动脚本
```bash
./run.sh
```

## 第五步：使用系统

1. 打开浏览器访问: http://localhost:5173

2. 首次使用点击 **"立即获取论文"** 按钮

3. 等待 2-3 分钟（获取 + LLM 分析）

4. 刷新页面查看结果

## 主要功能

### 📋 论文列表
- 查看所有论文
- 按日期/相关性排序
- 按分类筛选
- 收藏重要论文

### 📄 论文详情
- 查看中文摘要
- 查看关键词
- 跳转到 PDF/arXiv

### ⚙️ 自动化
- 每天早上 9:00 自动获取新论文
- 可在 `config.yaml` 中修改时间

### 🔧 手动操作
- 立即获取: 点击顶部按钮
- API 触发: `POST http://localhost:8000/api/tasks/fetch-now`

## API 文档

访问 http://localhost:8000/docs 查看完整 API 文档

## 常用配置

### 修改获取时间
编辑 `backend/config.yaml`:
```yaml
scheduler:
  fetch_time: "09:00"  # 修改为你想要的时间
```

### 修改研究兴趣
编辑 `backend/config.yaml`:
```yaml
research_interests:
  primary:
    - "text-to-speech"
    - "voice cloning"
    # 添加你的关键词...
```

### 禁用定时任务
编辑 `backend/config.yaml`:
```yaml
scheduler:
  enabled: false
```

## 故障排除

### 后端启动失败
- 检查 Python 版本 >= 3.10
- 检查是否激活了虚拟环境
- 检查 `.env` 文件是否存在

### 前端启动失败
- 检查 Node.js 版本 >= 18
- 删除 `node_modules` 重新安装

### 获取论文失败
- 检查网络连接
- 检查 arXiv API 是否可访问
- 查看 `logs/app.log` 日志

### LLM 分析失败
- 检查 API Key 是否正确
- 检查账户余额
- 查看日志中的错误信息

## 数据位置

- 数据库: `data/papers.db`
- 日志: `logs/app.log`

## 下一步

- 配置个性化的研究兴趣
- 探索不同的筛选和排序方式
- 定期查看收藏的论文
- 导出重要论文信息

## 技术支持

如有问题，请查看：
- README.md - 完整文档
- http://localhost:8000/docs - API 文档
- logs/app.log - 日志文件
