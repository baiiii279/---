#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用 Playwright 截取系统各页面截图"""

from playwright.sync_api import sync_playwright
import os

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'screenshots')
os.makedirs(OUT, exist_ok=True)

FRONTEND = 'http://localhost:5179'

def shot(page, name, url):
    page.goto(url, wait_until='commit', timeout=15000)
    page.wait_for_timeout(2000)
    path = os.path.join(OUT, name)
    page.screenshot(path=path, full_page=True)
    sz = os.path.getsize(path) // 1024
    print(f'  [OK] {name} ({sz}KB)')

def login(page):
    page.goto(f'{FRONTEND}/login', wait_until='commit', timeout=15000)
    page.wait_for_timeout(1000)
    page.fill('input[placeholder="用户名"], input[placeholder*="用户"]', 'admin')
    page.fill('input[type="password"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_timeout(2000)

def main():
    print('截取系统截图...\n')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = ctx.new_page()

        # 先登录
        login(page)

        # 首页
        shot(page, '01_首页.png', FRONTEND + '/')

        # 论文列表
        shot(page, '02_论文列表.png', FRONTEND + '/papers')

        # 文献库
        shot(page, '03_文献库.png', FRONTEND + '/references')

        # 个人中心
        shot(page, '04_个人中心.png', FRONTEND + '/profile')

        # 管理后台 - 需要点击不同标签
        page.goto(f'{FRONTEND}/admin', wait_until='networkidle')
        page.wait_for_timeout(1500)

        # 管理后台 - 概览（默认）
        shot(page, '05_管理后台_概览.png', FRONTEND + '/admin')

        # 管理后台 - 用户管理
        page.goto(f'{FRONTEND}/admin', wait_until='networkidle')
        page.wait_for_timeout(1000)
        page.click('button:has-text("用户管理")')
        page.wait_for_timeout(1000)
        shot(page, '06_管理后台_用户管理.png', FRONTEND + '/admin')

        # 管理后台 - 论文管理
        page.goto(f'{FRONTEND}/admin', wait_until='networkidle')
        page.wait_for_timeout(1000)
        page.click('button:has-text("论文管理")')
        page.wait_for_timeout(1000)
        shot(page, '07_管理后台_论文管理.png', FRONTEND + '/admin')

        # 管理后台 - 系统日志
        page.goto(f'{FRONTEND}/admin', wait_until='networkidle')
        page.wait_for_timeout(1000)
        page.click('button:has-text("系统日志")')
        page.wait_for_timeout(1000)
        shot(page, '08_管理后台_日志.png', FRONTEND + '/admin')

        # 清除登录态后截图登录页
        page.evaluate('() => localStorage.clear()')
        shot(page, '09_登录页.png', FRONTEND + '/login')

        # 注册页面
        shot(page, '10_注册页.png', FRONTEND + '/register')

        browser.close()
        print(f'\n截图完成，共 10 张')

if __name__ == '__main__':
    main()
