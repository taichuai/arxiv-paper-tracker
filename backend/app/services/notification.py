"""
论文订阅推送服务
支持飞书和微信（Server酱、PushPlus、企业微信）推送
"""
import logging
import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import Paper, PaperAnalysis
from app.core.config import get_config

logger = logging.getLogger(__name__)


class NotificationService:
    """论文推送通知服务"""

    def __init__(self, db: Session):
        self.db = db
        self.config = get_config()
        self.notification_config = self.config.get("notification", {})
        self.web_config = self.config.get("web", {})
        self.frontend_url = self.web_config.get("frontend_url", "http://localhost:5173")

        # 从环境变量读取敏感凭证
        self.feishu_webhook = os.getenv("FEISHU_WEBHOOK_URL", "") or self.notification_config.get("feishu", {}).get("webhook_url", "")
        self.wechat_token = os.getenv("WECHAT_PUSH_TOKEN", "") or self.notification_config.get("wechat", {}).get("token", "")

    def get_matching_papers(self, hours: int = 24) -> List[Dict]:
        """获取匹配订阅条件的新论文"""
        if not self.notification_config.get("enabled", False):
            return []

        keywords = self.notification_config.get("keywords", [])
        institutions = self.notification_config.get("institutions", [])
        min_score = self.notification_config.get("min_score", 7.0)
        max_papers = self.notification_config.get("max_papers", 10)

        # 获取最近 N 小时的论文
        time_threshold = datetime.now() - timedelta(hours=hours)

        query = (
            self.db.query(Paper, PaperAnalysis)
            .join(PaperAnalysis, Paper.id == PaperAnalysis.paper_id)
            .filter(Paper.created_at >= time_threshold)
        )

        all_papers = query.all()
        matched_papers = []

        for paper, analysis in all_papers:
            # 检查评分
            score = analysis.relevance_score or 0
            if score < min_score:
                continue

            # 检查关键词匹配
            keyword_match = False
            title_lower = paper.title.lower()
            abstract_lower = paper.abstract.lower()
            for kw in keywords:
                if kw.lower() in title_lower or kw.lower() in abstract_lower:
                    keyword_match = True
                    break

            # 检查机构匹配
            institution_match = False
            affiliations = analysis.affiliations or []
            for aff in affiliations:
                if aff:
                    for inst in institutions:
                        if inst.lower() in aff.lower():
                            institution_match = True
                            break
                if institution_match:
                    break

            # 满足任一条件即可
            if keyword_match or institution_match:
                matched_papers.append({
                    "id": paper.id,
                    "arxiv_id": paper.arxiv_id,
                    "title": paper.title,
                    "authors": paper.authors,
                    "chinese_summary": analysis.chinese_summary,
                    "subcategory": analysis.subcategory,
                    "relevance_score": analysis.relevance_score,
                    "innovation_score": analysis.innovation_score,
                    "affiliations": affiliations,
                    "github_url": analysis.github_url,
                    "arxiv_url": paper.arxiv_url,
                    "pdf_url": paper.pdf_url,
                    "keyword_match": keyword_match,
                    "institution_match": institution_match,
                })

        # 按分数排序，取前 N 篇
        matched_papers.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return matched_papers[:max_papers]

    def send_notifications(self, papers: List[Dict]) -> Dict[str, bool]:
        """发送推送通知"""
        if not papers:
            logger.info("没有匹配的论文需要推送")
            return {"feishu": False, "wechat": False}

        results = {
            "feishu": False,
            "wechat": False,
            "paper_count": len(papers)
        }

        # 飞书推送
        feishu_config = self.notification_config.get("feishu", {})
        if feishu_config.get("enabled") and self.feishu_webhook:
            try:
                self._send_feishu(papers, self.feishu_webhook)
                results["feishu"] = True
                logger.info(f"✓ 飞书推送成功，共 {len(papers)} 篇论文")
            except Exception as e:
                logger.error(f"飞书推送失败: {e}")

        # 微信推送
        wechat_config = self.notification_config.get("wechat", {})
        if wechat_config.get("enabled") and self.wechat_token:
            try:
                self._send_wechat(papers, wechat_config)
                results["wechat"] = True
                logger.info(f"✓ 微信推送成功，共 {len(papers)} 篇论文")
            except Exception as e:
                logger.error(f"微信推送失败: {e}")

        return results

    def _send_feishu(self, papers: List[Dict], webhook_url: str):
        """发送飞书卡片消息"""
        # 构建论文列表元素
        paper_elements = []
        for i, paper in enumerate(papers, 1):
            # 机构标签
            aff_text = ""
            if paper.get("affiliations"):
                aff_text = f"🏛️ {', '.join(paper['affiliations'][:2])}\n"

            # GitHub 链接
            github_text = ""
            if paper.get("github_url"):
                github_text = f"💻 [GitHub]({paper['github_url']})\n"

            # 匹配原因
            match_reason = []
            if paper.get("keyword_match"):
                match_reason.append("关键词匹配")
            if paper.get("institution_match"):
                match_reason.append("机构匹配")

            paper_elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{i}. [{paper['title']}]({paper['arxiv_url']})**\n"
                               f"📊 相关性: {paper.get('relevance_score', 0):.1f} | 创新性: {paper.get('innovation_score', 0):.1f}\n"
                               f"📁 {paper.get('subcategory', '其他')}\n"
                               f"{aff_text}"
                               f"📝 {paper.get('chinese_summary', '暂无摘要')[:100]}...\n"
                               f"{github_text}"
                               f"🔗 [PDF]({paper['pdf_url']}) | 匹配: {', '.join(match_reason)}"
                }
            })
            paper_elements.append({"tag": "hr"})

        # 飞书卡片消息
        card = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"📚 今日论文推送 ({len(papers)} 篇)"
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    },
                    {"tag": "hr"},
                    *paper_elements[:-1],  # 去掉最后一个 hr
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "查看更多"},
                                "type": "primary",
                                "url": self.frontend_url
                            }
                        ]
                    }
                ]
            }
        }

        response = requests.post(
            webhook_url,
            json=card,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()

        result = response.json()
        if result.get("code") != 0:
            raise Exception(f"飞书 API 错误: {result}")

    def _send_wechat(self, papers: List[Dict], config: Dict):
        """发送微信推送"""
        channel = config.get("channel", "pushplus")
        token = self.wechat_token

        # 构建消息内容（Markdown 格式）
        content_lines = [
            f"# 📚 今日论文推送 ({len(papers)} 篇)",
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            ""
        ]

        for i, paper in enumerate(papers, 1):
            # 机构
            aff_text = ""
            if paper.get("affiliations"):
                aff_text = f"🏛️ **机构**: {', '.join(paper['affiliations'][:2])}\n"

            # GitHub
            github_text = ""
            if paper.get("github_url"):
                github_text = f"💻 [GitHub]({paper['github_url']})\n"

            content_lines.extend([
                f"## {i}. {paper['title']}",
                "",
                f"📊 相关性: **{paper.get('relevance_score', 0):.1f}** | 创新性: **{paper.get('innovation_score', 0):.1f}**",
                f"📁 分类: {paper.get('subcategory', '其他')}",
                aff_text,
                f"📝 {paper.get('chinese_summary', '暂无摘要')}",
                "",
                github_text,
                f"🔗 [arXiv]({paper['arxiv_url']}) | [PDF]({paper['pdf_url']})",
                "",
                "---",
                ""
            ])

        content = "\n".join(content_lines)

        if channel == "serverchan":
            # Server酱 https://sct.ftqq.com
            url = f"https://sctapi.ftqq.com/{token}.send"
            data = {
                "title": f"📚 今日论文推送 ({len(papers)} 篇)",
                "desp": content
            }
            response = requests.post(url, data=data, timeout=10)

        elif channel == "pushplus":
            # PushPlus https://pushplus.plus
            url = "https://www.pushplus.plus/send"
            data = {
                "token": token,
                "title": f"📚 今日论文推送 ({len(papers)} 篇)",
                "content": content,
                "template": "markdown"
            }
            response = requests.post(url, json=data, timeout=10)

        elif channel == "wecom":
            # 企业微信机器人
            # token 就是完整的 webhook URL
            content_text = f"📚 今日论文推送 ({len(papers)} 篇)\n\n"
            for i, paper in enumerate(papers, 1):
                score = paper.get('relevance_score', 0)
                content_text += f"{i}. [{paper['title'][:40]}...]({paper['arxiv_url']})\n"
                content_text += f"   📊 {score:.1f}分 | {paper.get('subcategory', '其他')}\n\n"

            data = {
                "msgtype": "markdown",
                "markdown": {"content": content_text}
            }
            response = requests.post(token, json=data, timeout=10)

        else:
            raise ValueError(f"不支持的推送渠道: {channel}")

        response.raise_for_status()
        result = response.json()

        # 检查各渠道的响应
        if channel == "serverchan" and result.get("code") != 0:
            raise Exception(f"Server酱错误: {result}")
        elif channel == "pushplus" and result.get("code") != 200:
            raise Exception(f"PushPlus错误: {result}")
        elif channel == "wecom" and result.get("errcode") != 0:
            raise Exception(f"企业微信错误: {result}")


def send_daily_notification(db: Session) -> Dict:
    """发送每日推送（供调度器调用）"""
    service = NotificationService(db)
    papers = service.get_matching_papers(hours=24)
    return service.send_notifications(papers)
