from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models import Paper, PaperAnalysis
from app.core.config import get_config
import logging
import json
import os

logger = logging.getLogger(__name__)


class LLMProcessor:
    """LLM 论文分析处理器 - 支持多 Provider 自动切换"""

    def __init__(self, db: Session):
        self.db = db
        self.config = get_config()
        self.llm_config = self.config["llm"]
        self.research_interests = self.config.get("research_interests", {})
        self.subcategories = self.config.get("subcategories", [])
        self.featured_config = self.config.get("featured", {})

        # 初始化可用的 LLM 客户端列表
        self.clients = self._init_clients()

    def _init_clients(self) -> List[Dict]:
        """初始化多个 LLM 客户端，按优先级排序"""
        clients = []
        providers = self.llm_config.get("providers", [])

        for provider_config in providers:
            if not provider_config.get("enabled", True):
                continue

            name = provider_config.get("name")
            model = provider_config.get("model")

            try:
                client = self._create_client(name)
                if client:
                    clients.append({
                        "name": name,
                        "model": model,
                        "client": client
                    })
                    logger.info(f"✓ LLM Provider 初始化成功: {name} ({model})")
            except Exception as e:
                logger.warning(f"LLM Provider 初始化失败 {name}: {e}")

        if not clients:
            logger.warning("没有可用的 LLM Provider")

        return clients

    def _create_client(self, provider: str):
        """创建单个 LLM 客户端"""
        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                return None
            from openai import OpenAI
            return OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )

        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            base_url = os.getenv("ANTHROPIC_BASE_URL")
            if not api_key:
                return None
            from anthropic import Anthropic
            if base_url:
                return Anthropic(api_key=api_key, base_url=base_url)
            return Anthropic(api_key=api_key)

        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return None
            from openai import OpenAI
            return OpenAI(api_key=api_key)

        return None

    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用 LLM，自动切换 Provider"""
        for provider_info in self.clients:
            name = provider_info["name"]
            model = provider_info["model"]
            client = provider_info["client"]

            try:
                logger.debug(f"尝试使用 {name} ({model})...")

                if name in ["openai", "groq"]:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "你是一个语音技术领域的专家助手，擅长评估学术论文的创新性和价值。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=self.llm_config.get("temperature", 0.3),
                        max_tokens=self.llm_config.get("max_tokens", 800),
                    )
                    return response.choices[0].message.content

                elif name == "anthropic":
                    response = client.messages.create(
                        model=model,
                        max_tokens=self.llm_config.get("max_tokens", 800),
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return response.content[0].text

            except Exception as e:
                error_msg = str(e)
                # 检查是否是限额错误
                if "429" in error_msg or "rate_limit" in error_msg.lower() or "quota" in error_msg.lower():
                    logger.warning(f"{name} 限额已用完，尝试下一个 Provider...")
                    continue
                else:
                    logger.error(f"{name} 调用失败: {e}")
                    continue

        logger.error("所有 LLM Provider 都不可用")
        return None

    def process_paper(self, paper: Paper) -> Optional[PaperAnalysis]:
        """处理单篇论文"""
        if not self.clients:
            logger.warning(f"没有可用的 LLM 客户端，跳过论文处理: {paper.arxiv_id}")
            return None

        # 检查是否已处理
        existing = self.db.query(PaperAnalysis).filter(PaperAnalysis.paper_id == paper.id).first()
        if existing:
            logger.debug(f"论文已处理，跳过: {paper.arxiv_id}")
            return existing

        try:
            # 构建提示词
            prompt = self._build_prompt(paper)

            # 调用 LLM（自动切换）
            result_text = self._call_llm(prompt)
            if not result_text:
                return None

            # 解析结果
            analysis_result = self._parse_llm_response(result_text)

            # 创建分析记录
            analysis = PaperAnalysis(
                paper_id=paper.id,
                chinese_summary=analysis_result.get("chinese_summary"),
                keywords=analysis_result.get("keywords"),
                subcategory=analysis_result.get("subcategory"),
                relevance_score=analysis_result.get("relevance_score"),
                affiliations=analysis_result.get("affiliations"),
                innovation_score=analysis_result.get("innovation_score"),
                innovation_reason=analysis_result.get("innovation_reason"),
                github_url=analysis_result.get("github_url"),
            )

            self.db.add(analysis)
            self.db.commit()

            innovation_str = f" | 创新: {analysis.innovation_score}" if analysis.innovation_score else ""
            logger.info(f"✓ 论文分析完成: {paper.arxiv_id} | 分类: {analysis.subcategory} | 相关: {analysis.relevance_score}{innovation_str}")
            return analysis

        except Exception as e:
            logger.error(f"处理论文失败 {paper.arxiv_id}: {e}")
            self.db.rollback()
            return None

    def _build_prompt(self, paper: Paper) -> str:
        """构建 LLM 提示词（优化版，减少 token 消耗）"""
        subcategories_str = "、".join(self.subcategories)

        # 截断过长的摘要（节省 token）
        abstract = paper.abstract
        if len(abstract) > 800:
            abstract = abstract[:800] + "..."

        # 简化的提示词
        prompt = f"""分析语音领域论文，返回 JSON：

标题: {paper.title}
作者: {paper.authors}
摘要: {abstract}

要求：
1. chinese_summary: 2句中文摘要
2. keywords: 5个技术关键词
3. subcategory: 从 [{subcategories_str}] 选一个
4. relevance_score: 与TTS/语音合成的相关性(0-10)
5. affiliations: 推断作者机构(如Google/清华等)
6. innovation_score: 创新性评分(0-10)
7. innovation_reason: 一句话说明创新点
8. github_url: 提取GitHub链接或null

返回JSON：
{{"chinese_summary":"","keywords":[],"subcategory":"","relevance_score":0,"affiliations":[],"innovation_score":0,"innovation_reason":"","github_url":null}}"""

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
            required_fields = ["chinese_summary", "keywords", "subcategory", "relevance_score", "affiliations", "innovation_score", "innovation_reason", "github_url"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"LLM 响应缺少字段: {field}")
                    result[field] = self._get_default_value(field)

            return result

        except json.JSONDecodeError as e:
            logger.error(f"解析 LLM 响应失败: {e}\n响应内容: {response_text[:500]}")
            return {
                "chinese_summary": "解析失败",
                "keywords": [],
                "subcategory": "其他",
                "relevance_score": 0.0,
                "affiliations": [],
                "innovation_score": 0.0,
                "innovation_reason": "",
                "github_url": None
            }

    def _get_default_value(self, field: str):
        """获取字段默认值"""
        defaults = {
            "chinese_summary": "暂无摘要",
            "keywords": [],
            "subcategory": "其他",
            "relevance_score": 0.0,
            "affiliations": [],
            "innovation_score": 0.0,
            "innovation_reason": "",
            "github_url": None
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
