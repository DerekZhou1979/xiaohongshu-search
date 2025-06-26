/**
 * 小红书搜索API客户端
 * 提供前端与后端API通信的接口
 * 
 * 主要功能：
 * 1. 搜索笔记 - 根据关键词获取搜索结果
 * 2. 获取笔记详情 - 根据笔记ID获取详细信息  
 * 3. 获取热门关键词 - 获取推荐搜索词汇
 */

// ==================== 配置常量 ====================

// API基础URL - 本地开发环境
const API_BASE_URL = 'http://localhost:8080/api';

// 请求超时时间（毫秒）
// const REQUEST_TIMEOUT = 60000; // 60秒

// 默认热门关键词（后端API失败时的备用数据）
const DEFAULT_KEYWORDS = ['口红', '护肤品', '连衣裙', '耳机', '咖啡', '旅行'];

// ==================== 核心API函数 ====================

/**
 * 搜索小红书笔记
 * 
 * @param {string} keyword - 搜索关键词
 * @param {Object} options - 可选参数
 * @param {number} options.max_results - 最大结果数量
 * @param {boolean} options.use_cache - 是否使用缓存
 * @param {string} options.session_id - 会话ID（用于debug追踪）
 * @returns {Promise<Object>} 搜索结果对象
 * @throws {Error} 网络错误或API错误
 */
async function getRedBookNotes(keyword, options = {}) {
    // 参数验证
    if (!keyword || typeof keyword !== 'string') {
        throw new Error('搜索关键词不能为空');
    }
    
    try {
        // 生成会话ID（如果未提供）
        const sessionId = options.session_id || `search_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        // 构建查询参数
        const params = new URLSearchParams({
            keyword: keyword.trim(),
            max_results: options.max_results || 21,
            use_cache: options.use_cache !== false ? 'true' : 'false',
            session_id: sessionId
        });
        
        // 发送请求（不再设置超时）
        const response = await fetch(`${API_BASE_URL}/search?${params}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`搜索请求失败: HTTP ${response.status}`);
        }
        
        // 解析响应数据
        const data = await response.json();
        
        // 验证响应数据格式
        if (!data || typeof data !== 'object') {
            throw new Error('服务器返回数据格式错误');
        }
        
        // 确保返回的数据包含session_id
        data.session_id = data.session_id || sessionId;
        
        return data;
        
    } catch (error) {
        // 统一错误处理
        if (error.message && error.message.includes('Failed to fetch')) {
            throw new Error('网络连接失败，请检查网络状态');
        } else {
            console.error('搜索API错误:', error);
            throw error;
        }
    }
}

/**
 * 获取笔记详情
 * 
 * @param {string} noteId - 笔记ID
 * @returns {Promise<Object|null>} 笔记详情对象，不存在时返回null
 * @throws {Error} 网络错误或API错误
 */
async function getNoteDetail(noteId) {
    // 参数验证
    if (!noteId || typeof noteId !== 'string') {
        throw new Error('笔记ID不能为空');
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/note/${encodeURIComponent(noteId)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.status === 404) {
            // 笔记不存在
            return null;
        }
        
        if (!response.ok) {
            throw new Error(`获取笔记详情失败: HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return data.note || null;
        
    } catch (error) {
        console.error('笔记详情API错误:', error);
        throw error;
    }
}

/**
 * 获取热门搜索关键词
 * 
 * @returns {Promise<string[]>} 热门关键词数组
 */
async function getHotKeywords() {
    try {
        const response = await fetch(`${API_BASE_URL}/hot-keywords`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`获取热门关键词失败: HTTP ${response.status}`);
        }
        
        const data = await response.json();
        const keywords = data.keywords;
        
        // 验证返回数据
        if (Array.isArray(keywords) && keywords.length > 0) {
            return keywords;
        } else {
            // 返回默认关键词
            console.warn('服务器返回的热门关键词为空，使用默认关键词');
            return DEFAULT_KEYWORDS;
        }
        
    } catch (error) {
        console.error('热门关键词API错误:', error);
        // 发生错误时返回默认关键词
        return DEFAULT_KEYWORDS;
    }
}

/**
 * 获取debug信息
 * 
 * @param {string} sessionId - 会话ID
 * @param {number} since - 获取指定时间戳之后的信息（可选）
 * @returns {Promise<Object>} debug信息对象
 */
async function getDebugInfo(sessionId, since = 0) {
    if (!sessionId) {
        throw new Error('会话ID不能为空');
    }
    
    try {
        const params = new URLSearchParams();
        if (since > 0) {
            params.append('since', since.toString());
        }
        
        const url = `${API_BASE_URL}/debug/${encodeURIComponent(sessionId)}${params.toString() ? '?' + params.toString() : ''}`;
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`获取debug信息失败: HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('Debug信息API错误:', error);
        throw error;
    }
}

// ==================== 工具函数 ====================

/**
 * 检查API服务是否可用
 * 
 * @returns {Promise<boolean>} 服务是否可用
 */
async function checkApiHealth() {
    try {
        const response = await fetch(API_BASE_URL.replace('/api', '/'), {
            method: 'GET',
            timeout: 5000
        });
        return response.ok;
    } catch (error) {
        console.warn('API健康检查失败:', error);
        return false;
    }
}

/**
 * 执行统一批量提取
 * 
 * @param {Object} options - 提取选项
 * @param {string} options.keyword - 关键词标识
 * @param {number} options.max_files - 最大文件数量
 * @param {string} options.pattern - 文件匹配模式
 * @returns {Promise<Object>} 提取结果对象
 * @throws {Error} 网络错误或API错误
 */
async function performUnifiedExtraction(options = {}) {
    try {
        const requestData = {
            keyword: options.keyword || 'batch_extract',
            max_files: options.max_files || null,
            pattern: options.pattern || '*.html'
        };
        
        // 创建请求控制器（用于超时控制）
        const controller = new AbortController();
        const timeoutId = setTimeout(() => {
            controller.abort();
        }, REQUEST_TIMEOUT * 2); // 批量提取需要更长时间
        
        // 发送请求
        const response = await fetch(`${API_BASE_URL}/unified-extract`, {
            method: 'POST',
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        // 清除超时定时器
        clearTimeout(timeoutId);
        
        // 检查响应状态
        if (!response.ok) {
            throw new Error(`批量提取失败: HTTP ${response.status}`);
        }
        
        // 解析响应数据
        const data = await response.json();
        
        // 验证响应数据格式
        if (!data || typeof data !== 'object') {
            throw new Error('服务器返回数据格式错误');
        }
        
        return data;
        
    } catch (error) {
        // 统一错误处理
        if (error.name === 'AbortError') {
            throw new Error('批量提取超时，请重试');
        } else if (error.message.includes('Failed to fetch')) {
            throw new Error('网络连接失败，请检查网络状态');
        } else {
            console.error('批量提取API错误:', error);
            throw error;
        }
    }
}

/**
 * 获取智能搜索配置
 * 
 * @returns {Promise<Object>} 智能搜索配置对象
 */
async function getIntelligentSearchConfig() {
    try {
        const response = await fetch(`${API_BASE_URL}/config/intelligent-search`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            console.log('📋 使用默认智能搜索配置');
            return {
                enable_cache_search: false,
                enable_html_extraction: true,
                enable_realtime_search: false,
                wait_for_html_save: true,
                html_save_timeout: 30,
                extraction_timeout: 60
            };
        }
        
        const data = await response.json();
        return data.config || {
            enable_cache_search: false,
            enable_html_extraction: true,
            enable_realtime_search: false,
            wait_for_html_save: true,
            html_save_timeout: 30,
            extraction_timeout: 60
        };
        
    } catch (error) {
        console.log('📋 使用默认智能搜索配置 (API调用失败)');
        return {
            enable_cache_search: false,
            enable_html_extraction: true,
            enable_realtime_search: false,
            wait_for_html_save: true,
            html_save_timeout: 30,
            extraction_timeout: 60
        };
    }
}

/**
 * 🆕 获取HTML生成状态
 * 
 * @param {string} htmlHash - HTML内容的MD5哈希值
 * @returns {Promise<Object>} HTML状态对象
 */
async function getHtmlStatus(htmlHash) {
    try {
        const response = await fetch(`${API_BASE_URL}/html-status/${htmlHash}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`获取HTML状态失败: HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error('HTML状态查询API错误:', error);
        throw error;
    }
}

// ==================== 导出（如果需要模块化） ====================

// 如果在支持ES6模块的环境中，可以取消注释以下行
// export { getRedBookNotes, getNoteDetail, getHotKeywords, checkApiHealth, performUnifiedExtraction, getIntelligentSearchConfig }; 