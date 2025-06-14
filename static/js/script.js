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
    
    // ==================== 初始化设置 ====================
    
    // Logo图片加载失败时的占位图
    const logoImg = document.getElementById('logo-img');
    if (logoImg) {
        logoImg.onerror = function() {
            this.src = 'data:image/svg+xml;charset=UTF-8,%3Csvg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"%3E%3Crect width="40" height="40" fill="%23fe2c55"%3E%3C/rect%3E%3Ctext x="50%25" y="50%25" font-size="20" text-anchor="middle" alignment-baseline="middle" font-family="Arial" fill="white"%3ER%3C/text%3E%3C/svg%3E';
        };
    }
    
    // ==================== 核心搜索功能 ====================
    
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
        
        // 执行搜索并处理结果
        getRedBookNotes(keyword)
            .then(handleSearchSuccess)
            .catch(handleSearchError);
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
        // 隐藏加载状态
        loadingSection.style.display = 'none';
        
        // 检查是否有结果和HTML页面URL
        if (data && data.notes && data.notes.length > 0 && (data.html_api_url || data.html_url)) {
            // 优先使用API形式的HTML URL，避免文件路径问题
            const htmlUrl = data.html_api_url || data.html_url;
            window.location.href = htmlUrl;
        } else if (data && data.notes && data.notes.length > 0) {
            // 如果没有HTML URL，使用传统方式显示结果（备用方案）
            showTraditionalResults(data.notes);
        } else {
            // 显示空结果提示
            emptyResult.style.display = 'block';
        }
    }
    
    /**
     * 处理搜索错误
     * @param {Error} error - 错误对象
     */
    function handleSearchError(error) {
        console.error('搜索出错:', error);
        loadingSection.style.display = 'none';
        emptyResult.style.display = 'block';
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
    
    // 搜索按钮点击
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            performSearch(searchInput.value);
        });
    }
    
    // 输入框回车键
    if (searchInput) {
        searchInput.addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                performSearch(searchInput.value);
            }
        });
    }
    
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
    
}); 