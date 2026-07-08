#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复Word导出：去掉分隔线横线、避免开头空白页"""

import re

path = r'C:\Users\baiiii\Desktop\学校任务\实践周项目\backend\app\api\papers.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 去掉分隔线的横线渲染
old1 = "        if line.strip() == '---':\n            doc.add_paragraph('─' * 50)\n            i += 1\n            continue"
new1 = "        if line.strip() == '---':\n            i += 1\n            continue"
content = content.replace(old1, new1)

# 2. 添加 _has_content 变量
content = content.replace(
    "    _current_format = None\n    i = 0",
    "    _current_format = None\n    _has_content = False\n    i = 0"
)

# 3. page-break 加 _has_content 判断
old3 = """            if cmd == 'page-break':
                # 分页符
                run = doc.add_paragraph().add_run()
                br = run._element.makeelement(qn('w:br'), {qn('w:type'): 'page'})
                run._element.append(br)"""
new3 = """            if cmd == 'page-break':
                # 分页符（只在已有内容后才插入，避免开头白页）
                if _has_content:
                    run = doc.add_paragraph().add_run()
                    br = run._element.makeelement(qn('w:br'), {qn('w:type'): 'page'})
                    run._element.append(br)"""
content = content.replace(old3, new3)

# 4. 在格式标记处理块结束后，遇到正文内容时标记已有内容
# 在 "i += 1; continue" (格式标记处理后) 和 H1 检查之间插入
content = content.replace(
    "            i += 1\n            continue\n\n        # H1 标题",
    "            i += 1\n            continue\n\n        # 遇到正文内容\n        _has_content = True\n\n        # H1 标题"
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('OK - 导出已修复')
