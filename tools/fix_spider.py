import asyncio
import os
import requests
from playwright.async_api import async_playwright
from urllib.parse import urljoin

# --- 配置 ---
BASE_URL = "https://zsbcworld.com"
OUTPUT_DIR = "zsbc_final_site"

# 确保基础目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def download_file(url, local_folder):
    """通用下载函数，支持自动补全路径"""
    try:
        if not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        # 提取文件名并清理参数
        filename = url.split('/')[-1].split('?')[0]
        if not filename or "." not in filename: 
            return
        
        target_path = os.path.join(OUTPUT_DIR, local_folder, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # 避免重复下载
        if os.path.exists(target_path):
            return

        r = requests.get(url, stream=True, timeout=15)
        if r.status_code == 200:
            with open(target_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ 已提取资源: {local_folder}/{filename}")
    except Exception as e:
        pass # 静默处理错误以保持抓取流

async def run_fix():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 1. 拦截动态加载的资源
        async def intercept_assets(response):
            url = response.url
            if any(ext in url.lower() for ext in [".png", ".jpg", ".svg", ".ico", ".webp"]):
                await download_file(url, "assets/images")
            elif any(ext in url.lower() for ext in [".glb", ".gltf"]):
                await download_file(url, "assets/models")
            elif ".js" in url.lower() and "assets" in url:
                await download_file(url, "assets/js")
            elif ".css" in url.lower() and "assets" in url:
                await download_file(url, "assets/css")

        page.on("response", intercept_assets)

        print(f"🔗 正在同步站点资源: {BASE_URL}")
        await page.goto(BASE_URL, wait_until="networkidle")

        # 2. 针对你提供的 HTML 进行深度提取
        # 包含 Logo 和关键 JS/CSS 路径
        hardcoded_assets = [
            "/assets/zsbc_icon-CbfQQK20.png",
            "/assets/index-DwzMRaeZ.js",
            "/assets/index-BNetWitS.css",
            "https://app.zsbcworld.com/public/upload/zsbc_logo.png"
        ]
        
        print("🎯 正在提取关键 Logo 和前端入口文件...")
        for asset_url in hardcoded_assets:
            # 根据后缀决定存放文件夹
            folder = "assets/js" if ".js" in asset_url else "assets/css" if ".css" in asset_url else "assets/images"
            await download_file(asset_url, folder)

        # 3. 保存一份渲染后的 index.html 到本地
        content = await page.content()
        with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\n✨ 任务完成！")
        print(f"📁 复刻文件存放于: {os.path.abspath(OUTPUT_DIR)}")
        print("💡 接下来，你只需在 VSCode 中右键 index.html 点击 'Open with Live Server' 即可。")
        
        await asyncio.sleep(5) # 留一点时间缓冲
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_fix())