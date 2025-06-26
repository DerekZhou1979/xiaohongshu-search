#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试推荐页面检测和强制返回搜索功能修复
专门验证是否能正确处理小红书的推荐页面重定向问题
"""

import sys
import os
import time
from datetime import datetime
import requests

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from crawler.XHS_crawler import XiaoHongShuCrawler

def test_single_keyword_with_monitoring(keyword="老庙黄金"):
    """测试单个关键词搜索，重点监控推荐页面检测和恢复过程"""
    
    print("=" * 80)
    print(f"🧪 测试推荐页面检测和恢复功能 - 关键词: '{keyword}'")
    print("=" * 80)
    
    # 初始化爬虫（使用可见浏览器以便观察）
    crawler = XiaoHongShuCrawler(
        headless=False,  # 使用可见浏览器观察过程
        cookies_file='cache/cookies/xiaohongshu_cookies.json'
    )
    
    # 🔧 新增：cookies注入后截图
    try:
        post_cookies_screenshot_dir = "cache/post_cookies_screenshots"
        os.makedirs(post_cookies_screenshot_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        post_cookies_screenshot_path = os.path.join(post_cookies_screenshot_dir, f"post_cookies_{keyword}_{timestamp}.png")
        
        # 先访问主页确保cookies生效
        crawler.driver.get("https://www.xiaohongshu.com")
        time.sleep(3)
        
        crawler.driver.save_screenshot(post_cookies_screenshot_path)
        print(f"📸 Cookies注入后截图已保存: {post_cookies_screenshot_path}")
    except Exception as screenshot_error:
        print(f"⚠️  Cookies注入后截图失败: {str(screenshot_error)}")
    
    test_start_time = datetime.now()
    
    try:
        print(f"🔍 开始搜索关键词: '{keyword}'")
        print(f"⏰ 开始时间: {test_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 执行搜索（禁用缓存确保实时测试）
        results = crawler.search(keyword, max_results=5, use_cache=False)
        
        test_end_time = datetime.now()
        test_duration = (test_end_time - test_start_time).total_seconds()
        
        # 检查结果
        if results and len(results) > 0:
            print(f"\n✅ 搜索成功！找到 {len(results)} 条相关结果")
            print(f"⏱️  总耗时: {test_duration:.2f} 秒")
            
            # 显示结果预览
            print("\n📝 结果预览:")
            for i, result in enumerate(results[:3]):
                title = result.get('title', '无标题')
                author = result.get('author', '未知作者')
                likes = result.get('likes', 0)
                print(f"   {i+1}. 标题: {title[:40]}...")
                print(f"      作者: {author}, 点赞: {likes}")
            
            # 检查当前浏览器状态
            try:
                current_url = crawler.driver.current_url
                if 'search_result' in current_url or 'keyword=' in current_url:
                    print(f"\n✅ 浏览器状态: 正确停留在搜索页面")
                    print(f"📍 URL: {current_url[:70]}...")
                    
                    # 🔧 新增：截取成功页面的图片
                    try:
                        success_screenshot_dir = "cache/success_screenshots"
                        os.makedirs(success_screenshot_dir, exist_ok=True)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = os.path.join(success_screenshot_dir, f"success_{keyword}_{timestamp}.png")
                        
                        crawler.driver.save_screenshot(screenshot_path)
                        print(f"📸 成功页面截图已保存: {screenshot_path}")
                    except Exception as screenshot_error:
                        print(f"⚠️  截图保存失败: {str(screenshot_error)}")
                else:
                    print(f"\n⚠️  浏览器状态: 可能不在搜索页面")
                    print(f"📍 URL: {current_url[:70]}...")
            except Exception as e:
                print(f"\n❌ 无法检查浏览器状态: {str(e)}")
            
            return True
            
        else:
            print(f"\n❌ 搜索失败！未找到相关结果")
            print(f"⏱️  总耗时: {test_duration:.2f} 秒")
            
            # 检查最终浏览器状态
            try:
                current_url = crawler.driver.current_url
                page_title = crawler.driver.title
                print(f"\n🔍 当前浏览器状态:")
                print(f"   URL: {current_url}")
                print(f"   标题: {page_title}")
                
                # 检查是否在推荐页面
                page_source = crawler.driver.page_source
                if crawler._is_recommendation_page(page_source, current_url):
                    print(f"🚨 检测到仍在推荐页面 - 推荐页面检测和恢复功能需要优化")
                else:
                    print(f"✅ 不在推荐页面 - 可能是其他问题")
                
            except Exception as e:
                print(f"❌ 无法检查浏览器状态: {str(e)}")
            
            return False
    
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        return False
    finally:
        # 等待用户观察
        print(f"\n⏳ 等待10秒供用户观察浏览器状态...")
        time.sleep(10)
        
        # 关闭浏览器
        try:
            crawler.close()
            print("🔒 浏览器已关闭")
        except:
            pass

def test_api_connectivity():
    """测试服务器API连接性"""
    try:
        print("\n" + "="*50)
        print("🌐 测试服务器API连接性")
        print("="*50)
        
        # 测试主页
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ 主页访问正常")
        else:
            print(f"⚠️  主页访问异常，状态码: {response.status_code}")
        
        # 测试搜索API
        search_data = {"keyword": "测试", "max_results": 3}
        response = requests.post("http://localhost:8080/search", json=search_data, timeout=10)
        
        if response.status_code == 200:
            print("✅ 搜索API连接正常")
            result = response.json()
            print(f"📊 API返回: {result.get('message', '无消息')}")
        else:
            print(f"⚠️  搜索API异常，状态码: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用程序正在运行")
    except Exception as e:
        print(f"❌ API测试出错: {str(e)}")

def main():
    print("🚀 启动推荐页面检测和恢复功能修复测试")
    print("📝 这个测试专门验证强制搜索页面保持功能的修复效果")
    print("🎯 测试目标：确保不会被困在推荐页面")
    
    # 测试API连接性
    test_api_connectivity()
    
    print("\n" + "="*80)
    print("⚠️  重要提示:")
    print("1. 请确保已经运行了 simple_refresh_cookies.py 刷新cookies")
    print("2. 测试将使用可见浏览器，您可以观察整个恢复过程")
    print("3. 如果看到推荐页面，程序应该会自动尝试返回搜索页面")
    print("4. 测试完成后浏览器会自动关闭")
    print("="*80)
    
    input("\n按Enter键开始测试...")
    
    # 测试容易触发推荐页面的关键词
    test_keywords = ["老庙黄金"]
    
    success_count = 0
    total_count = len(test_keywords)
    
    for i, keyword in enumerate(test_keywords):
        print(f"\n{'='*60}")
        print(f"测试 {i+1}/{total_count}: {keyword}")
        print(f"{'='*60}")
        
        success = test_single_keyword_with_monitoring(keyword)
        if success:
            success_count += 1
        
        if i < total_count - 1:
            print(f"\n⏳ 等待5秒后进行下一个测试...")
            time.sleep(5)
    
    # 测试总结
    print(f"\n{'='*80}")
    print("📊 推荐页面检测和恢复功能测试总结")
    print(f"{'='*80}")
    print(f"📈 总测试数: {total_count}")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {total_count - success_count}")
    print(f"📊 成功率: {(success_count/total_count*100):.1f}%")
    
    if success_count == total_count:
        print("\n🌟 所有测试都通过了！推荐页面检测和恢复功能工作正常。")
        return 0
    elif success_count > 0:
        print("\n⚠️  部分测试通过。推荐页面检测和恢复功能需要进一步优化。")
        return 1
    else:
        print("\n🚨 所有测试都失败了。推荐页面检测和恢复功能需要修复。")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 