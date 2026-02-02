from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Paper, PaperAnalysis
from app.core.config import get_config
import logging
import json

logger = logging.getLogger(__name__)


class LLMProcessor:
    """LLM 论文分析处理器"""

    def __init__(self, db: Session):
        self.db = db
        self.config = get_config()
        self.llm_config = self.config["llm"]
        self.research_interests = self.config.get("research_interests", {})
        self.subcategories = self.config.get("subcategories", [])

        # 初始化 LLM 客户端
        self.client = self._init_client()

    def _init_client(self):
        """初始化 LLM 客户端"""
        provider = self.llm_config.get("provider", "openai")
        api_key = self.llm_config.get("api_key")

        if not api_key:
            logger.warning("未配置 LLM API Key，LLM 功能将被禁用")
            return None

        if provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=api_key)
        elif provider == "groq":
            from openai import OpenAI
            # Groq 使用 OpenAI 兼容的 API
            return OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
        elif provider == "anthropic":
            from anthropic import Anthropic
            return Anthropic(api_key=api_key)
        else:
            raise ValueError(f"不支持的 LLM provider: {provider}")

    def process_paper(self, paper: Paper) -> Optional[PaperAnalysis]:
        """处理单篇论文"""
        if not self.client:
            logger.warning(f"LLM 客户端未初始化，跳过论文处理: {paper.arxiv_id}")
            return None

        # 检查是否已处理
        existing = self.db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper.id).first()
        if existing:
            logger.debug(f"论文已处理，跳过: {paper.arxiv_id}")
            return existing

        try:
            # 调用 LLM 分析
            analysis_result = self._analyze_with_llm(paper)

            # 创建分析记录
            analysis = PaperAnalysis(
                paper_id=paper.id,
                chinese_summary=analysis_result.get("chinese_summary"),
                keywords=analysis_result.get("keywords"),
                subcategory=analysis_result.get("subcategory"),
                relevance_score=analysis_result.get("relevance_score"),
            )

            self.db.add(analysis)
            self.db.commit()

            logger.info(f"✓ 论文分析完成: {paper.arxiv_id} | 分类: {analysis.subcategory} | 评分: {analysis.relevance_score}")
            return analysis

        except Exception as e:
            logger.error(f"处理论文失败 {paper.arxiv_id}: {e}")
            self.db.rollback()
            return None

    def _analyze_with_llm(self, paper: Paper) -> Dict:
        """使用 LLM 分析论文"""
        provider = self.llm_config.get("provider")
        model = self.llm_config.get("model")

        # 构建提示词
        prompt = self._build_prompt(paper)

        # 调用 LLM
        if provider in ["openai", "groq"]:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个语音技术领域的专家助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.llm_config.get("temperature", 0.3),
                max_tokens=self.llm_config.get("max_tokens", 500),
            )
            result_text = response.choices[0].message.content

        elif provider == "anthropic":
            response = self.client.messages.create(
                model=model,
                max_tokens=self.llm_config.get("max_tokens", 500),
                temperature=self.llm_config.get("temperature", 0.3),
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            result_text = response.content[0].text

        else:
            raise ValueError(f"不支持的 provider: {provider}")

        # 解析结果
        return self._parse_llm_response(result_text)

    def _build_prompt(self, paper: Paper) -> str:
        """构建 LLM 提示词"""
        subcategories_str = "、".join(self.subcategories)

        # 研究兴趣关键词
        interests_str = ""
        if self.research_interests:
            primary = self.research_interests.get("primary", [])
            secondary = self.research_interests.get("secondary", [])
            interests_str = f"\n主要研究兴趣: {', '.join(primary)}\n次要研究兴趣: {', '.join(secondary)}"

        prompt = f"""请分析以下语音领域的学术论文，提供结构化的分析结果。

**论文信息：**
标题: {paper.title}
摘要: {paper.abstract}
{interests_str}

**任务要求：**
1. 生成 2-3 句话的中文摘要，突出核心创新点
2. 提取 5-8 个技术关键词（中英文均可）
3. 将论文分类到以下子领域之一：{subcategories_str}
4. 基于研究兴趣给出相关性评分（0-10分，10分最相关）

**输出格式（必须严格遵守 JSON 格式）：**
```json
{{
  "chinese_summary": "中文摘要内容",
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "subcategory": "子领域分类",
  "relevance_score": 8.5
}}
```

请直接返回 JSON，不要添加任何其他内容。"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict:
        """解析 LLM 响应"""
        try:
            # 尝试提取 JSON 代码块
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            result = json.loads(json_str)

            # 验证必需字段
            required_fields = ["chinese_summary", "keywords", "subcategory", "relevance_score"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"LLM 响应缺少字段: {field}")
                    result[field] = self._get_default_value(field)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"解析 LLM 响应失败: {e}\n响应内容: {response_text}")
            return {
                "chinese_summary": "解析失败",
                "keywords": [],
                "subcategory": "其他",
                "relevance_score": 0.0
            }

    def _get_default_value(self, field: str):
        """获取字段默认值"""
        defaults = {
            "chinese_summary": "暂无摘要",
            "keywords": [],
            "subcategory": "其他",
            "relevance_score": 0.0
        }
        return defaults.get(field)

    def process_unprocessed_papers(self, limit: int = 10) -> int:
        """批量处理未处理的论文"""
        # 查询未处理的论文
        unprocessed_papers = (
            self.db.query(Paper)
            .outerjoin(PaperAnalysis, Paper.id == PaperAnalysis.paper_id)
            .filter(PaperAnalysis.id == None)
            .order_by(Paper.published_date.desc())
            .limit(limit)
            .all()
        )

        if not unprocessed_papers:
            logger.info("没有需要处理的论文")
            return 0

        logger.info(f"开始处理 {len(unprocessed_papers)} 篇未处理的论文...")

        processed_count = 0
        for paper in unprocessed_papers:
            if self.process_paper(paper):
                processed_count += 1

        logger.info(f"✓ 批量处理完成，成功处理 {processed_count} 篇论文")
        return processed_count
