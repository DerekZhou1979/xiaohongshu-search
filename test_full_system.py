#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整系统测试脚本
测试精准容器提取功能是否正常集成到主系统中
"""

import os
import sys
import time
import json
import requests
from datetime import datetime

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def test_api_connection():
    """测试API连接"""
    print("🔗 测试API连接...")
    try:
        response = requests.get("http://localhost:8080/", timeout=10)
        if response.status_code == 200:
            print("✅ API连接正常")
            return True
        else:
            print(f"❌ API连接失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False

def test_search_api():
    """测试搜索API"""
    print("\n🔍 测试搜索API...")
    
    test_keywords = ["美食", "老庙黄金", "时尚"]
    
    for keyword in test_keywords:
        print(f"\n🔍 测试关键词: {keyword}")
        try:
            url = f"http://localhost:8080/api/search?keyword={keyword}&max_results=5"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   📊 返回结果: {data.get('count', 0)} 条")
                print(f"   📝 状态消息: {data.get('message', 'N/A')}")
                
                if data.get('count', 0) > 0:
                    print(f"   ✅ 成功找到 {data['count']} 条笔记")
                    
                    # 显示第一条结果的详细信息
                    first_note = data['notes'][0]
                    print(f"   📝 示例笔记:")
                    print(f"      ID: {first_note.get('note_id', 'N/A')}")
                    print(f"      标题: {first_note.get('title', 'N/A')[:30]}...")
                    print(f"      作者: {first_note.get('author', 'N/A')}")
                    print(f"      图片数: {len(first_note.get('images', []))}")
                    print(f"      提取方法: {first_note.get('method', 'N/A')}")
                    
                    return True
                else:
                    print(f"   ⚠️  未找到结果")
                    
            else:
                print(f"   ❌ API错误: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求失败: {e}")
    
    return False

def test_precise_extraction_integration():
    """测试精准提取功能是否已集成"""
    print("\n🎯 测试精准提取功能集成...")
    
    try:
        # 检查是否有缓存的HTML文件可用于测试
        cache_temp_dir = "cache/temp"
        if os.path.exists(cache_temp_dir):
            html_files = [f for f in os.listdir(cache_temp_dir) if f.endswith('.html')]
            if html_files:
                print(f"   📁 找到 {len(html_files)} 个缓存HTML文件")
                
                # 运行我们的精准提取脚本
                import subprocess
                result = subprocess.run(['python', 'precise_extraction.py'], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("   ✅ 精准提取脚本运行成功")
                    
                    # 检查是否生成了结果文件
                    if os.path.exists('cache/precise_extracted_notes.json'):
                        with open('cache/precise_extracted_notes.json', 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        print(f"   📊 精准提取结果: {data.get('count', 0)} 条笔记")
                        print(f"   ✅ 精准提取功能正常工作")
                        return True
                    else:
                        print("   ⚠️  未找到精准提取结果文件")
                else:
                    print(f"   ❌ 精准提取脚本失败: {result.stderr}")
            else:
                print("   ⚠️  未找到缓存HTML文件")
        else:
            print("   ⚠️  缓存目录不存在")
            
        return False
        
    except Exception as e:
        print(f"   ❌ 测试精准提取功能失败: {e}")
        return False

def test_strategies_configuration():
    """测试策略配置"""
    print("\n⚙️  测试策略配置...")
    
    try:
        # 检查环境变量中的配置
        import os
        crawl_config = os.environ.get('CRAWL_CONFIG')
        
        if crawl_config:
            config = json.loads(crawl_config)
            print("   📋 当前配置:")
            print(f"      策略1: {'✅' if config.get('enable_strategy_1') else '❌'}")
            print(f"      策略2: {'✅' if config.get('enable_strategy_2') else '❌'}")
            print(f"      策略3: {'✅' if config.get('enable_strategy_3') else '❌'}")
            print(f"      策略4: {'✅' if config.get('enable_strategy_4', True) else '❌'}")
            print(f"      验证严格度: {config.get('validation_strict_level', 'N/A')}")
            print(f"      后台提取: {'✅' if config.get('enable_backend_extraction') else '❌'}")
            
            return True
        else:
            print("   ⚠️  未找到爬虫配置")
            return False
            
    except Exception as e:
        print(f"   ❌ 配置测试失败: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("📋 完整系统测试报告")
    print("="*60)
    
    test_results = []
    
    # API连接测试
    api_ok = test_api_connection()
    test_results.append(("API连接", api_ok))
    
    # 策略配置测试
    config_ok = test_strategies_configuration()
    test_results.append(("策略配置", config_ok))
    
    # 精准提取集成测试
    extraction_ok = test_precise_extraction_integration()
    test_results.append(("精准提取集成", extraction_ok))
    
    # 搜索API测试
    search_ok = test_search_api()
    test_results.append(("搜索API功能", search_ok))
    
    # 生成总结
    print(f"\n📊 测试总结:")
    print(f"   测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常")
        print("\n📌 下一步操作:")
        print("   1. 访问 http://localhost:8080 使用Web界面")
        print("   2. 或直接调用API: http://localhost:8080/api/search?keyword=关键词")
        print("   3. 查看生成的HTML报告: cache/precise_notes_report.html")
    else:
        print("⚠️  部分测试失败，请检查系统配置")
        
        if not api_ok:
            print("   💡 建议: 检查服务器是否正常启动")
        if not search_ok:
            print("   💡 建议: 可能需要刷新cookies或等待初始化完成")
        if not extraction_ok:
            print("   💡 建议: 检查beautifulsoup4是否已安装")

def main():
    """主函数"""
    print("🚀 完整系统测试开始")
    print("测试小红书搜索工具的精准提取功能集成情况")
    print("="*60)
    
    try:
        generate_test_report()
        
    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 