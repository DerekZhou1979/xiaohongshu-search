# 小红书搜索工具 - 配置说明

本目录包含小红书搜索工具的全局配置文件，用于统一管理所有应用设置。

## 配置文件结构

### config.py - 主配置文件

包含所有应用配置参数，分为以下几个部分：

#### 1. 基础配置 (APP_CONFIG)
- `DEBUG`: 调试模式开关
- `HOST`: 服务器监听地址
- `PORT`: 服务器端口
- `SECRET_KEY`: 应用密钥

#### 2. 搜索配置 (SEARCH_CONFIG)
- `DEFAULT_MAX_RESULTS`: 默认搜索结果数量 (21篇)
- `MAX_RESULTS_LIMIT`: 最大搜索结果数量
- `USE_CACHE`: 是否启用缓存
- `CACHE_EXPIRE_TIME`: 缓存过期时间（秒）
- `REQUEST_DELAY`: 请求间隔
- `PAGE_LOAD_TIMEOUT`: 页面加载超时
- `MAX_RETRIES`: 最大重试次数
- `RETRY_DELAY`: 重试间隔

#### 3. 爬虫配置 (CRAWLER_CONFIG)
- `USE_SELENIUM`: 是否使用Selenium
- `HEADLESS`: 是否使用无头模式
- `WINDOW_SIZE`: 浏览器窗口大小
- `CHROME_OPTIONS`: Chrome浏览器选项列表
- `SCROLL_PAUSE_TIME`: 滚动停顿时间
- `SCROLL_COUNT`: 滚动次数
- `ELEMENT_WAIT_TIME`: 元素等待时间

#### 4. 三种提取策略配置 (EXTRACTION_STRATEGIES)

**策略1: CSS选择器方法**
- `NAME`: 策略名称
- `ENABLED`: 是否启用
- `PRIORITY`: 优先级
- `SELECTORS`: CSS选择器列表
- `MAX_ELEMENTS_PER_SELECTOR`: 每个选择器最大处理元素数

**策略2: URL模式匹配方法**
- `URL_PATTERNS`: URL匹配模式列表
- `MAX_LINKS_TO_PROCESS`: 最大处理链接数

**策略3: DOM结构分析方法**
- `XPATH_QUERIES`: XPath查询模板列表
- `MAX_ELEMENTS_TO_ANALYZE`: 最大分析元素数
- `PARENT_LEVEL_DEPTH`: 向上查找父元素的深度

#### 5. 目录配置 (DIRECTORIES)
- `CACHE_DIR`: 缓存目录
- `TEMP_DIR`: 临时文件目录
- `LOGS_DIR`: 日志目录
- `COOKIES_DIR`: Cookie存储目录
- `STATIC_DIR`: 静态文件目录
- `DRIVERS_DIR`: WebDriver目录

#### 6. 文件路径配置 (FILE_PATHS)
- `CHROMEDRIVER_PATH`: ChromeDriver可执行文件路径
- `COOKIES_FILE`: Cookie文件路径
- `STARTUP_LOG`: 启动日志文件路径
- `CRAWLER_LOG`: 爬虫日志文件路径

#### 7. 日志配置 (LOGGING_CONFIG)
- `LEVEL`: 日志级别
- `FORMAT`: 日志格式
- `DATE_FORMAT`: 时间格式
- `MAX_FILE_SIZE`: 最大文件大小
- `BACKUP_COUNT`: 备份文件数量
- `ENCODING`: 文件编码

#### 8. URL配置 (URLS)
- `XIAOHONGSHU_BASE`: 小红书基础URL
- `SEARCH_URL_TEMPLATE`: 搜索URL模板
- `LOGIN_URL`: 登录页面URL
- `API_BASE`: API基础路径

#### 9. 其他配置
- `SECURITY_CONFIG`: 安全相关配置
- `MOCK_DATA_CONFIG`: 模拟数据配置
- `HOT_KEYWORDS`: 热门关键词列表
- `ERROR_CONFIG`: 错误处理配置
- `PERFORMANCE_CONFIG`: 性能配置

## 如何使用配置

### 1. 在代码中导入配置

```python
from config.config import (
    SEARCH_CONFIG, CRAWLER_CONFIG, EXTRACTION_STRATEGIES,
    DIRECTORIES, FILE_PATHS, URLS,
    get_config
)

# 获取特定配置
search_config = get_config('SEARCH')
crawler_config = get_config('CRAWLER')

# 获取所有配置
all_config = get_config()
```

### 2. 修改配置

直接编辑 `config.py` 文件中的对应配置项。

### 3. 验证配置

```bash
python3 config/config.py
```

这将验证配置的有效性并显示主要配置信息。

### 4. 创建目录

配置文件提供了自动创建必要目录的功能：

```python
from config.config import create_directories
create_directories()
```

## 配置优化建议

### 1. 性能优化
- 根据实际需要调整 `DEFAULT_MAX_RESULTS`（默认21篇）
- 调整 `SCROLL_COUNT` 和 `SCROLL_PAUSE_TIME` 以平衡速度和成功率
- 适当设置 `REQUEST_DELAY` 避免被限流

### 2. 策略优化
- 可以根据实际效果启用/禁用特定策略
- 调整各策略的 `MAX_ELEMENTS` 参数
- 根据网站变化更新CSS选择器和URL模式

### 3. 稳定性优化
- 增加 `MAX_RETRIES` 和 `RETRY_DELAY` 提高稳定性
- 调整 `PAGE_LOAD_TIMEOUT` 适应网络状况
- 启用错误截图和日志保存

## 常见问题

### Q: 如何修改默认搜索结果数量？
A: 修改 `SEARCH_CONFIG['DEFAULT_MAX_RESULTS']` 的值。

### Q: 如何添加新的CSS选择器？
A: 在 `EXTRACTION_STRATEGIES['STRATEGY_1']['SELECTORS']` 列表中添加新的选择器。

### Q: 如何禁用某个提取策略？
A: 将对应策略的 `ENABLED` 设置为 `False`。

### Q: 如何修改Chrome浏览器选项？
A: 在 `CRAWLER_CONFIG['CHROME_OPTIONS']` 列表中添加或修改选项。

### Q: 配置验证失败怎么办？
A: 检查错误提示，确保必要的目录存在且ChromeDriver路径正确。

## 版本说明

- 当前版本支持三种提取策略
- 默认搜索结果数量已调整为21篇
- 所有调试信息已优化为正式代码
- 支持完整的配置验证和目录创建

## 注意事项

1. 修改配置后需要重启应用
2. ChromeDriver路径必须正确且可执行
3. 确保有足够的磁盘空间用于缓存和日志
4. 某些Chrome选项可能影响兼容性，请谨慎修改 