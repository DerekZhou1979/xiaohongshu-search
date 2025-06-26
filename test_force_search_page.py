#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试强制搜索页面保持功能
验证反爬虫处理后是否能正确保持在搜索页面
"""

import sys
import os
import time
from datetime import datetime

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from crawler.XHS_crawler import XiaoHongShuCrawler

def test_force_search_page():
    """测试强制搜索页面保持功能"""
    
    print("=" * 80)
    print("🧪 测试强制搜索页面保持功能")
    print("=" * 80)
    
    # 测试关键词列表
    test_keywords = [
        "美食推荐",
        "旅行攻略", 
        "护肤心得",
        "减肥方法",
        "摄影技巧"
    ]
    
    # 初始化爬虫（使用可见浏览器以便观察）
    crawler = XiaoHongShuCrawler(
        headless=False,  # 使用可见浏览器
        cookies_file='cache/cookies/xiaohongshu_cookies.json'
    )
    
    results_summary = []
    
    try:
        for i, keyword in enumerate(test_keywords):
            print(f"\n{'='*60}")
            print(f"🔍 测试 {i+1}/{len(test_keywords)}: 关键词 '{keyword}'")
            print(f"{'='*60}")
            
            test_start_time = datetime.now()
            
            # 执行搜索
            results = crawler.search(keyword, max_results=5, use_cache=False)
            
            test_end_time = datetime.now()
            test_duration = (test_end_time - test_start_time).total_seconds()
            
            # 检查结果
            if results and len(results) > 0:
                print(f"✅ 测试成功！找到 {len(results)} 条相关结果")
                print(f"⏱️  耗时: {test_duration:.2f} 秒")
                
                # 显示前3个结果的标题
                print("📝 结果预览:")
                for j, result in enumerate(results[:3]):
                    title = result.get('title', '无标题')[:50]
                    print(f"   {j+1}. {title}...")
                
                results_summary.append({
                    'keyword': keyword,
                    'status': 'SUCCESS',
                    'count': len(results),
                    'duration': test_duration
                })
            else:
                print(f"❌ 测试失败！未找到相关结果")
                print(f"⏱️  耗时: {test_duration:.2f} 秒")
                
                results_summary.append({
                    'keyword': keyword,
                    'status': 'FAILED',
                    'count': 0,
                    'duration': test_duration
                })
            
            # 检查当前URL状态
            try:
                current_url = crawler.driver.current_url
                if 'search_result' in current_url or 'keyword=' in current_url:
                    print(f"✅ URL状态: 正确的搜索页面")
                    print(f"📍 当前URL: {current_url[:70]}...")
                else:
                    print(f"⚠️  URL状态: 可能不在搜索页面")
                    print(f"📍 当前URL: {current_url[:70]}...")
            except Exception as e:
                print(f"❌ 无法检查URL状态: {str(e)}")
            
            # 等待一段时间再进行下一个测试
            if i < len(test_keywords) - 1:
                print(f"⏳ 等待5秒后进行下一个测试...")
                time.sleep(5)
    
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
    finally:
        # 关闭浏览器
        try:
            crawler.close()
            print("\n🔒 浏览器已关闭")
        except:
            pass
    
    # 显示测试总结
    print(f"\n{'='*80}")
    print("📊 测试总结")
    print(f"{'='*80}")
    
    total_tests = len(results_summary)
    successful_tests = len([r for r in results_summary if r['status'] == 'SUCCESS'])
    failed_tests = total_tests - successful_tests
    
    print(f"📈 总测试数: {total_tests}")
    print(f"✅ 成功: {successful_tests}")
    print(f"❌ 失败: {failed_tests}")
    print(f"📊 成功率: {(successful_tests/total_tests*100):.1f}%")
    
    if successful_tests > 0:
        avg_duration = sum([r['duration'] for r in results_summary if r['status'] == 'SUCCESS']) / successful_tests
        avg_results = sum([r['count'] for r in results_summary if r['status'] == 'SUCCESS']) / successful_tests
        print(f"⏱️  平均耗时: {avg_duration:.2f} 秒")
        print(f"📝 平均结果数: {avg_results:.1f} 条")
    
    print(f"\n📋 详细结果:")
    for result in results_summary:
        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
        print(f"   {status_icon} {result['keyword']}: {result['count']}条结果, {result['duration']:.2f}s")
    
    print(f"\n🎯 测试完成！")
    
    # 根据结果返回退出码
    if successful_tests == total_tests:
        print("🌟 所有测试都通过了！强制搜索页面保持功能工作正常。")
        return 0
    elif successful_tests > 0:
        print("⚠️  部分测试通过。强制搜索页面保持功能需要进一步优化。")
        return 1
    else:
        print("🚨 所有测试都失败了。强制搜索页面保持功能需要修复。")
        return 2

def test_redirect_detection():
    """测试重定向检测功能"""
    
    print("\n" + "="*80)
    print("🧪 测试重定向检测功能")
    print("="*80)
    
    crawler = XiaoHongShuCrawler(headless=False, cookies_file='cache/cookies.json')
    
    try:
        # 测试重定向检测
        original_search_url = "https://www.xiaohongshu.com/search_result?keyword=%E7%BE%8E%E9%A3%9F&source=web_search&type=comprehensive"
        non_search_url = "https://www.xiaohongshu.com"
        
        # 测试从搜索页面到非搜索页面的重定向检测
        redirected = crawler._check_redirected_from_search(original_search_url, non_search_url)
        
        if redirected:
            print("✅ 重定向检测功能正常：正确识别了从搜索页面到首页的重定向")
        else:
            print("❌ 重定向检测功能异常：未能识别重定向")
        
        # 测试从搜索页面到搜索页面的情况（不应被判定为重定向）
        same_search_url = "https://www.xiaohongshu.com/search_result?keyword=%E6%97%85%E8%A1%8C&source=web_search"
        not_redirected = crawler._check_redirected_from_search(original_search_url, same_search_url)
        
        if not not_redirected:
            print("✅ 重定向检测功能正常：正确识别了搜索页面间的跳转不是重定向")
        else:
            print("❌ 重定向检测功能异常：错误地将搜索页面间跳转判定为重定向")
            
    except Exception as e:
        print(f"❌ 重定向检测测试失败: {str(e)}")
    finally:
        try:
            crawler.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 启动强制搜索页面保持功能测试")
    print("📝 这个测试将验证反爬虫处理后是否能正确保持在搜索页面")
    print("⚠️  请确保已经运行了 simple_refresh_cookies.py 刷新cookies")
    
    input("\n按Enter键开始测试...")
    
    # 运行主要测试
    exit_code = test_force_search_page()
    
    # 运行重定向检测测试
    test_redirect_detection()
    
    sys.exit(exit_code) 