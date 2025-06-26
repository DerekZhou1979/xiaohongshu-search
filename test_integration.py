#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合功能测试脚本
验证统一提取器和Web界面的整合效果
"""

import sys
import os
import requests
import json
import time
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

def test_api_connection():
    """测试API连接"""
    try:
        response = requests.get('http://localhost:8080/', timeout=5)
        print(f"✅ Web服务器连接正常 (状态: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ Web服务器连接失败: {e}")
        return False

def test_unified_extractor():
    """测试统一提取器API"""
    try:
        # 准备测试数据
        test_data = {
            "keyword": "integration_test",
            "max_files": 10,
            "pattern": "*.html"
        }
        
        print(f"🔍 发送批量提取请求...")
        response = requests.post(
            'http://localhost:8080/api/unified-extract',
            json=test_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 统一提取器工作正常")
                print(f"   - 提取笔记数: {result.get('count', 0)}")
                print(f"   - 使用策略: {result.get('extraction_info', {}).get('strategies_used', [])}")
                print(f"   - 保存路径: {result.get('saved_path', 'N/A')}")
                return True
            else:
                print(f"⚠️  统一提取器返回失败: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ 统一提取器API错误: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 统一提取器测试失败: {e}")
        return False

def check_cache_files():
    """检查缓存文件"""
    cache_dir = Path("cache")
    
    if not cache_dir.exists():
        print("❌ cache目录不存在")
        return False
    
    html_files = list(cache_dir.glob("*.html"))
    print(f"📁 缓存目录状态:")
    print(f"   - 总HTML文件数: {len(html_files)}")
    
    if len(html_files) > 0:
        print(f"   - 文件示例: {html_files[0].name}")
        return True
    else:
        print("⚠️  缓存目录中没有HTML文件，可能无法测试提取功能")
        return False

def test_local_unified_extractor():
    """测试本地统一提取器"""
    try:
        from src.server.unified_extractor import UnifiedExtractor
        
        print("🔧 测试本地统一提取器...")
        extractor = UnifiedExtractor()
        
        # 测试从HTML文件提取
        results = extractor.extract_from_html_files(pattern="*.html", max_files=5)
        
        if results:
            print(f"✅ 本地统一提取器工作正常")
            print(f"   - 提取笔记数: {len(results)}")
            
            # 显示提取方法统计
            methods = {}
            for note in results:
                method = note.get('method', 'unknown')
                methods[method] = methods.get(method, 0) + 1
            
            print(f"   - 提取方法统计: {methods}")
            return True
        else:
            print("⚠️  本地统一提取器未提取到数据")
            return False
            
    except Exception as e:
        print(f"❌ 本地统一提取器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("="*50)
    print("🔬 小红书搜索工具整合功能测试")
    print("="*50)
    
    # 检查环境
    print("\n1️⃣ 环境检查")
    cache_ok = check_cache_files()
    
    # 测试API连接
    print("\n2️⃣ API连接测试")
    api_ok = test_api_connection()
    
    # 测试本地提取器
    print("\n3️⃣ 本地提取器测试")
    local_ok = test_local_unified_extractor()
    
    # 测试统一提取器API（如果服务器可用）
    print("\n4️⃣ API提取器测试")
    if api_ok:
        extractor_ok = test_unified_extractor()
    else:
        print("⏭️  跳过API测试（服务器不可用）")
        extractor_ok = False
    
    # 总结
    print("\n" + "="*50)
    print("📊 测试结果总结")
    print("="*50)
    print(f"缓存文件: {'✅' if cache_ok else '❌'}")
    print(f"API连接: {'✅' if api_ok else '❌'}")
    print(f"本地提取器: {'✅' if local_ok else '❌'}")
    print(f"API提取器: {'✅' if extractor_ok else '❌'}")
    
    if local_ok and api_ok:
        print("\n🎉 整合功能基本正常！")
        print("\n💡 测试建议:")
        print("1. 访问 http://localhost:8080 测试Web界面")
        print("2. 点击'批量提取缓存'按钮测试整合功能")
        print("3. 查看生成的HTML预览文件")
    else:
        print("\n⚠️  部分功能存在问题，请检查：")
        if not cache_ok:
            print("- 确保cache目录中有HTML文件")
        if not local_ok:
            print("- 检查统一提取器代码是否正确")
        if not api_ok:
            print("- 确保服务器已启动：python -m src.server.main_server")

if __name__ == "__main__":
    main() 