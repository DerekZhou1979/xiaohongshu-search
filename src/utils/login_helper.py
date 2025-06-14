#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书cookie获取工具
运行此脚本，将打开浏览器，用户手动登录后，会自动保存cookie到文件
"""

import os
import sys
import logging
import traceback
from crawler import XiaoHongShuCrawler

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # 确保cache目录存在
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    # 默认cookie文件路径
    cookies_file = os.path.join(cache_dir, 'xiaohongshu_cookies.json')
    
    print("=" * 60)
    print("小红书登录工具")
    print("=" * 60)
    print("此工具将打开浏览器，您需要手动登录小红书账号")
    print("登录成功后，cookie将自动保存到文件中")
    print(f"Cookie文件路径: {cookies_file}")
    print("=" * 60)
    input("按Enter键继续...")
    
    try:
        # 创建不使用无头模式的爬虫实例
        crawler = XiaoHongShuCrawler(use_selenium=True, headless=False, cookies_file=cookies_file)
        
        # 开始登录
        print("正在打开浏览器...")
        success = crawler.login()
        
        if success:
            print("=" * 60)
            print("登录成功！Cookie已保存")
            print(f"Cookie文件路径: {cookies_file}")
            print("=" * 60)
            print("您现在可以关闭浏览器，然后运行 python app.py 启动应用")
        else:
            print("=" * 60)
            print("登录失败或超时！")
            print("请重新运行此脚本，再次尝试登录")
            print("=" * 60)
        
        # 关闭爬虫
        crawler.close()
        
        return 0 if success else 1
    except Exception as e:
        print("=" * 60)
        print(f"错误: {str(e)}")
        print("可能是Selenium初始化失败，请确保已安装Chrome浏览器和相应的WebDriver")
        print("详细错误信息:")
        traceback.print_exc()
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 