#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""截取论文工作台和Agent流水线截图"""

from playwright.sync_api import sync_playwright
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'screenshots')
os.makedirs(OUT, exist_ok=True)
FRONTEND = 'http://localhost:5179'
BACKEND = 'http://localhost:8005'

def shot(page, name, wait='networkidle'):
    page.wait_for_timeout(2000)
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    sz = os.path.getsize(path) // 1024
    print(f'  [OK] {name} ({sz}KB)')

def main():
    print('截取论文工作台截图...\n')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = ctx.new_page()

        # 登录
        page.goto(f'{FRONTEND}/login', wait_until='commit', timeout=15000)
        page.wait_for_timeout(1000)
        page.fill('input[placeholder="用户名"], input[placeholder*="用户"]', 'admin')
        page.fill('input[type="password"]', 'admin123')
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)

        # 论文工作台 - 进入第11篇论文
        page.goto(f'{FRONTEND}/papers/11', wait_until='commit', timeout=15000)
        page.wait_for_timeout(5000)
        shot(page, '11_论文工作台_流水线.png')

        # Scroll to show the agent pipeline stages
        page.evaluate('window.scrollTo(0, 300)')
        page.wait_for_timeout(500)
        shot(page, '12_论文工作台_流水线下半.png')

        # Scroll to show content area
        page.evaluate('window.scrollTo(0, 600)')
        page.wait_for_timeout(500)
        shot(page, '13_论文工作台_内容区域.png')

        browser.close()
        print(f'\n截图完成')

if __name__ == '__main__':
    main()
