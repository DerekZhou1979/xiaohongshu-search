/**
 * 小红书笔记详情页面交互脚本
 */

class NoteDetailViewer {
    constructor() {
        this.currentNoteData = null;
        this.currentImageIndex = 0;
        this.images = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadNoteDetail();
    }

    bindEvents() {
        // 图片预览模态框事件
        document.getElementById('prev-image').onclick = () => this.showPreviousImage();
        document.getElementById('next-image').onclick = () => this.showNextImage();
        
        // 键盘事件
        document.addEventListener('keydown', (e) => {
            if (document.getElementById('image-modal').style.display !== 'none') {
                if (e.key === 'ArrowLeft') this.showPreviousImage();
                if (e.key === 'ArrowRight') this.showNextImage();
                if (e.key === 'Escape') this.closeImageModal();
            }
        });

        // 互动按钮事件
        this.bindInteractionEvents();
    }

    bindInteractionEvents() {
        const actionBtns = document.querySelectorAll('.action-btn');
        actionBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = btn.classList.contains('like-btn') ? 'like' :
                              btn.classList.contains('collect-btn') ? 'collect' :
                              btn.classList.contains('comment-btn') ? 'comment' :
                              btn.classList.contains('share-btn') ? 'share' : '';
                
                this.handleInteraction(action, btn);
            });
        });
    }

    handleInteraction(action, btn) {
        switch(action) {
            case 'like':
                this.toggleLike(btn);
                break;
            case 'collect':
                this.toggleCollect(btn);
                break;
            case 'comment':
                this.showComments();
                break;
            case 'share':
                this.shareNote();
                break;
        }
    }

    toggleLike(btn) {
        const isLiked = btn.classList.contains('active');
        const likeCountEl = document.getElementById('like-count');
        const currentCount = parseInt(likeCountEl.textContent) || 0;
        
        if (isLiked) {
            btn.classList.remove('active');
            btn.innerHTML = '<i class="far fa-heart"></i>点赞';
            likeCountEl.textContent = Math.max(0, currentCount - 1);
        } else {
            btn.classList.add('active');
            btn.innerHTML = '<i class="fas fa-heart"></i>已赞';
            likeCountEl.textContent = currentCount + 1;
        }
        
        this.animateButton(btn);
    }

    toggleCollect(btn) {
        const isCollected = btn.classList.contains('active');
        const collectCountEl = document.getElementById('collect-count');
        const currentCount = parseInt(collectCountEl.textContent) || 0;
        
        if (isCollected) {
            btn.classList.remove('active');
            btn.innerHTML = '<i class="far fa-bookmark"></i>收藏';
            collectCountEl.textContent = Math.max(0, currentCount - 1);
        } else {
            btn.classList.add('active');
            btn.innerHTML = '<i class="fas fa-bookmark"></i>已藏';
            collectCountEl.textContent = currentCount + 1;
        }
        
        this.animateButton(btn);
    }

    animateButton(btn) {
        btn.style.transform = 'scale(0.95)';
        setTimeout(() => {
            btn.style.transform = 'scale(1)';
        }, 150);
    }

    showComments() {
        alert('评论功能开发中...');
    }

    shareNote() {
        if (navigator.share && this.currentNoteData) {
            navigator.share({
                title: this.currentNoteData.title || '小红书笔记',
                text: this.currentNoteData.content || '',
                url: window.location.href
            }).catch(err => {
                console.log('分享失败:', err);
                this.copyToClipboard();
            });
        } else {
            this.copyToClipboard();
        }
    }

    copyToClipboard() {
        const url = window.location.href;
        navigator.clipboard.writeText(url).then(() => {
            this.showToast('链接已复制到剪贴板');
        }).catch(() => {
            this.showToast('复制失败，请手动复制链接');
        });
    }

    showToast(message) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            z-index: 2000;
            font-size: 14px;
        `;
        
        document.body.appendChild(toast);
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 2000);
    }

    async loadNoteDetail() {
        try {
            // 从URL参数获取文件路径
            const urlParams = new URLSearchParams(window.location.search);
            const filePath = urlParams.get('file');
            
            if (!filePath) {
                throw new Error('未指定笔记文件');
            }

            this.showLoading();
            
            // 加载JSON数据
            const response = await fetch(`/api/note-data?file=${encodeURIComponent(filePath)}`);
            
            if (!response.ok) {
                throw new Error(`加载失败：${response.status} ${response.statusText}`);
            }
            
            const noteData = await response.json();
            this.currentNoteData = noteData;
            
            this.renderNoteContent(noteData);
            this.showContent();
            
        } catch (error) {
            console.error('加载笔记详情失败:', error);
            this.showError(error.message);
        }
    }

    showLoading() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('error').style.display = 'none';
        document.getElementById('note-content').style.display = 'none';
    }

    showError(message) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('note-content').style.display = 'none';
        document.getElementById('error-message').textContent = message;
    }

    showContent() {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'none';
        document.getElementById('note-content').style.display = 'block';
    }

    renderNoteContent(data) {
        // 渲染标题
        this.renderTitle(data);
        
        // 渲染作者信息
        this.renderAuthor(data);
        
        // 渲染笔记内容
        this.renderContent(data);
        
        // 渲染标签
        this.renderTags(data);
        
        // 渲染图片
        this.renderImages(data);
        
        // 渲染互动数据
        this.renderInteractionStats(data);
        
        // 渲染提取信息
        this.renderExtractionInfo(data);
        
        // 渲染原始数据
        this.renderRawData(data);
    }

    renderTitle(data) {
        const titleEl = document.getElementById('note-title');
        const noteIdEl = document.getElementById('note-id');
        
        titleEl.textContent = data.title || '无标题';
        
        if (data.note_id) {
            noteIdEl.textContent = `ID: ${data.note_id}`;
            noteIdEl.style.display = 'inline-block';
        } else {
            noteIdEl.style.display = 'none';
        }
        
        // 更新页面标题
        document.title = `${data.title || '小红书笔记'} - 笔记详情`;
    }

    renderAuthor(data) {
        const authorNameEl = document.getElementById('author-name');
        const userIdEl = document.getElementById('user-id');
        
        authorNameEl.textContent = data.author_name || '未知作者';
        
        if (data.user_id) {
            userIdEl.textContent = `用户ID: ${data.user_id}`;
            userIdEl.style.display = 'inline-block';
        } else {
            userIdEl.style.display = 'none';
        }
    }

    renderContent(data) {
        const contentEl = document.getElementById('note-text');
        contentEl.textContent = data.content || '暂无内容';
    }

    renderTags(data) {
        const tagsEl = document.getElementById('note-tags');
        tagsEl.innerHTML = '';
        
        if (data.tags && data.tags.length > 0) {
            data.tags.forEach(tag => {
                const tagEl = document.createElement('span');
                tagEl.className = 'tag';
                tagEl.textContent = tag.startsWith('#') ? tag : `#${tag}`;
                tagsEl.appendChild(tagEl);
            });
            tagsEl.style.display = 'flex';
        } else {
            tagsEl.style.display = 'none';
        }
    }

    renderImages(data) {
        const imagesEl = document.getElementById('note-images');
        imagesEl.innerHTML = '';
        
        // 合并不同来源的图片
        this.images = [];
        if (data.images && data.images.length > 0) {
            this.images = [...this.images, ...data.images];
        }
        if (data.image_urls && data.image_urls.length > 0) {
            this.images = [...this.images, ...data.image_urls];
        }
        
        // 去重
        this.images = [...new Set(this.images)];
        
        if (this.images.length > 0) {
            // 设置网格样式
            if (this.images.length === 1) {
                imagesEl.className = 'note-images single';
            } else if (this.images.length === 2) {
                imagesEl.className = 'note-images double';
            } else {
                imagesEl.className = 'note-images multiple';
            }
            
            this.images.forEach((imageUrl, index) => {
                const imageContainer = document.createElement('div');
                imageContainer.className = 'note-image';
                imageContainer.onclick = () => this.openImageModal(index);
                
                const img = document.createElement('img');
                img.src = imageUrl;
                img.alt = `笔记图片 ${index + 1}`;
                img.onerror = () => {
                    imageContainer.style.display = 'none';
                };
                
                const overlay = document.createElement('div');
                overlay.className = 'image-overlay';
                overlay.innerHTML = `
                    <div class="image-info">
                        图片 ${index + 1} / ${this.images.length}
                    </div>
                `;
                
                imageContainer.appendChild(img);
                imageContainer.appendChild(overlay);
                imagesEl.appendChild(imageContainer);
            });
            
            imagesEl.style.display = 'grid';
        } else {
            imagesEl.style.display = 'none';
        }
    }

    renderInteractionStats(data) {
        document.getElementById('like-count').textContent = data.like_count || 0;
        document.getElementById('collect-count').textContent = data.collect_count || 0;
        document.getElementById('comment-count').textContent = data.comment_count || 0;
    }

    renderExtractionInfo(data) {
        const extractionInfo = data.extraction_info || {};
        
        document.getElementById('extracted-at').textContent = 
            extractionInfo.extracted_at ? 
            new Date(extractionInfo.extracted_at).toLocaleString('zh-CN') : '-';
            
        document.getElementById('extractor-version').textContent = 
            extractionInfo.extractor_version || '-';
            
        document.getElementById('fields-count').textContent = 
            extractionInfo.fields_count || '-';
            
        document.getElementById('source-file').textContent = 
            extractionInfo.source_file ? 
            extractionInfo.source_file.split('/').pop() : '-';
    }

    renderRawData(data) {
        const rawJsonEl = document.getElementById('raw-json');
        rawJsonEl.textContent = JSON.stringify(data, null, 2);
    }

    openImageModal(index) {
        if (this.images.length === 0) return;
        
        this.currentImageIndex = index;
        const modal = document.getElementById('image-modal');
        const modalImage = document.getElementById('modal-image');
        const currentImageEl = document.getElementById('current-image');
        const totalImagesEl = document.getElementById('total-images');
        
        modalImage.src = this.images[index];
        currentImageEl.textContent = index + 1;
        totalImagesEl.textContent = this.images.length;
        
        modal.style.display = 'flex';
        
        // 隐藏/显示导航按钮
        const prevBtn = document.getElementById('prev-image');
        const nextBtn = document.getElementById('next-image');
        
        prevBtn.style.display = this.images.length > 1 ? 'block' : 'none';
        nextBtn.style.display = this.images.length > 1 ? 'block' : 'none';
    }

    closeImageModal() {
        document.getElementById('image-modal').style.display = 'none';
    }

    showPreviousImage() {
        if (this.images.length <= 1) return;
        
        this.currentImageIndex = (this.currentImageIndex - 1 + this.images.length) % this.images.length;
        this.updateModalImage();
    }

    showNextImage() {
        if (this.images.length <= 1) return;
        
        this.currentImageIndex = (this.currentImageIndex + 1) % this.images.length;
        this.updateModalImage();
    }

    updateModalImage() {
        const modalImage = document.getElementById('modal-image');
        const currentImageEl = document.getElementById('current-image');
        
        modalImage.src = this.images[this.currentImageIndex];
        currentImageEl.textContent = this.currentImageIndex + 1;
    }
}

// 全局函数
function toggleRawData() {
    const rawDataContent = document.getElementById('raw-data');
    const toggleBtn = document.querySelector('.toggle-btn i');
    
    if (rawDataContent.style.display === 'none') {
        rawDataContent.style.display = 'block';
        toggleBtn.className = 'fas fa-chevron-up';
    } else {
        rawDataContent.style.display = 'none';
        toggleBtn.className = 'fas fa-chevron-down';
    }
}

function closeImageModal() {
    window.noteViewer.closeImageModal();
}

function loadNoteDetail() {
    window.noteViewer.loadNoteDetail();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.noteViewer = new NoteDetailViewer();
}); 