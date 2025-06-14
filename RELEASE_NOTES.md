# 版本发布说明 (Release Notes)

## v1.0.0 (2024-12-20) - 首个正式版本 🎉

### ✨ 新功能

#### 🔍 智能搜索系统
- **关键词搜索**：支持任意关键词搜索小红书笔记
- **智能排序**：按评论数降序 + 收藏数降序自动排列
- **批量提取**：一次性获取30-100条笔记信息
- **唯一Token**：为每个笔记生成独特的xsec_token

#### 🌐 双重访问方式
- **直接访问**：自动设置cookies并使用增强URL访问
- **代理访问**：通过代理服务器访问，解决网络限制问题
- **自动认证**：两种方式都已自动处理登录认证

#### 📊 数据展示界面
- **美观界面**：现代化的卡片式布局
- **详细信息**：显示标题、描述、作者、互动数据
- **实时更新**：支持缓存和实时搜索切换
- **响应式设计**：支持桌面和移动设备

#### 🛠️ 技术特性
- **反爬虫处理**：智能绕过检测机制
- **缓存系统**：提高搜索效率，减少重复请求
- **错误处理**：完善的异常处理和日志记录
- **配置管理**：灵活的配置文件支持

### 🏗️ 技术架构

#### 后端技术栈
- **Flask 3.0.0**：轻量级Web框架
- **Selenium 4.15.2**：浏览器自动化
- **Requests 2.31.0**：HTTP请求库
- **BeautifulSoup4 4.12.2**：HTML解析
- **LXML 4.9.3**：XML/HTML处理

#### 前端技术栈
- **HTML5/CSS3**：现代化界面设计
- **JavaScript ES6+**：交互逻辑实现
- **Bootstrap风格**：响应式组件

#### 部署方案
- **传统部署**：Python直接运行
- **Docker容器**：完整的容器化解决方案
- **Docker Compose**：多服务编排
- **GitHub Actions**：自动化CI/CD

### 📦 安装方式

#### 从源码安装
```bash
git clone https://github.com/DerekZhou1979/xiaohongshu-search.git
cd xiaohongshu-search
pip install -r requirements.txt
python app.py
```

#### 包管理器安装
```bash
# 直接从GitHub安装
pip install git+https://github.com/DerekZhou1979/xiaohongshu-search.git

# 开发模式安装
pip install -e .
```

#### Docker部署
```bash
# 使用Docker Compose
docker-compose up -d

# 或直接使用Docker
docker run -d -p 8080:8080 ghcr.io/derekzhou1979/xiaohongshu-search:latest
```

### 🔧 配置选项

#### 应用配置
- **端口设置**：默认8080，可在config中修改
- **调试模式**：生产环境建议关闭
- **秘钥管理**：Flask应用秘钥配置

#### 搜索配置
- **结果数量**：默认30条，最大100条
- **缓存策略**：默认3600秒过期
- **请求延迟**：默认0.5秒间隔
- **重试机制**：最大3次重试

#### 爬虫配置
- **浏览器设置**：Chrome headless模式
- **窗口大小**：1920x1080分辨率
- **用户代理**：模拟真实浏览器
- **反检测**：多种反爬虫策略

### 📈 性能指标

- **搜索速度**：平均10-30秒完成一次搜索
- **成功率**：正常网络环境下>95%
- **并发支持**：支持多用户同时使用
- **内存占用**：约200-500MB（含Chrome）
- **存储空间**：基础安装约100MB

### 🔒 安全特性

- **数据隐私**：不存储用户个人信息
- **网络安全**：HTTPS请求，安全cookie处理
- **权限控制**：Docker非root用户运行
- **日志管理**：敏感信息过滤

### 🐛 已知问题与限制

- **网络依赖**：需要稳定的网络连接
- **浏览器要求**：需要Chrome浏览器支持
- **频率限制**：建议避免过于频繁的请求
- **内容动态**：小红书页面结构变化可能影响提取效果

### 🚀 未来计划

#### v1.1.0 预期功能
- [ ] 用户登录功能
- [ ] 更多排序选项
- [ ] 数据导出功能
- [ ] API接口文档

#### v1.2.0 预期功能
- [ ] 多平台支持（其他社交媒体）
- [ ] 数据分析功能
- [ ] 定时任务支持
- [ ] Web管理界面

### 🙏 致谢

感谢所有测试用户的反馈和建议，感谢开源社区的技术支持。

### 📞 支持与反馈

- **问题报告**：[GitHub Issues](https://github.com/DerekZhou1979/xiaohongshu-search/issues)
- **功能建议**：[GitHub Discussions](https://github.com/DerekZhou1979/xiaohongshu-search/discussions)
- **邮件联系**：derekzhou1979@gmail.com

---

**重要提醒**：本工具仅供学习研究使用，请遵守相关法律法规和平台服务条款。 