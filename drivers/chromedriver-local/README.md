# 本地ChromeDriver

## 📋 版本信息
- **ChromeDriver版本**: 138.0.7204.49
- **Chrome版本**: 138.0.7204.49
- **平台**: Mac ARM64 (Apple M2)
- **下载时间**: 2025-06-26

## 📁 文件结构
```
chromedriver-local/
├── chromedriver-mac-arm64/
│   ├── chromedriver           # 可执行文件
│   ├── LICENSE.chromedriver
│   └── THIRD_PARTY_NOTICES.chromedriver
├── chromedriver-mac-arm64.zip # 原始下载文件
└── README.md                  # 本文件
```

## 🎯 配置说明

应用已配置为优先使用此本地ChromeDriver：

```python
'CHROMEDRIVER_PATH': os.path.join(DIRECTORIES['DRIVERS_DIR'], 'chromedriver-local', 'chromedriver-mac-arm64', 'chromedriver')
```

## ✅ 优势
1. **无需重复下载** - 避免每次启动应用时重新下载
2. **版本稳定** - 固定版本避免兼容性问题  
3. **启动加速** - 跳过下载时间，快速启动
4. **离线可用** - 不依赖网络连接

## 🔄 更新说明

当Chrome浏览器更新时，请：
1. 检查新的Chrome版本号
2. 下载对应版本的ChromeDriver
3. 替换当前的chromedriver文件
4. 更新此README中的版本信息

## 🌐 下载来源
- 官方下载地址: https://storage.googleapis.com/chrome-for-testing-public/
- 当前版本链接: https://storage.googleapis.com/chrome-for-testing-public/138.0.7204.49/mac-arm64/chromedriver-mac-arm64.zip 