# Groq API 配置指南

## 为什么选择 Groq？

- ✅ **完全免费**：每日 14,400 次请求额度
- ✅ **速度极快**：推理速度是 OpenAI 的 10 倍以上
- ✅ **API 兼容**：使用 OpenAI 兼容格式，改动最小
- ✅ **模型质量好**：支持 Llama 3.3 70B、Mixtral 等优质开源模型

## 获取 Groq API Key

### 步骤 1：注册账号
1. 访问 https://console.groq.com
2. 点击右上角 "Sign Up" 注册账号
3. 可以使用 Google/GitHub 账号快速注册

### 步骤 2：创建 API Key
1. 登录后，点击左侧菜单 "API Keys"
2. 点击 "Create API Key" 按钮
3. 给 Key 起个名字（比如 "arxiv-tracker"）
4. 点击 "Create" 创建
5. **重要**：立即复制显示的 API Key（格式类似：`gsk_...`）

### 步骤 3：配置到项目
1. 打开文件：`backend/.env`
2. 找到这一行：
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
3. 替换为你的真实 API Key：
   ```
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
4. 保存文件

### 步骤 4：重启服务
```bash
# 停止当前运行的服务（按 Ctrl+C）
# 然后重新运行
./run.sh
```

## 推荐模型

在 `backend/config.yaml` 中已配置好：

```yaml
llm:
  provider: "groq"
  model: "llama-3.3-70b-versatile"  # 推荐：速度快，质量高
```

### 其他可选模型：
- `llama-3.3-70b-versatile` - 最强，推荐使用
- `llama-3.1-70b-versatile` - 上一代，也很好
- `mixtral-8x7b-32768` - 更快，但质量稍低
- `gemma2-9b-it` - 最快，适合简单任务

## 测试 API

配置完成后，点击前端的 "立即获取论文" 按钮，应该可以看到：
- 中文摘要
- 关键词提取
- 子领域分类
- 相关性评分

## 常见问题

### Q: Groq 有什么限制吗？
A: 免费版限制：
- 每日 14,400 次请求
- 每分钟 30 次请求
- 对个人使用完全够用

### Q: 如果额度用完了怎么办？
A:
1. 等到第二天额度会重置
2. 或者在 `config.yaml` 中切换到其他免费 API（如 DeepSeek）

### Q: 模型质量如何？
A: Llama 3.3 70B 在中文和技术领域的表现非常好，完全可以替代 GPT-4o-mini。

### Q: 数据安全吗？
A: Groq 承诺不使用 API 请求数据训练模型，与 OpenAI 一样安全。

## 其他免费替代方案

如果 Groq 不满意，还可以尝试：

### DeepSeek（超便宜，中文好）
```yaml
llm:
  provider: "openai"  # 使用 OpenAI 兼容格式
  model: "deepseek-chat"
```
在 `.env` 中：
```
OPENAI_API_KEY=你的_deepseek_key
```
需要修改 `llm_processor.py` 添加 base_url

### Google Gemini（免费额度大）
需要额外修改代码适配 Gemini API

---

**配置完成后，enjoy your free AI-powered paper tracker! 🚀**
