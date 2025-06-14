#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试改进的数据提取功能
"""

import sys
import os
import json
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(__file__))

from src.crawler.xiaohongshu_crawler import XiaoHongShuCrawler

def test_search_with_improved_extraction():
    """测试改进的数据提取功能"""
    print("🚀 开始测试改进的数据提取功能...")
    
    # 初始化爬虫
    crawler = XiaoHongShuCrawler(use_selenium=True, headless=False)
    
    try:
        # 搜索关键词
        keyword = "护肤品"
        print(f"🔍 搜索关键词: {keyword}")
        
        # 执行搜索
        results = crawler.search(keyword, max_results=5, use_cache=False)
        
        if results:
            print(f"✅ 成功获取 {len(results)} 条结果")
            
            # 显示结果
            for i, note in enumerate(results, 1):
                print(f"\n📝 笔记 {i}:")
                print(f"   ID: {note['id']}")
                print(f"   标题: {note['title'][:50]}...")
                print(f"   描述: {note['desc'][:80]}...")
                print(f"   作者: {note['author']}")
                print(f"   封面: {note['cover'][:50]}...")
                print(f"   URL: {note['url'][:50]}...")
                print(f"   互动数据: 👍{note['likes']} 💬{note['comments']} ⭐{note['collects']} 🔄{note['shares']}")
        else:
            print("❌ 没有获取到结果")
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    finally:
        # 关闭爬虫
        crawler.close()
        print("🔚 测试完成")

if __name__ == "__main__":
    test_search_with_improved_extraction() 