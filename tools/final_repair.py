import asyncio
import os
import requests
from playwright.async_api import async_playwright
from urllib.parse import urljoin
import re

# --- 配置 ---
BASE_URL = "https://zsbcworld.com"
OUTPUT_DIR = "zsbc_fixed_project"
os.makedirs(OUTPUT_DIR, exist_ok=True)

async def download_file(url):
    """下载并返回本地相对路径"""
    if not url.startswith('http'):
        url = urljoin(BASE_URL, url)
    
    # 确定文件名和本地文件夹
    filename = url.split('/')[-1].split('?')[0]
    if not filename or "." not in filename: return None
    
    ext = os.path.splitext(filename)[1].lower()
    folder = "js" if ext == ".js" else "css" if ext == ".css" else "images"
    
    local_sub_path = os.path.join("assets", folder, filename)
    local_full_path = os.path.join(OUTPUT_DIR, local_sub_path)
    os.makedirs(os.path.dirname(local_full_path), exist_ok=True)

    if not os.path.exists(local_full_path):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(local_full_path, 'wb') as f:
                    f.write(r.content)
                print(f"📥 已下载: {local_sub_path}")
        except: return None
    
    return local_sub_path

async def run_final_repair():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print(f"🔗 正在抓取并修复站点...")
        await page.goto(BASE_URL, wait_until="networkidle")

        # 1. 获取渲染后的完整 HTML
        html_content = await page.content()

        # 2. 提取并下载所有资源 (Logo, CSS, JS)
        # 寻找所有 href 和 src
        links = re.findall(r'(?:href|src)=["\'](/assets/.*?)["\']', html_content)
        # 额外加上 Logo 的特殊路径
        links.append("https://app.zsbcworld.com/public/upload/zsbc_logo.png")
        links.append("/assets/zsbc_icon-CbfQQK20.png")

        for link in set(links):
            local_path = await download_file(link)
            if local_path:
                # 3. 关键一步：将 HTML 里的路径替换为本地相对路径
                html_content = html_content.replace(link, local_path)

        # 4. 修复图标和 CSS 路径
        html_content = html_content.replace('href="/assets/', 'href="assets/')
        html_content = html_content.replace('src="/assets/', 'src="assets/')

        # 保存修复后的 HTML
        with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"\n✅ 修复完成！请进入 {OUTPUT_DIR} 文件夹。")
        print("👉 找到 index.html，右键选择 'Open with Live Server' (如果你装了该插件)")
        print("👉 或者直接双击 index.html 看看效果。")
        
        await browser.close()

if __name__ == "__main__":
    # 先确保安装了依赖
    # os.system("/usr/local/bin/python3 -m pip install requests")
    asyncio.run(run_final_repair())