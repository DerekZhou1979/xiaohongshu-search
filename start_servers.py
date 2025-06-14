#!/usr/bin/env python3
"""
启动小红书搜索服务器
同时启动主服务器和图片代理服务器
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
        # 启动图片代理服务器
        image_proxy_cmd = "python3 src/server/image_proxy.py"
        image_proxy_process = start_process(image_proxy_cmd, "图片代理服务器")
        processes.append(("图片代理服务器", image_proxy_process))
        
        # 等待图片代理服务器启动
        time.sleep(2)
        
        # 启动主服务器
        main_server_cmd = "python3 app.py"
        main_server_process = start_process(main_server_cmd, "主服务器")
        processes.append(("主服务器", main_server_process))
        
        print("\n" + "="*50)
        print("🎉 服务器启动成功!")
        print("="*50)
        print("📷 图片代理服务器: http://localhost:8081")
        print("🌐 主服务器: http://localhost:8080")
        print("="*50)
        print("按 Ctrl+C 停止所有服务器")
        print("="*50)
        
        # 等待所有进程
        while True:
            for name, process in processes:
                if process.poll() is not None:
                    print(f"⚠️  {name} 意外停止")
                    return
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n正在停止所有服务器...")
        
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
        
        print("✅ 所有服务器已停止")
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 