#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版小红书Cookies刷新工具
避免复杂初始化问题，直接使用Selenium获取cookies
"""

import os
import sys
import json
import time
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Selenium相关库
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def refresh_cookies():
    """刷新cookies（手动登录模式）"""
    driver = None
    try:
        print("🍪 小红书Cookies刷新工具（简化版）")
        print("=" * 50)
        
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')  
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 反爬虫配置
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # 使用本地ChromeDriver
        chromedriver_path = "drivers/chromedriver-mac-arm64/chromedriver"
        if not os.path.exists(chromedriver_path):
            print(f"❌ ChromeDriver不存在: {chromedriver_path}")
            return False
        
        print("🚀 正在启动浏览器...")
        os.chmod(chromedriver_path, 0o755)
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 隐藏WebDriver特征
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ 浏览器启动成功！")
        print("=" * 50)
        print("🌟 请在浏览器中进行以下操作：")
        print("1. 访问 https://www.xiaohongshu.com")
        print("2. 登录您的小红书账号")
        print("3. 登录成功后，在此控制台按 Enter 键继续")
        print("=" * 50)
        
        # 打开小红书网站
        driver.get("https://www.xiaohongshu.com")
        
        # 等待用户手动登录
        input("⏳ 请完成登录后按 Enter 键继续...")
        
        # 等待确保登录状态生效
        print("⏳ 等待5秒确保登录状态...")
        time.sleep(5)
        
        # 获取cookies
        cookies = driver.get_cookies()
        
        if not cookies:
            print("❌ 未获取到任何cookies，可能登录失败")
            return False
        
        # 备份旧cookies（如果存在）
        cookies_dir = "cache/cookies"
        os.makedirs(cookies_dir, exist_ok=True)
        cookies_file = os.path.join(cookies_dir, "xiaohongshu_cookies.json")
        
        if os.path.exists(cookies_file):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(cookies_dir, f"xiaohongshu_cookies_backup_{timestamp}.json")
            os.rename(cookies_file, backup_file)
            print(f"📁 旧cookies已备份到: {backup_file}")
        
        # 保存新cookies
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        print("=" * 50)
        print(f"✅ 成功刷新cookies！")
        print(f"📊 共获取 {len(cookies)} 个cookie")
        print(f"📁 保存位置: {cookies_file}")
        
        # 显示重要cookies
        important_cookies = ['web_session', 'a1', 'webId', 'xsecappid']
        print("\n🔑 重要cookies预览:")
        for cookie in cookies:
            if cookie['name'] in important_cookies:
                print(f"   {cookie['name']}: {cookie['value'][:30]}...")
        
        print("=" * 50)
        print("🎉 Cookies刷新完成！现在可以重启应用程序了。")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ 刷新cookies失败: {str(e)}")
        logger.error(f"详细错误: {str(e)}")
        return False
    finally:
        if driver:
            print("🔄 正在关闭浏览器...")
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    success = refresh_cookies()
    if success:
        print("\n✨ 建议现在重启主程序以使用新的cookies！")
        print("💡 运行命令: python3 app.py")
    else:
        print("\n💡 请检查网络连接或重试")
    
    input("\n⏳ 按 Enter 键退出...") 