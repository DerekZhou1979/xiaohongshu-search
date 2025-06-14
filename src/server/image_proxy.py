from flask import Flask, request, Response, abort
import requests
from urllib.parse import urlparse, unquote
from cachetools import TTLCache
import threading
import time
import hashlib
import os

app = Flask(__name__)

# 图片缓存配置
image_cache = TTLCache(maxsize=5000, ttl=3600)  # 1小时缓存
cache_lock = threading.Lock()

# 创建缓存目录
CACHE_DIR = "cache/images"
os.makedirs(CACHE_DIR, exist_ok=True)

def is_xiaohongshu_image(url):
    """检查是否是小红书CDN图片"""
    xiaohongshu_domains = [
        'sns-webpic-qc.xhscdn.com',
        'xhscdn.com',
        'ci.xiaohongshu.com'
    ]
    
    try:
        domain = urlparse(url).netloc
        return any(xhs_domain in domain for xhs_domain in xiaohongshu_domains)
    except:
        return False

def get_cache_filename(url):
    """生成缓存文件名"""
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{url_hash}.jpg")

def get_xiaohongshu_headers():
    """获取小红书专用请求头"""
    return {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.xiaohongshu.com/',
        'Origin': 'https://www.xiaohongshu.com',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Safari";v="16.6"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"iOS"',
    }

@app.after_request
def after_request(response):
    """添加CORS头"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'false')
    return response

@app.route('/image')
def proxy_image():
    """图片代理接口"""
    target_url = request.args.get('url')
    if not target_url:
        abort(400, description="Missing 'url' parameter")
    
    # URL解码
    target_url = unquote(target_url)
    
    # 调试日志
    print(f"代理请求图片: {target_url}")
    
    try:
        # 检查内存缓存
        with cache_lock:
            cached_data = image_cache.get(target_url)
        
        if cached_data:
            return Response(
                cached_data,
                mimetype='image/jpeg',
                headers={
                    'Cache-Control': 'public, max-age=3600',
                    'Content-Type': 'image/jpeg'
                }
            )
        
        # 检查文件缓存
        cache_file = get_cache_filename(target_url)
        if os.path.exists(cache_file):
            # 检查文件是否过期（24小时）
            if time.time() - os.path.getmtime(cache_file) < 86400:
                with open(cache_file, 'rb') as f:
                    image_data = f.read()
                
                # 更新内存缓存
                with cache_lock:
                    image_cache[target_url] = image_data
                
                return Response(
                    image_data,
                    mimetype='image/jpeg',
                    headers={
                        'Cache-Control': 'public, max-age=3600',
                        'Content-Type': 'image/jpeg'
                    }
                )
        
        # 设置请求头
        headers = get_xiaohongshu_headers()
        
        # 如果是小红书图片，使用特殊处理
        if is_xiaohongshu_image(target_url):
            # 移除可能导致403的参数
            if '!' in target_url:
                target_url = target_url.split('!')[0]
            print(f"处理后的小红书图片URL: {target_url}")
        
        # 发起请求
        print(f"发起请求，headers: {headers}")
        response = requests.get(
            target_url,
            headers=headers,
            timeout=15,
            stream=True,
            verify=False  # 忽略SSL证书问题
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 403:
            print("收到403错误，尝试多种策略")
            
            # 策略1: 使用微信浏览器User-Agent
            headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/88.0.4324.181 Mobile Safari/537.36 MicroMessenger/8.0.1'
            headers.pop('sec-ch-ua', None)
            headers.pop('sec-ch-ua-mobile', None)
            headers.pop('sec-ch-ua-platform', None)
            
            response = requests.get(
                target_url,
                headers=headers,
                timeout=15,
                stream=True,
                verify=False
            )
            print(f"微信浏览器重试后状态码: {response.status_code}")
            
            if response.status_code == 403:
                # 策略2: 使用桌面Chrome
                headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                
                response = requests.get(
                    target_url,
                    headers=headers,
                    timeout=15,
                    stream=True,
                    verify=False
                )
                print(f"桌面Chrome重试后状态码: {response.status_code}")
                
                if response.status_code == 403:
                    # 策略3: 最简单的请求头
                    simple_headers = {
                        'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
                    }
                    
                    response = requests.get(
                        target_url,
                        headers=simple_headers,
                        timeout=15,
                        stream=True,
                        verify=False
                    )
                    print(f"简单请求头重试后状态码: {response.status_code}")
        
        response.raise_for_status()
        
        # 读取图片数据
        image_data = b''
        for chunk in response.iter_content(chunk_size=8192):
            image_data += chunk
        
        # 检测内容类型
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        if 'image' not in content_type:
            content_type = 'image/jpeg'
        
        # 缓存到内存
        with cache_lock:
            image_cache[target_url] = image_data
        
        # 缓存到文件
        try:
            with open(cache_file, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            print(f"文件缓存失败: {e}")
        
        return Response(
            image_data,
            mimetype=content_type,
            headers={
                'Cache-Control': 'public, max-age=3600',
                'Content-Type': content_type
            }
        )
        
    except requests.exceptions.Timeout:
        abort(504, description="Request timeout")
    except requests.exceptions.RequestException as e:
        abort(502, description=f"Error fetching image: {str(e)}")
    except Exception as e:
        abort(500, description=f"Internal server error: {str(e)}")

@app.route('/health')
def health_check():
    """健康检查接口"""
    return {
        'status': 'healthy',
        'cache_size': len(image_cache),
        'timestamp': int(time.time())
    }

if __name__ == '__main__':
    print("图片代理服务器启动中...")
    print("访问地址: http://localhost:8081/image?url=图片URL")
    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True) 