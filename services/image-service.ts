/**
 * 图片服务 - 统一处理图片路径
 * 确保在开发和生产环境中都能正确访问图片
 */

/**
 * 获取图片的完整URL
 * @param imagePath 相对图片路径，如 'seagull_logo.png' 或 'payment/alipay-qr.png'
 * @returns 完整的图片URL
 */
export function getImageUrl(imagePath: string): string {
  // 移除开头的斜杠或images/前缀，统一格式
  const cleanPath = imagePath.replace(/^(\/)?images\//, '');
  
  // 获取base路径，兼容不同环境
  const baseUrl = getBaseUrl();
  return `${baseUrl}images/${cleanPath}`;
}

/**
 * 获取基础URL路径
 * @returns 基础URL路径
 */
function getBaseUrl(): string {
  // 尝试从不同来源获取基础路径
  if (typeof window !== 'undefined') {
    // 浏览器环境
    const base = document.querySelector('base')?.getAttribute('href');
    if (base) return base;
    
    // 从当前路径推断
    const pathname = window.location.pathname;
    const segments = pathname.split('/').filter(Boolean);
    
    // 如果是GitHub Pages或其他子路径部署
    if (segments.length > 0 && segments[0] !== 'index.html') {
      return `/${segments[0]}/`;
    }
  }
  
  // 默认返回根路径
  return '/';
}

/**
 * 获取支付二维码图片URL
 * @param paymentType 支付类型：'alipay' | 'wechat'
 * @returns 支付二维码图片URL
 */
export function getPaymentQRUrl(paymentType: 'alipay' | 'wechat'): string {
  const qrImageMap = {
    alipay: 'payment/alipay-qr.png',
    wechat: 'payment/wechat-qr.png'
  };
  
  return getImageUrl(qrImageMap[paymentType]);
}

/**
 * 获取产品图片URL数组
 * @param imagePaths 图片路径数组
 * @returns 完整URL数组
 */
export function getProductImageUrls(imagePaths: string[]): string[] {
  return imagePaths.map(path => getImageUrl(path));
}

/**
 * 预加载图片
 * @param imageUrl 图片URL
 * @returns Promise<boolean> 是否加载成功
 */
export function preloadImage(imageUrl: string): Promise<boolean> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(true);
    img.onerror = () => resolve(false);
    img.src = imageUrl;
  });
}

/**
 * 批量预加载图片
 * @param imageUrls 图片URL数组
 * @returns Promise<boolean[]> 每个图片的加载结果
 */
export async function preloadImages(imageUrls: string[]): Promise<boolean[]> {
  const promises = imageUrls.map(url => preloadImage(url));
  return Promise.all(promises);
} 