#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书cookie设置工具
使用此脚本可以直接设置cookie值，无需通过浏览器登录
"""

import os
import json
import sys
import logging

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
    print("小红书Cookie设置工具")
    print("=" * 60)
    print("此工具可以直接设置cookie值，无需通过浏览器登录")
    print(f"Cookie文件路径: {cookies_file}")
    print("=" * 60)
    
    # 获取用户输入的cookie值
    cookies = []
    
    print("请输入cookie键值对 (格式: name=value)，每行一个，输入空行结束:")
    
    while True:
        line = input().strip()
        if not line:
            break
        
        try:
            name, value = line.split('=', 1)
            cookie = {
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.xiaohongshu.com',
                'path': '/'
            }
            cookies.append(cookie)
            print(f"已添加cookie: {name}")
        except ValueError:
            print("格式错误，请使用 name=value 格式")
    
    if not cookies:
        print("没有输入任何cookie，退出")
        return 1
    
    # 保存到文件
    try:
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print("=" * 60)
        print(f"成功保存 {len(cookies)} 个cookie到文件: {cookies_file}")
        print("=" * 60)
    except Exception as e:
        print(f"保存cookie文件失败: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 