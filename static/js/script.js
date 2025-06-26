/**
 * 小红书搜索前端交互脚本
 * 提供搜索界面的交互功能，包括搜索、结果展示、详情查看等
 * 
 * 主要功能：
 * 1. 搜索功能 - 关键词搜索并跳转到结果页面
 * 2. 结果展示 - 卡片式显示搜索结果（备用方案）
 * 3. 详情查看 - 模态框显示笔记详情
 * 4. 热门关键词 - 快速搜索热门词汇
 */

document.addEventListener('DOMContentLoaded', function() {
    // ==================== DOM元素获取 ====================
    
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const keywordLinks = document.querySelectorAll('.keyword');
    const brandItems = document.querySelectorAll('.brand-item');
    const loadingSection = document.getElementById('loading-section');
    const resultSection = document.getElementById('result-section');
    const emptyResult = document.getElementById('empty-result');
    const searchTermSpan = document.getElementById('search-term');
    const resultTimeDiv = document.getElementById('result-time');
    const resultContainer = document.getElementById('result-container');
    const modal = document.getElementById('note-modal');
    const modalBody = document.getElementById('modal-body');
    const closeModal = document.querySelector('.close-modal');
    
    // Debug相关元素
    const debugSection = document.getElementById('debug-section');
    const debugLatest = document.getElementById('debug-latest');
    const debugDetails = document.getElementById('debug-details');
    const debugLog = document.getElementById('debug-log');
    const debugToggle = document.getElementById('debug-toggle');
    
    // ==================== 全局变量 ====================
    
    let currentHtmlWatcher = null; // HTML生成监听器实例
    
    // ==================== 初始化设置 ====================
    
    // Logo图片加载失败时的占位图
    const logoImg = document.getElementById('logo-img');
    if (logoImg) {
        logoImg.onerror = function() {
            this.src = 'data:image/svg+xml;charset=UTF-8,%3Csvg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"%3E%3Crect width="40" height="40" fill="%23fe2c55"%3E%3C/rect%3E%3Ctext x="50%25" y="50%25" font-size="20" text-anchor="middle" alignment-baseline="middle" font-family="Arial" fill="white"%3ER%3C/text%3E%3C/svg%3E';
        };
    }
    
    // ==================== Debug信息管理 ====================
    
    let currentSessionId = null;
    let debugInterval = null;
    let lastDebugTimestamp = 0;
    let allDebugInfo = [];
    
    /**
     * 开始debug信息监控
     * @param {string} sessionId - 会话ID
     */
    function startDebugMonitoring(sessionId) {
        currentSessionId = sessionId;
        lastDebugTimestamp = 0;
        allDebugInfo = [];
        
        // 清空之前的debug信息
        clearDebugInfo();
        
        // 开始轮询debug信息
        debugInterval = setInterval(() => {
            fetchDebugInfo();
        }, 1000); // 每秒获取一次
        
        // 立即获取一次
        fetchDebugInfo();
    }
    
    /**
     * 停止debug信息监控
     */
    function stopDebugMonitoring() {
        if (debugInterval) {
            clearInterval(debugInterval);
            debugInterval = null;
        }
        currentSessionId = null;
    }
    
    /**
     * 获取debug信息
     */
    async function fetchDebugInfo() {
        if (!currentSessionId) return;
        
        try {
            const data = await getDebugInfo(currentSessionId, lastDebugTimestamp);
            
            if (data && data.debug_info && data.debug_info.length > 0) {
                // 添加新的debug信息
                allDebugInfo.push(...data.debug_info);
                
                // 更新显示
                updateDebugDisplay(data.debug_info);
                
                // 更新时间戳
                lastDebugTimestamp = data.last_timestamp || lastDebugTimestamp;
            }
        } catch (error) {
            console.error('获取debug信息失败:', error);
        }
    }
    
    /**
     * 更新debug信息显示
     * @param {Array} newDebugInfo - 新的debug信息数组
     */
    function updateDebugDisplay(newDebugInfo) {
        // 更新最新信息
        if (newDebugInfo && newDebugInfo.length > 0) {
            const latest = newDebugInfo[newDebugInfo.length - 1];
            updateLatestDebugInfo(latest);
        }
        
        // 更新详细日志
        updateDebugLog();
    }
    
    /**
     * 更新最新debug信息
     * @param {Object} latest - 最新的debug信息
     */
    function updateLatestDebugInfo(latest) {
        if (!latest || !debugLatest) return;
        
        debugLatest.innerHTML = `
            <div class="debug-item ${latest.level}">
                <span class="debug-time">${latest.time_str}</span>
                <span class="debug-message">${latest.message}</span>
            </div>
        `;
    }
    
    /**
     * 更新详细debug日志
     */
    function updateDebugLog() {
        if (!debugLog) return;
        
        debugLog.innerHTML = '';
        
        // 显示最近50条debug信息
        const recentDebugInfo = allDebugInfo.slice(-50);
        
        recentDebugInfo.forEach(item => {
            const debugItem = document.createElement('div');
            debugItem.className = `debug-item ${item.level}`;
            debugItem.innerHTML = `
                <span class="debug-time">${item.time_str}</span>
                <span class="debug-message">${item.message}</span>
            `;
            debugLog.appendChild(debugItem);
        });
        
        // 自动滚动到底部
        debugLog.scrollTop = debugLog.scrollHeight;
    }
    
    /**
     * 清空debug信息
     */
    function clearDebugInfo() {
        if (debugLatest) {
            debugLatest.innerHTML = '<div class="debug-item INFO"><span class="debug-message">等待debug信息...</span></div>';
        }
        
        if (debugLog) {
            debugLog.innerHTML = '';
        }
        
        allDebugInfo = [];
        lastDebugTimestamp = 0;
    }
    
    /**
     * 切换debug详细信息显示
     */
    window.toggleDebugDetails = function() {
        if (!debugDetails || !debugToggle) return;
        
        const isVisible = debugDetails.style.display !== 'none';
        debugDetails.style.display = isVisible ? 'none' : 'block';
        
        // 更新按钮状态
        const icon = debugToggle.querySelector('i');
        if (icon) {
            debugToggle.classList.toggle('expanded', !isVisible);
        }
    };
    
    // ==================== 批量提取功能 ====================
    
    /**
     * 执行批量提取
     */
    async function performBatchExtraction() {
        const extractButton = document.getElementById('extract-button');
        
        // 禁用按钮，防止重复点击
        if (extractButton) {
            extractButton.disabled = true;
            extractButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在提取...';
        }
        
        try {
            // 显示加载状态
            showLoadingState('正在执行批量提取');
            showLoadingProgress('扫描缓存目录中的HTML文件...');
            
            // 获取关键词（如果有搜索过的话）
            const keyword = searchInput.value.trim() || 'batch_extract_' + Date.now();
            
            // 执行统一提取
            const result = await performUnifiedExtraction({
                keyword: keyword,
                max_files: 50, // 限制最大文件数量
                pattern: '*.html'
            });
            
            if (result.success && result.notes && result.notes.length > 0) {
                // 显示提取成功消息
                showLoadingProgress(`提取成功！共找到 ${result.count} 条笔记数据`);
                
                // 等待2秒后显示结果
                setTimeout(() => {
                    handleExtractionSuccess(result);
                }, 2000);
            } else {
                handleExtractionError(new Error(result.message || '未提取到任何数据'));
            }
            
        } catch (error) {
            console.error('批量提取失败:', error);
            handleExtractionError(error);
        } finally {
            // 恢复按钮状态
            if (extractButton) {
                extractButton.disabled = false;
                extractButton.innerHTML = '<i class="fas fa-download"></i> 批量提取缓存';
            }
        }
    }
    
    /**
     * 处理提取成功
     * @param {Object} result - 提取结果
     */
    function handleExtractionSuccess(result) {
        // 停止debug监控
        stopDebugMonitoring();
        
        // 隐藏加载状态
        if (loadingSection) loadingSection.style.display = 'none';
        
        // 设置搜索词显示
        if (searchTermSpan) {
            searchTermSpan.textContent = `缓存提取 (${result.keyword})`;
        }
        
        // 设置结果时间
        if (resultTimeDiv) {
            resultTimeDiv.textContent = `提取时间: ${new Date().toLocaleString()} | 共 ${result.count} 条记录`;
        }
        
        // 显示结果
        showTraditionalResults(result.notes);
        
        // 显示成功提示
        if (result.html_preview) {
            console.log('HTML预览文件已生成:', result.html_preview);
        }
        
        // 在控制台显示详细信息
        console.log('批量提取结果:', {
            count: result.count,
            strategies: result.extraction_info?.strategies_used,
            saved_path: result.saved_path,
            html_preview: result.html_preview
        });
    }
    
    /**
     * 处理提取错误
     * @param {Error} error - 错误对象
     */
    function handleExtractionError(error) {
        console.error('批量提取失败:', error);
        
        // 停止debug监控
        stopDebugMonitoring();
        
        // 隐藏加载状态
        if (loadingSection) loadingSection.style.display = 'none';
        
        // 显示错误提示
        if (emptyResult) {
            emptyResult.style.display = 'block';
            
            // 修改错误提示内容
            const emptyIcon = emptyResult.querySelector('.empty-icon i');
            const emptyTitle = emptyResult.querySelector('h2');
            const emptyText = emptyResult.querySelector('p');
            
            if (emptyIcon) emptyIcon.className = 'fas fa-exclamation-triangle';
            if (emptyTitle) emptyTitle.textContent = '批量提取失败';
            if (emptyText) emptyText.textContent = error.message || '请检查缓存目录是否有HTML文件';
        }
    }

    // ==================== 新一体化搜索主流程 ====================

    /**
     * 一体化搜索并等待HTML生成，最终才跳转或报错
     * @param {string} keyword - 搜索关键词
     */
    async function performSearchAndWaitHtml(keyword) {
        // 1. 发起搜索，获取html_hash
        let htmlHash = null, statusUrl = null;
        try {
            showLoadingState(keyword);
            const data = await getRedBookNotes(keyword, { session_id: `search_${Date.now()}` });
            // 兼容不同后端返回
            htmlHash = (data.html_api_url || data.html_url || data.html_status_url || '').match(/[a-f0-9]{32}/)?.[0];
            statusUrl = data.html_status_url || (htmlHash ? `/api/html-status/${htmlHash}` : null);
            if (!statusUrl) throw new Error('未获取到HTML状态查询地址');
        } catch (e) {
            handleSearchError(new Error('搜索请求失败，请稍后重试'));
            return;
        }

        // 2. 轮询html-status，直到ready/error/超时
        let attempts = 0, maxAttempts = 300; // 最多300秒（5分钟）
        while (attempts < maxAttempts) {
            attempts++;
            try {
                const res = await fetch(statusUrl);
                if (!res.ok) throw new Error('状态查询失败');
                const statusData = await res.json();
                if (statusData.status === 'ready' && statusData.html_api_url) {
                    hideLoadingState();
                    window.open(statusData.html_api_url, '_blank');
                    window.location.href = statusData.html_api_url;
                    return;
                }
                if (statusData.status === 'error') {
                    hideLoadingState();
                    handleSearchError(new Error(statusData.message || 'HTML生成失败'));
                    return;
                }
                // 继续等待
                showLoadingProgress(`正在生成HTML页面... (${attempts}s)`);
            } catch (e) {
                // 网络异常也继续等待
                showLoadingProgress(`正在生成HTML页面... (${attempts}s)`);
            }
            await new Promise(r => setTimeout(r, 1000));
        }
        // 超时
        hideLoadingState();
        handleSearchError(new Error('HTML生成超时，请稍后重试'));
    }

    // ==================== 搜索按钮事件绑定 ====================

    if (searchButton) {
        searchButton.addEventListener('click', function() {
            const keyword = searchInput.value.trim();
            if (!keyword) {
                alert('请输入搜索关键词');
                return;
            }
            performSearchAndWaitHtml(keyword);
        });
    }

    // ==================== 核心搜索功能 ====================
    
    /**
     * 智能搜索：整合缓存和深度提取功能
     * @param {string} keyword - 搜索关键词
     * @param {Object} options - 搜索选项
     */
    async function performIntelligentSearch(keyword, options = {}) {
        try {
            // 显示加载状态
            showLoadingState(keyword);
            showLoadingProgress('正在执行智能搜索...');
            
            // 生成会话ID
            const sessionId = `search_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            
            // 开始debug监控
            startDebugMonitoring(sessionId);
            
            console.log('🔍 执行智能搜索:', keyword);
            console.log('🔧 搜索选项:', options);
            
            // 🆕 获取智能搜索配置
            const searchConfig = await getIntelligentSearchConfig();
            console.log('📋 智能搜索配置:', searchConfig);
            
            let finalResult = null;
            let searchResults = [];
            
            // 根据配置执行多种搜索策略
            if (searchConfig.enable_html_extraction) {
                console.log('📄 执行HTML提取搜索...');
                showLoadingProgress('正在从HTML文件提取数据...');
                try {
                    const extractResult = await performUnifiedExtraction({
                        keyword: keyword,
                        max_files: 10,
                        pattern: '*.html'
                    });
                    
                    if (extractResult && extractResult.notes && extractResult.notes.length > 0) {
                        console.log(`✅ HTML提取成功: ${extractResult.notes.length} 条结果`);
                        searchResults.push({type: 'html_extraction', result: extractResult});
                        if (!finalResult) finalResult = extractResult;
                    }
                } catch (error) {
                    console.log('❌ HTML提取失败:', error);
                }
            }
            
            if (searchConfig.enable_cache_search) {
                console.log('💾 执行缓存搜索...');
                showLoadingProgress('正在搜索缓存数据...');
                try {
                    const cacheResult = await getRedBookNotes(keyword, { 
                        session_id: sessionId,
                        use_cache_only: true 
                    });
                    
                    if (cacheResult && cacheResult.notes && cacheResult.notes.length > 0) {
                        console.log(`✅ 缓存搜索成功: ${cacheResult.notes.length} 条结果`);
                        searchResults.push({type: 'cache_search', result: cacheResult});
                        if (!finalResult) finalResult = cacheResult;
                    }
                } catch (error) {
                    console.log('❌ 缓存搜索失败:', error);
                }
            }
            
            if (searchConfig.enable_realtime_search) {
                console.log('🔥 执行实时搜索...');
                showLoadingProgress('正在进行实时搜索...');
                try {
                    const realtimeResult = await getRedBookNotes(keyword, { 
                        session_id: sessionId,
                        force_fresh: true 
                    });
                    
                    if (realtimeResult && realtimeResult.notes && realtimeResult.notes.length > 0) {
                        console.log(`✅ 实时搜索成功: ${realtimeResult.notes.length} 条结果`);
                        searchResults.push({type: 'realtime_search', result: realtimeResult});
                        finalResult = realtimeResult; // 实时搜索结果优先级最高
                    }
                } catch (error) {
                    console.log('❌ 实时搜索失败:', error);
                }
            }
            
            console.log(`📊 智能搜索完成: 执行了 ${searchResults.length} 种策略`);
            
            if (finalResult) {
                // 🔧 修复：处理新的HTML状态响应格式
                const htmlStatus = finalResult.html_generation_status || 'unknown';
                const hasHtmlUrl = finalResult && (finalResult.html_api_url || finalResult.html_url);
                const hasHtmlStatusUrl = finalResult && finalResult.html_status_url;
                
                console.log(`📊 最终结果状态: HTML=${htmlStatus}, URL=${hasHtmlUrl ? '有' : '无'}, 状态URL=${hasHtmlStatusUrl ? '有' : '无'}`);
                
                // 根据HTML状态决定是否等待
                if (htmlStatus === 'completed' && hasHtmlUrl) {
                    // HTML已准备就绪，直接处理
                    console.log('✅ HTML已准备就绪，直接处理结果');
                    stopDebugMonitoring();
                    handleSearchSuccess(finalResult);
                } else if (htmlStatus === 'pending' || hasHtmlStatusUrl) {
                    // HTML正在生成或有状态查询URL，交给handleSearchSuccess处理
                    console.log('⏳ HTML生成中，交给状态处理器');
                    stopDebugMonitoring();
                    handleSearchSuccess(finalResult);
                } else if (searchConfig.wait_for_html_save && hasHtmlUrl) {
                    // 兼容模式：配置了等待HTML保存，启动HTML监听器
                    console.log('⏳ 兼容模式：等待HTML保存完成...');
                    showLoadingProgress('等待HTML页面生成完成...');
                    stopDebugMonitoring();
                    handleSearchSuccess(finalResult);
                } else {
                    // 直接显示结果（无HTML或不等待HTML）
                    console.log('📄 直接显示搜索结果（无HTML生成）');
                    stopDebugMonitoring();
                    handleSearchSuccess(finalResult);
                }
            } else {
                // 没有找到任何结果
                stopDebugMonitoring();
                handleSearchError(new Error('所有搜索策略均未找到结果'));
            }
            
        } catch (error) {
            console.error('❌ 智能搜索失败:', error);
            stopDebugMonitoring();
            handleSearchError(error);
        }
    }
    
    /**
     * 执行搜索
     * @param {string} keyword - 搜索关键词
     */
    function performSearch(keyword) {
        // 参数验证
        if (!keyword.trim()) {
            alert('请输入搜索关键词');
            return;
        }
        
        // 显示加载状态
        showLoadingState(keyword);
        
        // 生成会话ID
        const sessionId = `search_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        // 开始debug监控
        startDebugMonitoring(sessionId);
        
        // 执行搜索并处理结果
        getRedBookNotes(keyword, { session_id: sessionId })
            .then(data => {
                // 停止debug监控
                stopDebugMonitoring();
                handleSearchSuccess(data);
            })
            .catch(error => {
                // 停止debug监控
                stopDebugMonitoring();
                handleSearchError(error);
            });
    }
    
    /**
     * 显示加载状态
     * @param {string} keyword - 搜索关键词
     */
    function showLoadingState(keyword) {
        // 切换界面状态
        loadingSection.style.display = 'block';
        resultSection.style.display = 'none';
        emptyResult.style.display = 'none';
        
        // 更新搜索词显示
        searchTermSpan.textContent = keyword;
        
        // 显示详细的加载进度
        const loadingText = document.querySelector('#loading-section .loading-text');
        if (loadingText) {
            showLoadingProgress(loadingText);
        }
    }
    
    /**
     * 显示加载进度
     * @param {Element} loadingText - 加载文本元素
     */
    function showLoadingProgress(loadingText) {
        const progressSteps = [
            { text: '正在初始化搜索引擎...', delay: 0 },
            { text: '正在访问小红书页面...', delay: 3000 },
            { text: '正在分析页面内容...', delay: 8000 },
            { text: '正在提取笔记数据...', delay: 15000 }
        ];
        
        progressSteps.forEach(step => {
            setTimeout(() => {
                if (loadingText.textContent.includes(progressSteps[progressSteps.indexOf(step) - 1]?.text.split('正在')[1].split('...')[0] || '初始化')) {
                    loadingText.textContent = step.text;
                }
            }, step.delay);
        });
    }
    
    /**
     * 处理搜索成功
     * @param {Object} data - 搜索结果数据
     */
    function handleSearchSuccess(data) {
        console.log('🎯 搜索结果数据:', data);
        
        // 🔧 修复：检查新的HTML生成状态字段
        const hasValidNotes = data && data.notes && data.notes.length > 0;
        const htmlStatus = data.html_generation_status || 'unknown';
        const hasHtmlUrl = data && (data.html_api_url || data.html_url);
        const hasHtmlStatusUrl = data && data.html_status_url;
        const hasKeyword = data && data.keyword;
        
        // 🆕 显示搜索结果概要
        console.log(`📊 搜索结果概要:`);
        console.log(`   - 关键词: ${hasKeyword ? data.keyword : '无'}`);
        console.log(`   - 笔记数量: ${hasValidNotes ? data.notes.length : 0}`);
        console.log(`   - HTML状态: ${htmlStatus}`);
        console.log(`   - HTML URL: ${hasHtmlUrl ? (data.html_api_url || data.html_url) : '无'}`);
        console.log(`   - HTML状态URL: ${hasHtmlStatusUrl ? data.html_status_url : '无'}`);
        console.log(`   - 总数量: ${data.count || 0}`);
        
        if (hasValidNotes) {
            // 根据HTML状态决定处理策略
            if (htmlStatus === 'completed' && hasHtmlUrl) {
                // HTML已准备就绪，直接跳转
                console.log('🎯 HTML页面已准备就绪，直接跳转');
                hideLoadingState();
                window.location.href = data.html_api_url || data.html_url;
            } else if (htmlStatus === 'pending' && hasHtmlStatusUrl) {
                // HTML正在生成，使用状态查询API轮询
                console.log('🎯 HTML页面生成中，启动状态轮询...');
                startHtmlStatusPolling(data.html_status_url, data);
            } else if (hasHtmlUrl) {
                // 兼容旧版本：有HTML URL但状态未知，使用原有监听器
                console.log('🎯 兼容模式：使用HTML生成监听器...');
                startHtmlSaveWatcher(data, hasValidNotes);
            } else {
                // 没有HTML URL，使用备用显示
                console.log('🎯 备用策略: 没有HTML信息，使用传统显示方式');
                hideLoadingState();
                handleFallbackDisplay(data, hasValidNotes);
            }
        } else {
            // 🎯 没有有效笔记数据
            console.log('🎯 没有找到有效笔记数据，显示空结果');
            hideLoadingState();
            emptyResult.style.display = 'block';
        }
    }
    
    /**
     * 🆕 HTML生成和保存状态监听器
     * 实时监控HTML生成和保存状态，一旦完成立即跳转
     * @param {Object} data - 搜索结果数据
     * @param {boolean} hasValidNotes - 是否有有效笔记数据
     */
    async function startHtmlSaveWatcher(data, hasValidNotes) {
        const htmlUrl = data.html_api_url || data.html_url;
        const sessionId = data.session_id;
        const expectedCount = data.count || data.notes?.length || 0;
        const keyword = data.keyword;
        
        console.log('🎯 启动HTML生成状态监听器...');
        console.log(`📊 输入数据:`, data);
        console.log(`📊 监控参数: URL=${htmlUrl}, SessionID=${sessionId}, 期望数量=${expectedCount}, 关键词=${keyword}`);
        
        // 🆕 验证必要参数
        if (!htmlUrl && !sessionId && !keyword) {
            console.error('❌ 监听器启动失败: 缺少必要参数 (需要HTML URL、会话ID或关键词中的至少一个)');
            handleFallbackDisplay(data, hasValidNotes);
            return;
        }
        
        // 🆕 停止之前的监听器（如果存在）
        if (currentHtmlWatcher) {
            console.log('🛑 停止之前的HTML监听器');
            currentHtmlWatcher.stop();
            currentHtmlWatcher = null;
        }
        
        // 创建状态监听器
        const watcher = new HtmlGenerationWatcher({
            htmlUrl: htmlUrl,
            sessionId: sessionId,
            keyword: keyword,
            expectedCount: expectedCount,
            checkInterval: 1000, // 每1秒检查一次
            maxDuration: 60000,  // 最大等待60秒
            onProgress: (status) => {
                showLoadingProgress(status.message);
                console.log(`📊 状态更新: ${status.message} (${status.phase})`);
            },
            onSuccess: (finalUrl) => {
                console.log('✅ HTML生成完成，准备跳转到:', finalUrl);
                hideLoadingState();
                window.location.href = finalUrl;
            },
            onFailure: (error) => {
                console.log('❌ HTML生成监控失败:', error);
                hideLoadingState();
                handleFallbackDisplay(data, hasValidNotes);
            }
        });
        
        // 保存监听器引用并启动
        currentHtmlWatcher = watcher;
        watcher.start();
    }
    
    /**
     * 🆕 HTML生成状态监听器类
     */
    class HtmlGenerationWatcher {
        constructor(options) {
            this.htmlUrl = options.htmlUrl;
            this.sessionId = options.sessionId;
            this.keyword = options.keyword;
            this.expectedCount = options.expectedCount;
            this.checkInterval = options.checkInterval || 1000;
            this.maxDuration = options.maxDuration || 60000;
            this.onProgress = options.onProgress || (() => {});
            this.onSuccess = options.onSuccess || (() => {});
            this.onFailure = options.onFailure || (() => {});
            
            this.isRunning = false;
            this.startTime = null;
            this.checkCount = 0;
            this.lastStatus = 'initializing';
            this.timer = null;
        }
        
        start() {
            if (this.isRunning) {
                console.warn('⚠️ 监听器已在运行中，跳过启动');
                return;
            }
            
            this.isRunning = true;
            this.startTime = Date.now();
            this.checkCount = 0;
            
            console.log('🚀 HTML生成监听器启动');
            console.log(`📋 监听配置: 间隔=${this.checkInterval}ms, 超时=${this.maxDuration}ms`);
            console.log(`🎯 目标: URL=${this.htmlUrl}, 会话=${this.sessionId}, 关键词=${this.keyword}`);
            
            this.onProgress({
                phase: 'starting',
                message: '正在启动HTML生成监控...',
                progress: 0
            });
            
            // 立即执行第一次检查
            console.log('⏰ 启动第一次检查...');
            this.performCheck();
        }
        
        stop() {
            if (this.timer) {
                clearTimeout(this.timer);
                this.timer = null;
            }
            this.isRunning = false;
            console.log('🛑 HTML生成监听器停止');
        }
        
        async performCheck() {
            if (!this.isRunning) {
                console.log('⏹️ 监听器已停止，跳过检查');
                return;
            }
            
            this.checkCount++;
            const elapsed = Date.now() - this.startTime;
            const progress = Math.min((elapsed / this.maxDuration) * 100, 95);
            
            try {
                console.log(`🔍 监听器检查 #${this.checkCount} (已用时${Math.round(elapsed/1000)}秒) - 进度${progress.toFixed(1)}%`);
                
                // 检查是否超时
                if (elapsed >= this.maxDuration) {
                    console.log(`⏰ 监听器超时 (${elapsed}ms >= ${this.maxDuration}ms)`);
                    this.handleTimeout();
                    return;
                }
                
                // 多种检查策略
                console.log('🔄 开始执行多阶段检查...');
                const checkResult = await this.performMultiStageCheck();
                
                if (checkResult.success) {
                    console.log('✅ 检查成功，准备处理结果:', checkResult.url);
                    this.handleSuccess(checkResult.url);
                    return;
                } else {
                    console.log(`⏳ 检查未完成: ${checkResult.phase} - ${checkResult.message}`);
                }
                
                // 更新进度
                this.onProgress({
                    phase: checkResult.phase,
                    message: checkResult.message,
                    progress: progress,
                    checkCount: this.checkCount,
                    elapsed: Math.round(elapsed/1000)
                });
                
                // 安排下一次检查
                console.log(`⏰ 安排下次检查，间隔${this.checkInterval}ms`);
                this.scheduleNextCheck();
                
            } catch (error) {
                console.error('❌ 监听器检查出错:', error);
                this.handleError(error);
            }
        }
        
        async performMultiStageCheck() {
            console.log('🔄 执行多阶段检查策略...');
            
            // 阶段1: 检查HTML URL是否可访问
            if (this.htmlUrl) {
                console.log('📄 阶段1: 检查HTML URL -', this.htmlUrl);
                const urlCheck = await this.checkHtmlUrl();
                console.log('📄 阶段1结果:', urlCheck.success ? '✅ 成功' : `❌ 失败 - ${urlCheck.message}`);
                if (urlCheck.success) {
                    return urlCheck;
                }
            } else {
                console.log('📄 阶段1: 跳过 - 无HTML URL');
            }
            
            // 阶段2: 通过会话ID检查后端状态
            if (this.sessionId) {
                console.log('🔍 阶段2: 检查会话状态 -', this.sessionId);
                const sessionCheck = await this.checkSessionStatus();
                console.log('🔍 阶段2结果:', sessionCheck.htmlReady ? '✅ HTML准备就绪' : '⏳ HTML未准备好');
                if (sessionCheck.htmlReady) {
                    console.log('🔄 阶段2: HTML准备就绪，重新检查URL...');
                    return await this.checkHtmlUrl(); // 重新检查HTML
                }
            } else {
                console.log('🔍 阶段2: 跳过 - 无会话ID');
            }
            
            // 阶段3: 通过关键词查找已生成的HTML文件
            if (this.keyword) {
                console.log('🔑 阶段3: 通过关键词搜索 -', this.keyword);
                const keywordCheck = await this.checkByKeyword();
                console.log('🔑 阶段3结果:', keywordCheck.success ? `✅ 找到 - ${keywordCheck.url}` : `❌ 未找到 - ${keywordCheck.message}`);
                if (keywordCheck.success) {
                    return keywordCheck;
                }
            } else {
                console.log('🔑 阶段3: 跳过 - 无关键词');
            }
            
            // 返回当前状态
            console.log('⏳ 所有阶段均未完成，继续等待...');
            return {
                success: false,
                phase: 'waiting',
                message: `正在生成HTML页面... (检查 #${this.checkCount})`
            };
        }
        
        async checkHtmlUrl() {
            try {
                const response = await fetch(this.htmlUrl, { method: 'HEAD' });
                
                if (response.ok) {
                    // 验证内容完整性
                    const isComplete = await verifyHtmlContent(this.htmlUrl, this.expectedCount);
                    
                    if (isComplete) {
                        return {
                            success: true,
                            url: this.htmlUrl,
                            phase: 'completed',
                            message: 'HTML页面生成完成！'
                        };
                    } else {
                        return {
                            success: false,
                            phase: 'generating',
                            message: 'HTML页面正在生成内容...'
                        };
                    }
                } else {
                    return {
                        success: false,
                        phase: 'creating',
                        message: 'HTML页面正在创建...'
                    };
                }
            } catch (error) {
                return {
                    success: false,
                    phase: 'error',
                    message: '检查HTML页面时出错'
                };
            }
        }
        
                 async checkSessionStatus() {
             try {
                 if (!this.sessionId) {
                     return { htmlReady: false };
                 }
                 
                 const response = await fetch(`/api/debug/${this.sessionId}?since=${this.startTime}`);
                 
                 if (response.ok) {
                     const debugInfo = await response.json();
                     
                     // 查找HTML生成完成的日志
                     const htmlCompleted = debugInfo.some(log => 
                         log.message && (
                             log.message.includes('HTML结果页面已生成') ||
                             log.message.includes('HTML内容已通过回调函数传递') ||
                             log.message.includes('生成HTML页面') ||
                             log.message.includes('📄 生成HTML页面')
                         )
                     );
                     
                     if (htmlCompleted) {
                         console.log('🎯 后端日志显示HTML已生成完成');
                     }
                     
                     return { htmlReady: htmlCompleted };
                 }
                 
                 return { htmlReady: false };
             } catch (error) {
                 console.warn('检查会话状态失败:', error);
                 return { htmlReady: false };
             }
         }
        
        async checkByKeyword() {
            try {
                const possibleUrls = await this.generatePossibleUrls();
                
                for (const url of possibleUrls) {
                    try {
                        const response = await fetch(url, { method: 'HEAD' });
                        if (response.ok) {
                            const isComplete = await verifyHtmlContent(url, this.expectedCount);
                            if (isComplete) {
                                return {
                                    success: true,
                                    url: url,
                                    phase: 'found',
                                    message: '通过关键词找到完整HTML页面！'
                                };
                            }
                        }
                    } catch (e) {
                        // 忽略单个URL的错误
                    }
                }
                
                return {
                    success: false,
                    phase: 'searching',
                    message: '正在搜索已生成的HTML文件...'
                };
            } catch (error) {
                return {
                    success: false,
                    phase: 'search_error',
                    message: '搜索HTML文件时出错'
                };
            }
        }
        
        async generatePossibleUrls() {
            const urls = [];
            
            if (this.keyword) {
                // MD5哈希方式
                const hash = generateMD5Hash(this.keyword);
                urls.push(`/api/result-html/${hash}`);
                urls.push(`/results/search_${hash}.html`);
                
                // 简单哈希方式
                const simpleHash = generateSimpleHash(this.keyword);
                urls.push(`/api/result-html/${simpleHash}`);
                urls.push(`/results/search_${simpleHash}.html`);
            }
            
            return urls;
        }
        
        scheduleNextCheck() {
            if (this.isRunning) {
                console.log(`⏰ 安排下次检查: ${this.checkInterval}ms后执行第${this.checkCount + 1}次检查`);
                this.timer = setTimeout(() => {
                    console.log(`⏰ 执行预定检查 #${this.checkCount + 1}`);
                    this.performCheck();
                }, this.checkInterval);
            } else {
                console.log('⏹️ 监听器已停止，取消下次检查');
            }
        }
        
        handleSuccess(url) {
            this.stop();
            this.onSuccess(url);
        }
        
        handleTimeout() {
            console.log('⏰ 监听器处理超时');
            this.stop();
            this.onFailure('HTML生成超时');
        }
        
        handleError(error) {
            console.error('❌ 监听器处理错误:', error);
            this.stop();
            this.onFailure(error);
        }
    }
    

    
    /**
     * 🆕 验证HTML内容完整性
     * @param {string} htmlUrl - HTML文件URL
     * @param {number} expectedCount - 期望的笔记数量
     * @returns {Promise<boolean>} - 内容是否完整
     */
    async function verifyHtmlContent(htmlUrl, expectedCount) {
        try {
            console.log(`🔍 验证HTML内容完整性: ${htmlUrl}, 期望笔记数: ${expectedCount}`);
            
            const response = await fetch(htmlUrl);
            if (!response.ok) {
                console.log(`❌ HTTP响应失败: ${response.status}`);
                return false;
            }
            
            const htmlText = await response.text();
            
            // 🆕 增强的基本结构检查
            const basicChecks = [
                // HTML结构完整性
                htmlText.includes('<html'),
                htmlText.includes('</html>'),
                htmlText.includes('<body'),
                htmlText.includes('</body>'),
                htmlText.includes('<title>'),
                
                // CSS和样式加载
                htmlText.includes('<style>') || htmlText.includes('.css'),
                
                // 内容区域存在
                htmlText.includes('class="container"') || htmlText.includes('class="results-grid"'),
                
                // 基本长度检查 - 提高要求
                htmlText.length > 20000, // 提高到20KB
            ];
            
            // 🆕 内容完整性检查
            const contentChecks = [
                // 笔记卡片相关元素
                htmlText.includes('note-card'),
                htmlText.includes('note-title'),
                htmlText.includes('note-desc'),
                htmlText.includes('note-author'),
                htmlText.includes('note-image'),
                
                // 交互元素
                htmlText.includes('direct-link') || htmlText.includes('直接访问'),
                htmlText.includes('create-link') || htmlText.includes('新增同类笔记'),
                
                // JavaScript功能
                htmlText.includes('function ') || htmlText.includes('directAccess'),
            ];
            
            // 🆕 数据量验证 - 更严格的检查
            let dataChecks = [];
            if (expectedCount > 0) {
                const noteCardMatches = (htmlText.match(/class="note-card"/g) || []).length;
                const noteTitleMatches = (htmlText.match(/class="note-title"/g) || []).length;
                const noteImageMatches = (htmlText.match(/class="note-image"/g) || []).length;
                
                // 要求至少80%的内容完整性
                const minExpected = Math.max(1, Math.floor(expectedCount * 0.8));
                
                dataChecks = [
                    noteCardMatches >= minExpected,
                    noteTitleMatches >= minExpected,
                    noteImageMatches >= minExpected,
                    // 确保卡片、标题、图片数量基本一致
                    Math.abs(noteCardMatches - noteTitleMatches) <= 2,
                    Math.abs(noteCardMatches - noteImageMatches) <= 2
                ];
                
                console.log(`📊 数据验证: 卡片=${noteCardMatches}, 标题=${noteTitleMatches}, 图片=${noteImageMatches}, 期望>=${minExpected}`);
            }
            
            // 综合检查结果
            const allChecks = [...basicChecks, ...contentChecks, ...dataChecks];
            const passedChecks = allChecks.filter(check => check).length;
            const totalChecks = allChecks.length;
            const passRate = passedChecks / totalChecks;
            
            // 要求95%以上的检查通过
            const isComplete = passRate >= 0.95;
            
            console.log(`📝 HTML内容完整性检查: ${passedChecks}/${totalChecks} 通过 (${(passRate * 100).toFixed(1)}%)`);
            console.log(`📋 基本结构: ${basicChecks.filter(c => c).length}/${basicChecks.length}`);
            console.log(`📋 内容检查: ${contentChecks.filter(c => c).length}/${contentChecks.length}`);
            if (dataChecks.length > 0) {
                console.log(`📋 数据验证: ${dataChecks.filter(c => c).length}/${dataChecks.length}`);
            }
            console.log(`🎯 最终结果: ${isComplete ? '✅ 通过' : '❌ 未通过'}`);
            
            return isComplete;
            
        } catch (error) {
            console.error('验证HTML内容失败:', error);
            return false;
        }
    }
    
    /**
     * 🆕 隐藏加载状态
     */
    function hideLoadingState() {
        if (loadingSection) {
            loadingSection.style.display = 'none';
        }
    }
    
    /**
     * 🆕 处理备用显示逻辑
     * @param {Object} data - 搜索结果数据
     * @param {boolean} hasValidNotes - 是否有有效笔记数据
     */
    function handleFallbackDisplay(data, hasValidNotes) {
        if (hasValidNotes) {
            // 有笔记数据，使用传统方式显示
            console.log('有笔记数据，使用传统方式显示');
            showTraditionalResults(data.notes);
        } else {
            // 显示空结果提示
            console.log('没有笔记数据，显示空结果提示');
            emptyResult.style.display = 'block';
        }
    }
    
    /**
     * 🆕 检查已存在的HTML文件
     * @param {string} keyword - 搜索关键词
     * @returns {Promise<string|null>} - 找到的HTML URL或null
     */
    async function checkExistingHtmlFiles(keyword) {
        // 策略1：使用常见的哈希方式构建路径
        const possiblePaths = [
            // MD5哈希路径（最常见）
            generatePossibleMD5Paths(keyword),
            // 时间戳路径
            generateRecentTimestampPaths(),
            // 直接扫描已知文件
            getKnownHtmlFiles()
        ].flat();
        
        console.log('🔍 检查可能的HTML路径:', possiblePaths);
        
        // 并行检查所有可能的路径
        for (const path of possiblePaths) {
            try {
                const response = await fetch(path, { method: 'HEAD' });
                if (response.ok) {
                    console.log('✅ 找到有效的HTML文件:', path);
                    return path;
                }
            } catch (error) {
                // 忽略404等错误，继续检查下一个
                console.debug('检查路径失败:', path, error.message);
            }
        }
        
        return null;
    }
    
    /**
     * 🆕 生成可能的MD5路径
     * @param {string} keyword - 关键词
     * @returns {Array<string>} - 可能的路径数组
     */
    function generatePossibleMD5Paths(keyword) {
        // 考虑不同的编码和格式
        const variations = [
            keyword,
            keyword.trim(),
            encodeURIComponent(keyword),
            keyword.replace(/\s+/g, ''),
        ];
        
        const paths = [];
        variations.forEach(variant => {
            const hash = generateSimpleHash(variant);
            paths.push(`/results/search_${hash}.html`);
            paths.push(`/api/result-html/${hash}`);
        });
        
        return paths;
    }
    
    /**
     * 🆕 生成最近时间戳路径
     * @returns {Array<string>} - 最近的时间戳路径
     */
    function generateRecentTimestampPaths() {
        const paths = [];
        const now = Date.now();
        
        // 检查最近1小时内的时间戳
        for (let i = 0; i < 60; i++) {
            const timestamp = Math.floor((now - i * 60000) / 1000); // 每分钟检查一次
            const hash = timestamp.toString(16);
            paths.push(`/results/search_${hash}.html`);
            paths.push(`/api/result-html/${hash}`);
        }
        
        return paths.slice(0, 20); // 限制检查数量
    }
    
    /**
     * 🆕 获取已知的HTML文件路径
     * @returns {Array<string>} - 已知文件路径
     */
    function getKnownHtmlFiles() {
        // 基于已知的文件名模式
        const knownFiles = [
            'search_4deb2e9c1a88e91e98eef4876d4eed6c.html', // 海鸥表的已知文件
        ];
        
        const paths = [];
        knownFiles.forEach(filename => {
            paths.push(`/results/${filename}`);
            // 提取哈希部分用于API路径
            const hashMatch = filename.match(/search_([a-f0-9]+)\.html/);
            if (hashMatch) {
                paths.push(`/api/result-html/${hashMatch[1]}`);
            }
        });
        
        return paths;
    }
    
    /**
     * 🆕 生成简单哈希值
     * @param {string} str - 输入字符串
     * @returns {string} - 哈希值
     */
    function generateSimpleHash(str) {
        let hash = 0;
        if (str.length === 0) return hash.toString(16);
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        return Math.abs(hash).toString(16);
    }
    
    /**
     * 🆕 生成MD5哈希值（简化版本）
     * @param {string} str - 输入字符串
     * @returns {string} - MD5哈希值
     */
    function generateMD5Hash(str) {
        // 简化的哈希算法，用于前端生成哈希值
        // 注意：这不是真正的MD5，只是一个简单的哈希函数
        let hash = 0;
        if (str.length === 0) return hash.toString(16);
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // 转换为32位整数
        }
        return Math.abs(hash).toString(16);
    }
    
    /**
     * 处理搜索错误
     * @param {Error} error - 错误对象
     */
    function handleSearchError(error) {
        console.error('搜索出错:', error);
        
        // 🔧 修复：确保加载状态被隐藏
        hideLoadingState();
        
        // 🔧 修复：提供更详细的错误信息
        if (emptyResult) {
            emptyResult.style.display = 'block';
            
            // 更新错误提示内容
            const emptyIcon = emptyResult.querySelector('.empty-icon i');
            const emptyTitle = emptyResult.querySelector('h2');
            const emptyText = emptyResult.querySelector('p');
            
            if (emptyIcon) emptyIcon.className = 'fas fa-exclamation-triangle';
            if (emptyTitle) emptyTitle.textContent = '搜索失败';
            
            // 根据错误类型提供不同的提示
            let errorMessage = '搜索过程中遇到问题，请稍后重试';
            if (error && error.message) {
                if (error.message.includes('网络')) {
                    errorMessage = '网络连接失败，请检查网络状态后重试';
                } else if (error.message.includes('超时')) {
                    errorMessage = '搜索请求超时，请稍后重试';
                } else if (error.message.includes('未找到')) {
                    errorMessage = '未找到相关笔记，请尝试其他关键词';
                } else {
                    errorMessage = `搜索失败：${error.message}`;
                }
            }
            
            if (emptyText) emptyText.textContent = errorMessage;
        }
    }
    
    // ==================== 备用结果展示功能 ====================
    
    /**
     * 显示传统结果（备用方案）
     * @param {Array} notes - 笔记数组
     */
    function showTraditionalResults(notes) {
        // 显示结果区域
        resultSection.style.display = 'block';
        
        // 更新结果时间
        const now = new Date();
        resultTimeDiv.textContent = `${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
        
        // 清空之前的结果
        resultContainer.innerHTML = '';
        
        // 生成结果卡片
        notes.forEach(note => {
            const card = createNoteCard(note);
            resultContainer.appendChild(card);
        });
    }
    
    /**
     * 创建笔记卡片元素
     * @param {Object} note - 笔记数据
     * @returns {Element} - 卡片DOM元素
     */
    function createNoteCard(note) {
        const card = document.createElement('div');
        card.className = 'note-card';
        card.dataset.noteId = note.id || '';
        
        // 创建图片占位符URL
        const imageUrl = note.cover || generatePlaceholderImage(note.title || '小红书笔记');
        
        // 卡片HTML结构
        card.innerHTML = `
            <img src="${imageUrl}" alt="${note.title || ''}" class="note-image">
            <div class="note-content">
                <div class="note-title">${note.title || '无标题'}</div>
                <div class="note-description">${note.desc || '暂无描述'}</div>
                <div class="note-meta">
                    <div class="note-author">
                        <img src="${note.avatar || generatePlaceholderImage('U')}" alt="${note.author || ''}" class="author-avatar">
                        <span>${note.author || '匿名用户'}</span>
                    </div>
                    <div class="note-stats">
                        <div class="note-stat"><i class="fas fa-heart"></i> ${formatNumber(note.likes)}</div>
                        <div class="note-stat"><i class="fas fa-comment"></i> ${formatNumber(note.comments)}</div>
                    </div>
                </div>
            </div>
        `;
        
        // 添加点击事件
        card.addEventListener('click', () => openNoteDetail(note));
        
        return card;
    }
    
    // ==================== 笔记详情模态框 ====================
    
    /**
     * 打开笔记详情模态框
     * @param {Object} note - 笔记数据
     */
    function openNoteDetail(note) {
        // 创建图片占位符URL
        const coverImageUrl = note.cover || generatePlaceholderImage(note.title || '小红书笔记');
        
        // 格式化时间
        let publishedTime = '未知时间';
        if (note.published) {
            const date = new Date(note.published);
            publishedTime = isNaN(date) ? note.published : date.toLocaleDateString();
        }
        
        // 构建模态框内容
        modalBody.innerHTML = `
            <div class="modal-note-header">
                <h2 class="modal-note-title">${note.title || '无标题'}</h2>
                <div class="modal-note-author">
                    <img src="${note.avatar || generatePlaceholderImage('U')}" class="modal-author-avatar">
                    <div class="modal-author-info">
                        <div class="modal-author-name">${note.author || '匿名用户'}</div>
                        <div class="modal-author-date">${publishedTime}</div>
                    </div>
                </div>
            </div>
            
            <div class="modal-note-images">
                <img src="${coverImageUrl}" class="modal-note-image">
                ${generateAdditionalImages(note)}
            </div>
            
            <div class="modal-note-content">
                ${note.content || note.desc || '暂无内容'}
            </div>
            
            <div class="modal-note-stats">
                <div class="modal-note-stat"><i class="fas fa-heart"></i> ${formatNumber(note.likes)} 赞</div>
                <div class="modal-note-stat"><i class="fas fa-comment"></i> ${formatNumber(note.comments)} 评论</div>
                <div class="modal-note-stat"><i class="fas fa-star"></i> ${formatNumber(note.collects)} 收藏</div>
                <div class="modal-note-stat"><i class="fas fa-share"></i> ${formatNumber(note.shares)} 分享</div>
            </div>
        `;
        
        // 显示模态框
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
    
    /**
     * 关闭笔记详情模态框
     */
    function closeNoteDetail() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }
    
    // ==================== 工具函数 ====================
    
    /**
     * 生成占位图片URL
     * @param {string} text - 占位文字
     * @returns {string} - 占位图片URL
     */
    function generatePlaceholderImage(text) {
        return `https://via.placeholder.com/400x300/fe2c55/ffffff?text=${encodeURIComponent(text)}`;
    }
    
    /**
     * 生成额外的图片HTML
     * @param {Object} note - 笔记数据
     * @returns {string} - 图片HTML字符串
     */
    function generateAdditionalImages(note) {
        if (!note.images || !Array.isArray(note.images) || note.images.length === 0) {
            return '';
        }
        
        return note.images.map(img => {
            const imgUrl = img || generatePlaceholderImage('图片');
            return `<img src="${imgUrl}" class="modal-note-image">`;
        }).join('');
    }
    
    /**
     * 格式化数字显示
     * @param {number} num - 要格式化的数字
     * @returns {string} - 格式化后的字符串
     */
    function formatNumber(num) {
        if (num === undefined || num === null) return 0;
        
        num = Number(num);
        if (isNaN(num)) return 0;
        
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'm';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'k';
        } else {
            return num;
        }
    }
    
    // ==================== 事件监听器 ====================
    
    // 热门关键词点击
    keywordLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const keyword = this.getAttribute('data-keyword');
            searchInput.value = keyword;
            performSearch(keyword);
        });
    });
    
    // 品牌logo点击
    brandItems.forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault();
            const keyword = this.getAttribute('data-keyword');
            if (keyword) {
                searchInput.value = keyword;
                performSearch(keyword);
            }
        });
    });
    
    // 关闭模态框
    if (closeModal) {
        closeModal.addEventListener('click', closeNoteDetail);
    }
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeNoteDetail();
        }
    });
    
    // 按ESC键关闭模态框
    window.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && modal && modal.style.display === 'block') {
            closeNoteDetail();
        }
    });
    
    /**
     * 🆕 HTML状态轮询器
     * 定期查询HTML生成状态，一旦完成立即跳转
     * @param {string} statusUrl - HTML状态查询URL
     * @param {Object} fallbackData - 备用数据（用于失败时的传统显示）
     */
    async function startHtmlStatusPolling(statusUrl, fallbackData) {
        console.log('🎯 启动HTML状态轮询器...');
        console.log(`📊 状态URL: ${statusUrl}`);
        
        const maxAttempts = 30; // 最多30次 (30秒)
        const interval = 1000;  // 每1秒查询一次
        let attempts = 0;
        
        const pollStatus = async () => {
            attempts++;
            console.log(`🔍 状态轮询 #${attempts}/${maxAttempts}`);
            
            try {
                const response = await fetch(statusUrl);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const statusData = await response.json();
                console.log(`📊 状态响应:`, statusData);
                
                showLoadingProgress(`正在生成HTML页面... (${attempts}/${maxAttempts})`);
                
                if (statusData.status === 'ready' && statusData.html_api_url) {
                    // HTML准备就绪
                    console.log('✅ HTML页面生成完成，准备跳转:', statusData.html_api_url);
                    hideLoadingState();
                    window.open(statusData.html_api_url, '_blank');
                    window.location.href = statusData.html_api_url;
                    return;
                } else if (statusData.status === 'error') {
                    // HTML生成出错
                    console.log('❌ HTML页面生成出错:', statusData.message);
                    hideLoadingState();
                    handleFallbackDisplay(fallbackData, fallbackData.notes && fallbackData.notes.length > 0);
                    return;
                } else {
                    // 继续等待
                    console.log(`⏳ HTML页面生成中: ${statusData.message}`);
                }
                
            } catch (error) {
                console.error(`❌ 状态查询出错 (尝试 #${attempts}):`, error);
            }
            
            // 检查是否超时
            if (attempts >= maxAttempts) {
                console.log('⏰ HTML状态轮询超时');
                hideLoadingState();
                handleFallbackDisplay(fallbackData, fallbackData.notes && fallbackData.notes.length > 0);
                return;
            }
            
            // 安排下一次查询
            setTimeout(pollStatus, interval);
        };
        
        // 开始第一次查询
        pollStatus();
    }
    
}); 