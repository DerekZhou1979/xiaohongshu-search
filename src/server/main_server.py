#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
小红书搜索服务器模块
提供Web API和静态文件服务，支持搜索、结果展示等功能

主要功能：
1. Web API服务 - 搜索、笔记详情、热门关键词
2. 静态文件服务 - HTML、CSS、JS、图片
3. HTML结果页面服务 - 文件形式和API形式
4. 用户登录支持
"""

import sys
import os
import logging
import time
import hashlib
import traceback
import json
import threading
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
from flask_cors import CORS
from src.crawler.XHS_crawler import XiaoHongShuCrawler
from src.server.debug_manager import debug_manager
# from src.server.note_generator import NoteContentGenerator  # 已删除，功能已整合
from src.server.note_content_extractor import NoteContentExtractor

# ==================== 配置和初始化 ====================

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__, static_folder='../../static')
CORS(app)  # 允许跨域请求

# ==================== 全局变量 ====================

# Cookie文件路径
COOKIES_FILE = os.path.join('cache', 'cookies', 'xiaohongshu_cookies.json')

# 全局爬虫实例（延迟初始化）
crawler = None

# 笔记内容生成器实例（已删除，功能已整合到统一提取器）
# note_generator = NoteContentGenerator()

# 笔记内容提取器实例
note_extractor = NoteContentExtractor()

# 统一数据提取器实例
from src.server.unified_extractor import UnifiedExtractor
unified_extractor = UnifiedExtractor()

# HTML结果内存缓存（避免文件路径问题）
html_results_cache = {}

# ==================== 工具函数 ====================

def store_html_result(html_hash, html_content):
    """
    存储HTML结果到内存缓存
    
    Args:
        html_hash: HTML内容的MD5哈希值
        html_content: HTML内容
    """
    global html_results_cache
    html_results_cache[html_hash] = html_content
    logger.info(f"HTML内容已存储到内存缓存: {html_hash}")

def init_crawler():
    """
    延迟初始化爬虫实例
    只在第一次使用时初始化，避免启动时的性能开销
    
    Returns:
        bool: 初始化是否成功
    """
    global crawler
    if crawler is None:
        try:
            logger.info("正在初始化小红书爬虫...")
            crawler = XiaoHongShuCrawler(
                use_selenium=True, 
                headless=True, 
                cookies_file=COOKIES_FILE
            )
            # 设置HTML存储回调函数
            crawler.set_html_callback(store_html_result)
            logger.info("小红书爬虫初始化成功")
            return True
        except Exception as e:
            logger.error(f"小红书爬虫初始化失败: {str(e)}")
            logger.error(traceback.format_exc())
            crawler = None
            return False
    return True

def get_project_root():
    """获取项目根目录路径"""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def start_backend_extraction(search_results, session_id):
    """
    启动后台笔记内容提取任务
    
    Args:
        search_results: 搜索结果列表
        session_id: 会话ID
    """
    try:
        # 导入后台爬虫模块
        from src.crawler.backend_XHS_crawler import start_backend_crawl
        
        # 规范化搜索结果格式
        if isinstance(search_results, dict) and 'data' in search_results:
            notes_data = search_results['data']
        else:
            notes_data = search_results if isinstance(search_results, list) else []
        
        if not notes_data:
            logger.warning(f"后台提取任务取消：没有有效的笔记数据 (session: {session_id})")
            return
        
        logger.info(f"🚀 启动后台笔记内容提取任务")
        logger.info(f"📊 会话ID: {session_id}")
        logger.info(f"📝 待提取笔记数量: {len(notes_data)}")
        
        # 记录到debug管理器
        debug_manager.store_debug_info(session_id, f"🚀 后台爬虫开始提取 {len(notes_data)} 篇笔记的详细内容", "INFO")
        
        # 启动后台爬取任务
        backend_session_id = f"{session_id}_backend"
        result = start_backend_crawl(notes_data, backend_session_id)
        
        # 记录完成状态
        success_count = result.get('success_count', 0)
        failed_count = result.get('failed_count', 0)
        success_rate = result.get('success_rate', 0)
        duration = result.get('duration_seconds', 0)
        
        logger.info(f"🎉 后台笔记内容提取任务完成!")
        logger.info(f"📊 成功: {success_count}, 失败: {failed_count}, 成功率: {success_rate:.1f}%, 耗时: {duration:.1f}秒")
        
        debug_manager.store_debug_info(
            session_id, 
            f"✅ 后台爬虫完成！成功: {success_count}/{len(notes_data)} 篇 ({success_rate:.1f}%), 耗时: {duration:.1f}秒", 
            "INFO"
        )
        
    except Exception as e:
        error_msg = f"后台笔记内容提取任务失败: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        debug_manager.store_debug_info(session_id, f"❌ {error_msg}", "ERROR")





# ==================== 静态文件路由 ====================

@app.route('/')
def index():
    """主页 - 返回搜索界面"""
    return send_from_directory('../../static', 'index.html')

@app.route('/css/<path:path>')
def serve_css(path):
    """提供CSS文件服务"""
    return send_from_directory('../../static/css', path)

@app.route('/js/<path:path>')
def serve_js(path):
    """提供JavaScript文件服务"""
    return send_from_directory('../../static/js', path)

@app.route('/img/<path:path>')
def serve_img(path):
    """提供图片文件服务"""
    return send_from_directory('../../static/images', path)

# ==================== 用户登录路由 ====================

@app.route('/login')
def login():
    """
    用户登录页面
    打开浏览器让用户手动登录小红书，获取cookie
    """
    try:
        # 创建专门用于登录的爬虫实例（非无头模式）
        login_crawler = XiaoHongShuCrawler(use_selenium=True, headless=False)
        success = login_crawler.login()
        login_crawler.close()
        
        if success:
            # 登录成功后重置主爬虫实例，以使用新的cookie
            global crawler
            crawler = None
            return redirect(url_for('index'))
        else:
            return jsonify({"error": "登录失败，请重试"}), 500
    except Exception as e:
        logger.error(f"登录过程出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"登录过程出错: {str(e)}"}), 500

# ==================== API路由 ====================

@app.route('/api/search')
def search():
    """
    搜索API
    根据关键词搜索小红书笔记
    
    参数:
        keyword: 搜索关键词（必需）
        max_results: 最大结果数量（可选，默认21）
        use_cache: 是否使用缓存（可选，默认true）
        session_id: 会话ID（可选，用于debug信息）
    
    返回:
        JSON格式的搜索结果，包含笔记列表和HTML页面URL
    """
    # 初始化爬虫
    if not init_crawler():
        return jsonify({"error": "爬虫初始化失败，请检查网络连接和Chrome浏览器"}), 500
        
    # 获取参数
    keyword = request.args.get('keyword', '').strip()
    session_id = request.args.get('session_id', f"search_{int(time.time())}")
    
    if not keyword:
        return jsonify({"error": "缺少关键词参数"}), 400
    
    try:
        # 解析参数
        max_results = int(request.args.get('max_results', 21))
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        
        # 记录开始搜索
        debug_manager.store_debug_info(session_id, f"🔍 开始搜索关键词: {keyword}", "INFO")
        debug_manager.store_debug_info(session_id, f"📊 最大结果数: {max_results}, 使用缓存: {use_cache}", "INFO")
        
        # 设置爬虫的debug回调
        debug_callback = debug_manager.create_debug_callback(session_id)
        
        # 如果爬虫支持debug回调，设置它
        if hasattr(crawler, 'set_debug_callback'):
            crawler.set_debug_callback(debug_callback)
        
        # 🔧 修复1：记录HTML生成状态的标志
        html_generation_started = False
        html_hash = hashlib.md5(keyword.encode()).hexdigest()
        
        # 设置HTML生成状态追踪回调
        def html_status_callback(hash_key, html_content):
            nonlocal html_generation_started
            html_generation_started = True
            debug_manager.store_debug_info(session_id, f"📄 HTML结果页面生成完成: {hash_key}", "INFO")
            # 调用原始的存储回调
            store_html_result(hash_key, html_content)
        
        # 设置增强的HTML回调
        if hasattr(crawler, 'set_html_callback'):
            crawler.set_html_callback(html_status_callback)
        
        # 执行搜索
        debug_manager.store_debug_info(session_id, "🚀 正在执行搜索...", "INFO")
        search_results = crawler.search(keyword, max_results=max_results, use_cache=use_cache)
        
        # 调试信息：检查搜索结果
        logger.info(f"搜索结果类型: {type(search_results)}")
        logger.info(f"搜索结果长度: {len(search_results) if search_results else 0}")
        if search_results:
            logger.info(f"第一条结果: {search_results[0] if len(search_results) > 0 else 'N/A'}")
        
        # 如果搜索结果为空，尝试从缓存直接读取
        if not search_results or len(search_results) == 0:
            logger.warning("爬虫搜索结果为空，尝试从缓存直接读取...")
            try:
                cache_filename = f"search_{hashlib.md5(keyword.encode()).hexdigest()}.json"
                cache_path = os.path.join(get_project_root(), 'cache', 'temp', cache_filename)
                if os.path.exists(cache_path):
                    with open(cache_path, 'r', encoding='utf-8') as cache_file:
                        cache_data = json.load(cache_file)
                        search_results = cache_data.get('data', [])
                        logger.info(f"从缓存恢复了 {len(search_results)} 条结果")
                        debug_manager.store_debug_info(session_id, f"✅ 从缓存恢复了 {len(search_results)} 条结果", "INFO")
            except Exception as cache_error:
                logger.error(f"从缓存恢复失败: {cache_error}")
        
        # 🔧 修复2：等待HTML生成完成（如果有数据的话）
        html_ready = False
        if search_results and len(search_results) > 0:
            # 等待HTML生成（最多10秒）
            debug_manager.store_debug_info(session_id, "⏳ 等待HTML页面生成...", "INFO")
            wait_start = time.time()
            max_wait = 10  # 最大等待10秒
            
            while time.time() - wait_start < max_wait:
                if html_generation_started or html_hash in html_results_cache:
                    html_ready = True
                    debug_manager.store_debug_info(session_id, "✅ HTML页面生成完成", "INFO")
                    break
                time.sleep(0.5)  # 每500ms检查一次
            
            if not html_ready:
                debug_manager.store_debug_info(session_id, "⚠️ HTML页面生成超时，但搜索数据有效", "WARNING")
        
        # 根据配置决定是否启动后台爬虫提取详细内容
        if search_results and len(search_results) > 0:
            # 获取配置（从环境变量或配置文件）
            enable_backend_extraction = os.environ.get('ENABLE_BACKEND_EXTRACTION', 'false').lower() == 'true'
            
            if enable_backend_extraction:
                debug_manager.store_debug_info(session_id, "🔍 启动后台爬虫提取笔记详细内容...", "INFO")
                threading.Thread(
                    target=start_backend_extraction,
                    args=(search_results, session_id),
                    daemon=True
                ).start()
            else:
                debug_manager.store_debug_info(session_id, "⚠️ 后台笔记内容提取已禁用", "INFO")
        
        # 规范化搜索结果格式
        if isinstance(search_results, dict) and 'data' in search_results:
            notes = search_results['data']
        else:
            notes = search_results if isinstance(search_results, list) else []
        
        debug_manager.store_debug_info(session_id, f"✅ 搜索完成，找到 {len(notes)} 条笔记", "INFO")
        
        # 🔧 修复3：只有在有有效笔记数据且HTML确实生成时才返回HTML URL
        if notes and len(notes) > 0:
            # 验证笔记数据的有效性
            valid_notes = [note for note in notes if note.get('title') or note.get('desc')]
            
            if valid_notes:
                # 构建响应数据
                response_data = {
                    "keyword": keyword,
                    "session_id": session_id,
                    "timestamp": int(time.time()),
                    "count": len(valid_notes),
                    "notes": valid_notes,
                    "html_generation_status": "completed" if html_ready else "pending"
                }
                
                # 🔧 修复：只有HTML确实准备好时才提供URL
                if html_ready:
                    html_url = f"/results/search_{html_hash}.html"           # 文件形式
                    html_api_url = f"/api/result-html/{html_hash}"           # API形式（推荐）
                    response_data["html_url"] = html_url
                    response_data["html_api_url"] = html_api_url
                    debug_manager.store_debug_info(session_id, f"📄 HTML页面已准备就绪: {html_api_url}", "INFO")
                else:
                    # 提供HTML状态查询端点
                    response_data["html_status_url"] = f"/api/html-status/{html_hash}"
                    debug_manager.store_debug_info(session_id, f"📄 HTML页面生成中，提供状态查询: {response_data['html_status_url']}", "INFO")
                
                return jsonify(response_data)
            else:
                debug_manager.store_debug_info(session_id, "⚠️ 笔记数据无效，没有标题或描述", "WARNING")
        
        # 🔧 修复：没有有效数据时不返回HTML URL
        debug_manager.store_debug_info(session_id, "❌ 没有找到有效的笔记数据", "WARNING")
        return jsonify({
            "keyword": keyword,
            "session_id": session_id,
            "timestamp": int(time.time()),
            "count": 0,
            "notes": [],
            "html_generation_status": "no_data",
            "message": "未找到相关笔记"
        })
    except Exception as e:
        logger.error(f"搜索出错: {str(e)}")
        logger.error(traceback.format_exc())
        debug_manager.store_debug_info(session_id, f"❌ 搜索失败: {str(e)}", "ERROR")
        return jsonify({"error": "搜索失败", "message": str(e), "session_id": session_id}), 500

@app.route('/api/note/<note_id>')
def get_note(note_id):
    """
    获取笔记详情API
    
    参数:
        note_id: 笔记ID
    
    返回:
        JSON格式的笔记详情
    """
    if not init_crawler():
        return jsonify({"error": "爬虫初始化失败"}), 500
        
    if not note_id:
        return jsonify({"error": "缺少笔记ID参数"}), 400
    
    try:
        note = crawler.get_note_detail(note_id)
        
        if note:
            return jsonify({"note": note})
        else:
            return jsonify({"error": "未找到该笔记"}), 404
    except Exception as e:
        logger.error(f"获取笔记详情出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "获取笔记详情失败", "message": str(e)}), 500

@app.route('/api/hot-keywords')
def hot_keywords():
    """
    获取热门关键词API
    
    返回:
        JSON格式的热门关键词列表
    """
    if not init_crawler():
        return jsonify({"error": "爬虫初始化失败"}), 500
        
    try:
        keywords = crawler.get_hot_keywords()
        return jsonify({"keywords": keywords})
    except Exception as e:
        logger.error(f"获取热门关键词出错: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": "获取热门关键词失败", "message": str(e)}), 500

@app.route('/api/debug/<session_id>')
def get_debug_info(session_id):
    """
    获取debug信息API
    
    参数:
        session_id: 会话ID
        since: 获取指定时间戳之后的信息（可选）
    
    返回:
        JSON格式的debug信息列表
    """
    since = request.args.get('since', type=float, default=0)
    return jsonify(debug_manager.get_debug_info(session_id, since))

@app.route('/api/html-status/<html_hash>')
def get_html_status(html_hash):
    """
    获取HTML生成状态API
    
    参数:
        html_hash: HTML内容的MD5哈希值
    
    返回:
        JSON格式的HTML状态信息
    """
    global html_results_cache
    
    try:
        # 检查内存缓存
        if html_hash in html_results_cache:
            html_url = f"/results/search_{html_hash}.html"           
            html_api_url = f"/api/result-html/{html_hash}"           
            return jsonify({
                "status": "ready",
                "html_url": html_url,
                "html_api_url": html_api_url,
                "message": "HTML页面已生成完成"
            })
        
        # 检查文件系统
        results_dir = os.path.join(get_project_root(), 'cache', 'results')
        html_file = os.path.join(results_dir, f"search_{html_hash}.html")
        
        if os.path.exists(html_file):
            # 文件存在，加载到内存缓存
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                html_results_cache[html_hash] = html_content
                
                html_url = f"/results/search_{html_hash}.html"           
                html_api_url = f"/api/result-html/{html_hash}"           
                return jsonify({
                    "status": "ready",
                    "html_url": html_url,
                    "html_api_url": html_api_url,
                    "message": "HTML页面已生成完成（从文件加载）"
                })
            except Exception as e:
                logger.error(f"加载HTML文件到缓存失败: {str(e)}")
                return jsonify({
                    "status": "error",
                    "message": f"HTML文件加载失败: {str(e)}"
                }), 500
        
        # HTML还未生成
        return jsonify({
            "status": "pending",
            "message": "HTML页面正在生成中..."
        })
        
    except Exception as e:
        logger.error(f"获取HTML状态失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"获取HTML状态失败: {str(e)}"
        }), 500

@app.route('/api/create-similar-note/<note_id>', methods=['POST'])
def create_similar_note(note_id):
    """
    创建同类笔记API
    
    参数:
        note_id: 原笔记ID
    
    返回:
        JSON格式的生成笔记内容
    """
    if not note_id:
        return jsonify({"success": False, "message": "缺少笔记ID参数"}), 400
    
    try:
        # 初始化爬虫
        if not init_crawler():
            return jsonify({"success": False, "message": "系统初始化失败"}), 500
        
        # 获取原笔记详情
        logger.info(f"正在获取原笔记详情: {note_id}")
        original_note = crawler.get_note_detail(note_id)
        
        if not original_note:
            return jsonify({"success": False, "message": "无法获取原笔记内容"}), 404
        
        # 添加note_id到原笔记信息中
        original_note['note_id'] = note_id
        
        # 笔记生成功能已移除，返回错误信息
        logger.warning(f"笔记生成功能已移除，无法生成基于笔记: {note_id} 的同类笔记")
        return jsonify({
            "success": False,
            "message": "笔记生成功能已移除，请使用其他方式"
        }), 501
        
        # 这部分代码不会执行到，因为上面已经返回了错误
        
    except Exception as e:
        logger.error(f"创建同类笔记失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False, 
            "message": f"创建同类笔记失败: {str(e)}"
        }), 500

@app.route('/api/note-generation-debug/<session_id>')
def get_note_generation_debug(session_id):
    """
    获取笔记生成debug信息API
    
    参数:
        session_id: 笔记生成会话ID
    
    返回:
        JSON格式的debug信息
    """
    try:
        # 笔记生成功能已移除
        return jsonify({
            "success": False,
            "message": "笔记生成功能已移除",
            "session_id": session_id
        }), 501
    except Exception as e:
        logger.error(f"获取笔记生成debug信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route('/api/backend-crawl-status/<session_id>')
def get_backend_crawl_status(session_id):
    """
    获取后台爬虫状态API
    
    参数:
        session_id: 会话ID
    
    返回:
        JSON格式的后台爬虫状态信息
    """
    try:
        backend_session_id = f"{session_id}_backend"
        
        # 检查后台爬虫结果目录
        temp_notes_dir = os.path.join(get_project_root(), 'temp', 'notes')
        batch_dir = os.path.join(temp_notes_dir, f"batch_{backend_session_id}")
        
        if not os.path.exists(batch_dir):
            return jsonify({
                'success': False,
                'status': 'not_started',
                'message': '后台爬虫任务尚未开始'
            })
        
        # 读取任务信息
        task_file = os.path.join(batch_dir, 'task_info.json')
        stats_file = os.path.join(batch_dir, 'crawl_stats.json')
        
        result = {
            'success': True,
            'session_id': session_id,
            'backend_session_id': backend_session_id,
            'batch_dir': batch_dir
        }
        
        # 读取任务信息
        if os.path.exists(task_file):
            with open(task_file, 'r', encoding='utf-8') as f:
                task_info = json.load(f)
                result['task_info'] = task_info
        
        # 读取统计信息
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                result['stats'] = stats
                result['status'] = 'completed'
        else:
            result['status'] = 'running'
        
        # 统计已完成的文件
        files = os.listdir(batch_dir) if os.path.exists(batch_dir) else []
        source_files = [f for f in files if f.endswith('_source.html')]
        detail_files = [f for f in files if f.endswith('_detail.json')]
        image_dirs = [f for f in files if f.endswith('_images') and os.path.isdir(os.path.join(batch_dir, f))]
        
        result['file_counts'] = {
            'source_files': len(source_files),
            'detail_files': len(detail_files),
            'image_dirs': len(image_dirs),
            'total_files': len(files)
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取后台爬虫状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/cache/notes/<path:filename>')
def serve_note_files(filename):
    """
    提供笔记相关文件的静态访问
    包括页面源码、图片等文件
    
    参数:
        filename: 文件路径（可能包含子目录）
    
    返回:
        静态文件内容
    """
    try:
        cache_notes_dir = os.path.join(get_project_root(), 'cache', 'notes')
        logger.debug(f"提供笔记文件服务: {filename} from {cache_notes_dir}")
        return send_from_directory(cache_notes_dir, filename)
    except Exception as e:
        logger.error(f"提供笔记文件服务失败: {str(e)}")
        return "文件不存在", 404

@app.route('/api/note-data')
def get_note_data():
    """
    获取笔记提取数据的API接口
    支持通过文件路径加载已提取的JSON数据
    """
    try:
        file_path = request.args.get('file')
        if not file_path:
            return jsonify({'error': '缺少文件路径参数'}), 400
        
        logger.info(f"请求笔记数据: {file_path}")
        
        # 安全检查：确保文件路径在允许的范围内
        cache_dir = os.path.join(get_project_root(), 'cache', 'notes')
        full_path = os.path.join(cache_dir, file_path)
        
        # 规范化路径，防止路径遍历攻击
        full_path = os.path.normpath(full_path)
        cache_dir = os.path.normpath(cache_dir)
        
        if not full_path.startswith(cache_dir):
            return jsonify({'error': '非法的文件路径'}), 403
        
        # 如果是HTML文件，使用统一提取器提取数据
        if file_path.endswith('.html'):
            if os.path.exists(full_path):
                logger.info(f"使用统一提取器从HTML文件提取数据: {full_path}")
                extracted_data = unified_extractor.extract_from_html_file_hybrid(full_path)
                
                if extracted_data:
                    # 尝试保存提取的数据
                    try:
                        keyword = "extracted"
                        saved_path = unified_extractor.save_unified_results(extracted_data.get('notes', []), keyword)
                        logger.info(f"已保存统一提取数据到: {saved_path}")
                    except Exception as save_error:
                        logger.warning(f"保存统一提取数据失败: {save_error}")
                    
                    return jsonify(extracted_data)
                else:
                    return jsonify({'error': '无法从HTML文件中提取数据'}), 422
            else:
                return jsonify({'error': 'HTML文件不存在'}), 404
        
        # 如果是JSON文件，直接读取
        elif file_path.endswith('.json'):
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.info(f"成功读取JSON文件: {full_path}")
                    return jsonify(data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON文件格式错误: {e}")
                    return jsonify({'error': 'JSON文件格式错误'}), 422
            else:
                return jsonify({'error': 'JSON文件不存在'}), 404
        
        else:
            return jsonify({'error': '不支持的文件类型，仅支持.html和.json文件'}), 400
            
    except Exception as e:
        logger.error(f"获取笔记数据失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/note-detail.html')
def note_detail_page():
    """笔记详情页面"""
    return send_from_directory('../../static', 'note_detail.html')

@app.route('/api/unified-extract', methods=['POST'])
def unified_extract():
    """
    统一数据提取API
    批量处理缓存中的HTML文件，使用统一提取器
    """
    try:
        # 获取参数
        data = request.get_json() or {}
        keyword = data.get('keyword', 'batch_extract')
        max_files = data.get('max_files', None)
        pattern = data.get('pattern', '*.html')
        
        logger.info(f"启动统一数据提取: keyword={keyword}, max_files={max_files}, pattern={pattern}")
        
        # 执行批量提取
        results = unified_extractor.extract_from_html_files(pattern=pattern, max_files=max_files)
        
        if results:
            # 保存统一结果
            saved_path = unified_extractor.save_unified_results(results, keyword)
            
            # 生成HTML预览
            html_file = unified_extractor._generate_html_preview(results, keyword)
            
            return jsonify({
                'success': True,
                'count': len(results),
                'notes': results,
                'saved_path': saved_path,
                'html_preview': html_file,
                'keyword': keyword,
                'extraction_info': {
                    'extractor_version': '2.0.0',
                    'processed_at': time.time(),
                    'strategies_used': list(set(note.get('method', 'unknown') for note in results))
                },
                'message': f'成功提取 {len(results)} 条笔记数据'
            })
        else:
            return jsonify({
                'success': False,
                'count': 0,
                'notes': [],
                'message': '未提取到任何数据'
            })
            
    except Exception as e:
        logger.error(f"统一数据提取失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '统一数据提取失败'
        }), 500

@app.route('/api/config/intelligent-search')
def get_intelligent_search_config():
    """
    获取智能搜索配置API
    
    返回:
        JSON格式的智能搜索配置
    """
    try:
        # 从环境变量获取配置
        import os
        import json
        
        config_str = os.environ.get('INTELLIGENT_SEARCH_CONFIG')
        if config_str:
            try:
                config = json.loads(config_str)
                logger.info(f"📋 返回智能搜索配置: {config}")
                return jsonify({
                    'success': True,
                    'config': config
                })
            except json.JSONDecodeError:
                pass
        
        # 默认配置
        default_config = {
            'enable_cache_search': False,
            'enable_html_extraction': True,
            'enable_realtime_search': False,
            'wait_for_html_save': True,
            'html_save_timeout': 30,
            'extraction_timeout': 60
        }
        
        logger.info(f"📋 返回默认智能搜索配置: {default_config}")
        return jsonify({
            'success': True,
            'config': default_config
        })
        
    except Exception as e:
        logger.error(f"获取智能搜索配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '获取智能搜索配置失败'
        }), 500

# ==================== HTML结果页面路由 ====================

@app.route('/results/<path:filename>')
def serve_results(filename):
    """
    提供HTML结果页面服务（文件形式）
    从文件系统提供预生成的HTML结果页面
    """
    results_dir = os.path.join(get_project_root(), 'cache', 'results')
    logger.debug(f"文件服务目录: {results_dir}")
    return send_from_directory(results_dir, filename)

@app.route('/api/result-html/<html_hash>')
def get_result_html(html_hash):
    """
    直接返回HTML结果页面内容（API形式，推荐）
    优先从内存缓存返回，避免文件路径问题
    
    参数:
        html_hash: HTML内容的MD5哈希值
    
    返回:
        HTML页面内容
    """
    global html_results_cache
    
    # 优先从内存缓存获取
    if html_hash in html_results_cache:
        html_content = html_results_cache[html_hash]
        logger.info(f"从内存缓存返回HTML内容: {html_hash}")
        return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    
    # 回退：尝试从文件读取
    try:
        html_filename = f"search_{html_hash}.html"
        results_dir = os.path.join(get_project_root(), 'cache', 'results')
        html_path = os.path.join(results_dir, html_filename)
        
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            # 存储到内存缓存中
            html_results_cache[html_hash] = html_content
            logger.info(f"从文件读取并缓存HTML内容: {html_path}")
            return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            logger.warning(f"HTML文件不存在: {html_path}")
            return jsonify({"error": "HTML结果页面不存在"}), 404
    except Exception as e:
        logger.error(f"读取HTML文件失败: {str(e)}")
        return jsonify({"error": "无法读取HTML文件"}), 500



# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(e):
    """处理404错误"""
    return jsonify({"error": "资源不存在"}), 404

@app.errorhandler(500)
def server_error(e):
    """处理500错误"""
    return jsonify({"error": "服务器内部错误"}), 500

# ==================== 清理函数 ====================

def cleanup():
    """应用退出时的清理工作"""
    global crawler
    if crawler:
        crawler.close()
        crawler = None

# ==================== 主程序入口 ====================

if __name__ == '__main__':
    import atexit
    
    try:
        # 创建必要的目录
        project_root = get_project_root()
        essential_dirs = [
            'cache/cookies',
            'cache/temp', 
            'cache/logs',
            'cache/results',
            'static/images'
        ]
        for dir_path in essential_dirs:
            full_path = os.path.join(project_root, dir_path)
            os.makedirs(full_path, exist_ok=True)
        
        # 注册清理函数
        atexit.register(cleanup)
        
        logger.info("小红书搜索服务启动中...")
        logger.info("访问地址: http://localhost:8080")
        logger.info("如需登录，请访问: http://localhost:8080/login")
        
        # 启动服务
        app.run(debug=False, host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        logger.info("服务已停止")
        cleanup()
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        logger.error(traceback.format_exc())
        cleanup() 