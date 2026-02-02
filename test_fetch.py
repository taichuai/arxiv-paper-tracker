#!/usr/bin/env python3
"""
快速测试脚本 - 不依赖 LLM，验证 arXiv 获取功能
"""

import sys
import os

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import init_db, SessionLocal
from app.services.arxiv_fetcher import ArxivFetcher

def test_arxiv_fetch():
    """测试 arXiv 论文获取"""
    print("=" * 50)
    print("测试 arXiv 论文获取功能")
    print("=" * 50)
    print()

    # 初始化数据库
    print("1. 初始化数据库...")
    init_db()
    print("   ✓ 数据库初始化完成")
    print()

    # 创建会话
    db = SessionLocal()

    try:
        # 获取论文
        print("2. 从 arXiv 获取论文...")
        print("   (这可能需要几秒钟...)")
        print()

        fetcher = ArxivFetcher(db)
        papers = fetcher.fetch_recent_papers()

        if papers:
            print(f"   ✓ 成功获取 {len(papers)} 篇论文")
            print()

            # 显示前3篇
            print("3. 预览前 3 篇论文:")
            print()
            for i, paper in enumerate(papers[:3], 1):
                print(f"   [{i}] {paper['title']}")
                print(f"       作者: {paper['authors'][:100]}...")
                print(f"       分类: {paper['categories']}")
                print(f"       发布: {paper['published_date']}")
                print()

            # 保存到数据库
            print("4. 保存到数据库...")
            saved_count = fetcher.save_papers(papers)
            print(f"   ✓ 成功保存 {saved_count} 篇论文")
            print()

            print("=" * 50)
            print("✅ 测试成功!")
            print("=" * 50)
            print()
            print("下一步:")
            print("1. 配置 LLM API Key (编辑 backend/.env)")
            print("2. 运行完整服务: ./run.sh")
            print("3. 访问 http://localhost:5173")
            print()

        else:
            print("   ⚠️  没有获取到新论文")
            print("   可能原因:")
            print("   - 网络连接问题")
            print("   - arXiv API 限流")
            print("   - 时间范围内没有新论文")
            print()

    except Exception as e:
        print(f"   ❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    test_arxiv_fetch()
