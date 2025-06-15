#!/usr/bin/env python3
"""
启动小红书搜索服务器
启动主服务器，提供web界面和API服务
"""

import subprocess
import sys
import time
import signal
import os

def start_process(command, name):
    """启动进程"""
    print(f"启动 {name}...")
    process = subprocess.Popen(
        command,
        shell=True,
        preexec_fn=os.setsid
    )
    return process

def main():
    """主函数"""
    processes = []
    
    try:
        print("🚀 正在启动小红书搜索工具...")
        
        # 启动主服务器
        main_server_cmd = "python3 app.py"
        main_server_process = start_process(main_server_cmd, "主服务器")
        processes.append(("主服务器", main_server_process))
        
        # 等待主服务器启动
        time.sleep(3)
        
        print("\n" + "="*50)
        print("🎉 服务器启动成功!")
        print("="*50)
        print("🌐 小红书搜索工具: http://localhost:8080")
        print("📱 使用方法:")
        print("   1. 在浏览器中打开上述地址")
        print("   2. 输入搜索关键词")
        print("   3. 查看实时debug信息和搜索结果")
        print("="*50)
        print("💡 提示:")
        print("   - 支持5种运行模式选择")
        print("   - 实时显示搜索过程debug信息")
        print("   - 自动处理验证码和反爬虫")
        print("   - 支持缓存和结果HTML生成")
        print("="*50)
        print("按 Ctrl+C 停止服务器")
        print("="*50)
        
        # 等待进程
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f"⚠️  {name} 意外停止")
                    return
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        
        # 停止所有进程
        for name, process in processes:
            try:
                print(f"停止 {name}...")
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
        
        print("✅ 服务器已停止")
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("💡 请确保:")
        print("   1. Python环境正常")
        print("   2. 依赖包已安装 (pip install -r requirements.txt)")
        print("   3. ChromeDriver可执行")
        sys.exit(1)

if __name__ == "__main__":
    main() 