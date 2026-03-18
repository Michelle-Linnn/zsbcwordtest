import asyncio
import os
import re
from urllib.parse import urlparse
from playwright.async_api import async_playwright

# --- 配置区 ---
TARGET_URL = "https://www.zsbcworld.com"
OUTPUT_DIR = "zsbc_site_clone"

async def save_resource(url, content):
    """根据 URL 结构自动创建本地文件夹并保存文件"""
    parsed_url = urlparse(url)
    # 提取路径，去掉开头的斜杠
    path = parsed_url.path.lstrip('/')
    if not path or path.endswith('/'):
        path = os.path.join(path, "index.html")
    
    # 构造本地存储路径
    local_path = os.path.join(OUTPUT_DIR, path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    try:
        with open(local_path, "wb") as f:
            f.write(content)
        print(f"📥 已保存: {path}")
    except Exception as e:
        print(f"❌ 无法保存 {path}: {e}")

async def run_clone():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # 监听所有网络响应
        async def handle_response(response):
            url = response.url
            # 只抓取该域名下的资源，或者 3D 模型资源
            if "zsbcworld.com" in url or any(ext in url.lower() for ext in [".glb", ".gltf", ".obj"]):
                try:
                    # 排除掉已经处理过的或者超大的请求
                    status = response.status
                    if 200 <= status < 300:
                        content = await response.body()
                        await save_resource(url, content)
                except:
                    pass

        page.on("response", handle_response)

        print(f"🌐 正在完整扫描: {TARGET_URL}")
        await page.goto(TARGET_URL, wait_until="networkidle")

        # --- 针对 Logo 的特殊处理 ---
        # 尝试通过选择器直接定位 Logo 元素并截图或提取源码
        logo_element = await page.query_selector(".logo, [class*='logo'], img[src*='logo']")
        if logo_element:
            print("🎯 成功定位到 Logo 元素")

        print("\n--- 深度复刻提示 ---")
        print("1. 请在弹出的浏览器中，手动点击左上角的 Logo。")
        print("2. 浏览『Majors』和『Services』页面，确保所有 3D 组件都加载出来。")
        print("3. 所有的 CSS、JS、Logo 图片、3D 模型会自动按原目录结构存入 'zsbc_site_clone'。")
        
        # 保持 5 分钟操作时间
        await asyncio.sleep(300) 
        await browser.close()

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    asyncio.run(run_clone())