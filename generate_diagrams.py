#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PaperCraft 第3章 12张SVG图表生成器 v3 (全面重绘)
专业课程设计论文风格 · 统一设计系统 · 精准匹配代码库
"""

import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagrams')
OUT_BW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagrams_bw')
os.makedirs(OUT, exist_ok=True)
os.makedirs(OUT_BW, exist_ok=True)

FONT = 'Microsoft YaHei, SimHei, Arial, sans-serif'

# ========== SVG 元素函数（返回纯XML，不操作s） ==========
# 重要：所有函数只返回 SVG 片段，不接收 s 参数
# 调用时统一用 s += E(...)

def R(x, y, w, h, fill='#FFF', stroke='#333', sw=1.5, rx=6):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'

def RF(x, y, w, h, fill='#FFF', stroke='#333', sw=1.5, rx=6):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" filter="url(#sh)"/>'

def T(txt, x, y, sz=14, fill='#333', anchor='middle', bold=False):
    w = 'bold' if bold else 'normal'
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{sz}" fill="{fill}" text-anchor="{anchor}" font-weight="{w}" dominant-baseline="central">{txt}</text>'

def L(x1, y1, x2, y2, color='#475569', sw=1.2, marker='ar', dash=''):
    m = f' marker-end="url(#{marker})"'
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{m}{d}/>'

def BOX(cx, y, txt, wd=160, hg=34, fill='#EFF6FF', stroke='#93C5FD', sz=12, is_bw=False):
    if is_bw: fill, stroke = '#F5F5F5', '#000000'
    x = cx - wd/2
    return (R(x, y, wd, hg, fill, stroke, 1.5, 6)
            + T(txt, cx, y+hg/2, sz, '#1E293B' if not is_bw else '#000', 'center', False))

def DIAMOND(cx, y, txt, dw=130, dh=55, fill='#FEF3C7', stroke='#D97706', sz=11, bw=False):
    if bw: fill, stroke = '#F5F5F5', '#000000'
    pts = f"{cx},{y} {cx+dw/2},{y+dh/2} {cx},{y+dh} {cx-dw/2},{y+dh/2}"
    return (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
            + T(txt, cx, y+dh/2, sz, '#92400E' if not bw else '#000', 'center', False))

def ARROW(cx, y1, y2, label='', color='#475569', marker='ar', bw=False):
    if bw: color = '#000'
    r = L(cx, y1, cx, y2, color, 1.2, marker)
    if label:
        r += T(label, cx, (y1+y2)/2 - 14, 9, color, 'center')
    return r

def CARD(x, y, w, h, fill, label, sub='', fsz=14, ssz=11, lc='#FFF', sc='#CBD5E1', bw=False):
    if bw: fill, lc, sc, stroke = '#F5F5F5', '#000', '#666', '#000'
    else: stroke = fill
    r = R(x, y, w, h, fill, stroke, 1, 8)
    r += T(label, x+w/2, y+h/2 - (8 if sub else 0), fsz, lc, 'center', True)
    if sub:
        r += T(sub, x+w/2, y+h-14, ssz, sc, 'center')
    return r

def LAYER_BG(x, y, w, h, label, fill, stroke, bw=False):
    if bw: fill, stroke = '#F5F5F5', '#000'
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1" stroke-dasharray="4,4"/>'
            + T(label, x+8, y+16, 11, '#475569' if not bw else '#000', 'start', True))

def HDR(w, h, is_bw=False):
    if is_bw:
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<rect width="{w}" height="{h}" fill="#FFFFFF"/>
<defs>
<marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#000000"/></marker>
<marker id="ar-b" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#000000"/></marker>
<marker id="ar-g" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#000000"/></marker>
<marker id="ar-r" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#000000"/></marker>
<marker id="ar-a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#000000"/></marker>
<filter id="sh"><feDropShadow dx="0" dy="1" stdDeviation="1" flood-opacity="0.08"/></filter>
</defs>
'''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<rect width="{w}" height="{h}" fill="#FFFFFF"/>
<defs>
<marker id="ar" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#475569"/></marker>
<marker id="ar-b" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#2563EB"/></marker>
<marker id="ar-g" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#059669"/></marker>
<marker id="ar-r" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#DC2626"/></marker>
<marker id="ar-a" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto"><polygon points="0 0,10 3.5,0 7" fill="#D97706"/></marker>
<filter id="sh"><feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.10"/></filter>
<filter id="shl"><feDropShadow dx="0.5" dy="1" stdDeviation="1" flood-opacity="0.06"/></filter>
</defs>
'''
def FTR(): return '</svg>\n'

# ========== 颜色辅助 ==========
def c(color, bw):
    """在彩色/黑白间切换"""
    return '#000' if bw else color

# ================================================================
#  图3-1 系统架构图
# ================================================================

def fig_3_1(bw=False):
    w, h = 820, 540
    s = HDR(w, h, bw)
    s += T('PaperCraft 系统架构图', 410, 28, 20, c('#0F172A', bw), 'center', True)

    layers = [
        ('表现层 (React + Vite)', '#EFF6FF', '#93C5FD', 50, [
            ('首页', 35), ('登录/注册', 155), ('论文工作台', 275),
            ('文献库', 395), ('个人中心', 515), ('管理后台', 635),
        ]),
        ('业务逻辑层 (FastAPI)', '#ECFDF5', '#6EE7B7', 140, [
            ('认证API', 35), ('论文API', 155), ('AgentAPI', 275),
            ('文献API', 395), ('用户API', 515), ('管理API', 635),
        ]),
        ('Agent编排层 (CrewAI)', '#F5F3FF', '#C4B5FD', 230, [
            ('ParseAgent\n文献解析', 35), ('OutlineAgent\n大纲生成', 155),
            ('WriteAgent\n内容撰写', 275), ('PolishAgent\n润色优化', 395),
            ('CiteCheckAgent\n引用检查', 515), ('Orchestrator\n任务编排', 635),
        ]),
        ('AI能力层 (DeepSeek API)', '#F0F9FF', '#BAE6FD', 320, [
            ('DeepSeek\nChat API', 180), ('DeepSeek\nStream模式', 360), ('LiteLLM\n统一网关', 540),
        ]),
        ('数据存储层 (MySQL + ORM)', '#FFFBEB', '#FDE68A', 410, [
            ('users\n用户表', 35), ('papers\n论文表', 155),
            ('user_references\n文献表', 275), ('tasks\n任务表', 395),
            ('agent_logs\n日志表', 515), ('SQLAlchemy\nORM映射', 635),
        ]),
    ]

    for lname, lbg, lstroke, ly, items in layers:
        s += LAYER_BG(25, ly, 770, 75, lname, lbg, lstroke, bw)
        fc = lstroke if not bw else '#F5F5F5'
        for iname, ix in items:
            parts = iname.split('\n')
            s += CARD(ix, ly+22, 110, 46, fc, parts[0],
                      parts[1] if len(parts) > 1 else '', 10, 0,
                      '#FFF' if not bw else '#000', '#DDD' if not bw else '#666', bw)

    for ly in [125, 215, 305, 395]:
        s += L(410, ly, 410, ly+8, c('#94A3B8', bw), 1, 'ar')

    # SSE 图例
    s += R(585, 52, 185, 24, c('#F0F9FF', bw), c('#38BDF8', bw), 1, 4)
    s += T('SSE 实时流式推送', 677, 64, 10, c('#0369A1', bw), 'center')
    s += L(410, 52, 585, 64, c('#38BDF8', bw), 1, 'ar', '4,3')

    s += FTR()
    return s

# ================================================================
#  图3-2 系统功能结构图
# ================================================================

def fig_3_2(bw=False):
    w, h = 820, 520
    s = HDR(w, h, bw)
    s += T('PaperCraft 系统功能结构图', 410, 28, 20, c('#0F172A', bw), 'center', True)

    s += R(280, 48, 260, 38, c('#1E293B', bw), c('#1E293B', bw), 0, 8)
    s += T('PaperCraft 多智能体论文写作系统', 410, 67, 15, '#FFF', 'center', True)

    s += L(410, 86, 410, 108, c('#64748B', bw), 1.5, 'ar')
    s += L(410, 108, 175, 135, c('#64748B', bw), 1.5, 'ar')
    s += L(410, 108, 645, 135, c('#64748B', bw), 1.5, 'ar')

    s += R(60, 140, 230, 36, c('#2563EB', bw), c('#2563EB', bw), 0, 8)
    s += T('普通用户功能模块', 175, 158, 14, '#FFF', 'center', True)
    s += R(530, 140, 230, 36, c('#D97706', bw), c('#D97706', bw), 0, 8)
    s += T('管理员功能模块', 645, 158, 14, '#FFF', 'center', True)

    # 用户子功能
    user_fns = [('注册与登录', 95, 210), ('论文管理', 240, 210), ('Agent智能写作', 372, 210),
                ('文献库管理', 130, 275), ('个人中心', 260, 275), ('Word导出', 330, 275)]
    for name, ix, iy in user_fns:
        bw2 = min(len(name)*15, 110)
        s += R(ix, iy, bw2, 30, c('#EFF6FF', bw), c('#93C5FD', bw), 1, 6)
        s += T(name, ix+bw2/2, iy+15, 11, c('#1E40AF', bw), 'center')
        s += L(175, 176, ix+bw2/2, iy-3, c('#93C5FD', bw), 1, c('ar-b', bw) if not bw else 'ar')

    # 管理员子功能
    admin_fns = [('用户管理', 530, 210), ('论文管理', 670, 210),
                 ('系统日志', 570, 275), ('数据统计', 700, 275)]
    for name, ix, iy in admin_fns:
        bw2 = min(len(name)*15, 100)
        s += R(ix, iy, bw2, 30, c('#FFFBEB', bw), c('#FCD34D', bw), 1, 6)
        s += T(name, ix+bw2/2, iy+15, 11, c('#92400E', bw), 'center')
        s += L(645, 176, ix+bw2/2, iy-3, c('#FCD34D', bw), 1, c('ar-a', bw) if not bw else 'ar')

    s += FTR()
    return s

# ================================================================
#  图3-3 登录与注册程序流程图
# ================================================================

def fig_3_3(bw=False):
    w, h = 600, 720
    s = HDR(w, h, bw)
    s += T('登录与注册程序流程图', 300, 28, 18, c('#0F172A', bw), 'center', True)
    cx = 300

    s += BOX(cx, 48, '开始', 110, 30, c('#DCFCE7', bw), c('#4ADE80', bw), 12, bw)
    s += ARROW(cx, 78, 108, '', c('#475569', bw), 'ar', bw)
    s += DIAMOND(cx, 108, '是否有账号？', 140, 55, c('#FEF3C7', bw), c('#D97706', bw), 11, bw)

    # 左侧注册
    s += L(cx-50, 163, cx-50, 195, c('#2563EB', bw), 1, 'ar-b' if not bw else 'ar')
    s += T('否', cx-50, 180, 9, c('#2563EB', bw), 'center', True)
    s += BOX(cx-50, 195, '进入注册页面', 140, 34, c('#EFF6FF', bw), c('#93C5FD', bw), 12, bw)
    s += ARROW(cx-50, 229, 262, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx-50, 262, '填写注册信息\n用户名 / 密码 / 邮箱', 180, 44, c('#EFF6FF', bw), c('#93C5FD', bw), 11, bw)
    s += ARROW(cx-50, 306, 340, '', c('#475569', bw), 'ar', bw)
    s += DIAMOND(cx-50, 340, '校验通过？', 140, 55, c('#FEF3C7', bw), c('#D97706', bw), 11, bw)

    s += L(cx-50, 395, cx-130, 395, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += T('否', cx-90, 388, 9, c('#DC2626', bw), 'center', True)
    s += L(cx-130, 395, cx-130, 262, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += L(cx-130, 262, cx-50, 262, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')

    s += BOX(cx-50, 430, '注册成功\n返回登录页', 160, 40, c('#DCFCE7', bw), c('#4ADE80', bw), 11, bw)
    s += L(cx-50, 470, cx-50, 500, c('#475569', bw), 1, 'ar')

    # 右侧登录
    s += L(cx+50, 163, cx+50, 490, c('#059669', bw), 1, 'ar-g' if not bw else 'ar')
    s += T('是', cx+50, 380, 9, c('#059669', bw), 'center', True)
    s += L(cx+50, 490, cx, 490, c('#059669', bw), 1, 'ar-g' if not bw else 'ar')

    s += BOX(cx, 490, '输入账号密码登录', 170, 34, c('#EFF6FF', bw), c('#93C5FD', bw), 12, bw)
    s += ARROW(cx, 524, 558, '', c('#475569', bw), 'ar', bw)
    s += DIAMOND(cx, 558, '验证通过？', 140, 55, c('#FEF3C7', bw), c('#D97706', bw), 11, bw)

    s += L(cx, 613, cx+80, 613, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += T('否', cx+40, 606, 9, c('#DC2626', bw), 'center', True)
    s += L(cx+80, 613, cx+80, 490, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += L(cx+80, 490, cx, 490, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')

    s += BOX(cx, 650, '登录成功\n进入首页', 150, 40, c('#DCFCE7', bw), c('#4ADE80', bw), 12, bw)

    s += FTR()
    return s

# ================================================================
#  图3-4 登录时序图
# ================================================================

def fig_3_4(bw=False):
    w, h = 720, 480
    s = HDR(w, h, bw)
    s += T('用户登录时序图', 360, 25, 18, c('#0F172A', bw), 'center', True)

    parts = [(95, '用户'), (220, '前端'), (375, '后端API'), (535, 'MySQL'), (650, 'JWT')]
    for x, name in parts:
        s += R(x-40, 42, 80, 34, c('#F1F5F9', bw), c('#CBD5E1', bw), 1, 6)
        s += T(name, x, 59, 10, c('#1E293B', bw), 'center', True)
        s += L(x, 76, x, 460, c('#CBD5E1', bw), 1, 'ar', '5,3')

    msgs = [
        (95, 220, 105, '1. 输入账号密码', c('#475569', bw), 'ar'),
        (220, 375, 142, '2. POST /api/auth/login', c('#2563EB', bw), 'ar-b' if not bw else 'ar'),
        (375, 535, 180, '3. SELECT * FROM users', c('#2563EB', bw), 'ar-b' if not bw else 'ar'),
        (535, 375, 218, '4. 返回用户信息(哈希密码)', c('#059669', bw), 'ar-g' if not bw else 'ar'),
        (375, 650, 256, '5. bcrypt验证 + JWT签发', c('#2563EB', bw), 'ar-b' if not bw else 'ar'),
        (650, 375, 294, '6. 返回JWT令牌(7天有效)', c('#059669', bw), 'ar-g' if not bw else 'ar'),
        (375, 220, 332, '7. 返回{user, token}', c('#059669', bw), 'ar-g' if not bw else 'ar'),
        (220, 95, 370, '8. 存入localStorage→首页', c('#475569', bw), 'ar'),
    ]

    for fr, to, y, label, color, marker in msgs:
        s += L(fr, y, to, y, color, 1.2, marker)
        s += T(label, (fr+to)/2, y-10, 9, color, 'center')

    s += R(75, 392, 165, 24, c('#F0F9FF', bw), c('#38BDF8', bw), 1, 4)
    s += T('登录成功 → 激活菜单/路由', 157, 404, 9, c('#0369A1', bw), 'center')

    s += FTR()
    return s

# ================================================================
#  图3-5 创建论文程序流程图
# ================================================================

def fig_3_5(bw=False):
    w, h = 520, 600
    s = HDR(w, h, bw)
    s += T('创建论文程序流程图', 260, 28, 18, c('#0F172A', bw), 'center', True)
    cx = 260

    s += BOX(cx, 50, '开始', 110, 30, c('#DCFCE7', bw), c('#4ADE80', bw), 12, bw)
    s += ARROW(cx, 80, 110, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx, 110, '点击"新建论文"按钮', 170, 34, c('#EFF6FF', bw), c('#93C5FD', bw), 12, bw)
    s += ARROW(cx, 144, 175, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx, 175, '弹出创建论文模态框', 170, 34, c('#EFF6FF', bw), c('#93C5FD', bw), 12, bw)
    s += ARROW(cx, 209, 240, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx, 240, '填写论文主题\n勾选关联文献', 190, 44, c('#F0F9FF', bw), c('#38BDF8', bw), 11, bw)
    s += ARROW(cx, 284, 315, '', c('#475569', bw), 'ar', bw)
    s += DIAMOND(cx, 315, '信息是否\n完整？', 140, 55, c('#FEF3C7', bw), c('#D97706', bw), 11, bw)

    s += L(cx, 370, cx-100, 370, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += T('否', cx-50, 364, 9, c('#DC2626', bw), 'center', True)
    s += L(cx-100, 370, cx-100, 175, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += L(cx-100, 175, cx, 175, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')

    s += BOX(cx, 405, 'POST /api/papers\n后端创建论文记录', 180, 44, c('#DCFCE7', bw), c('#4ADE80', bw), 11, bw)
    s += ARROW(cx, 449, 482, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx, 482, 'INSERT paper_references\n关联所选文献', 190, 44, c('#F0FDF4', bw), c('#4ADE80', bw), 11, bw)
    s += ARROW(cx, 526, 558, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx, 558, '完成 — 状态: draft(草稿)', 180, 34, c('#DCFCE7', bw), c('#4ADE80', bw), 12, bw)

    s += FTR()
    return s

# ================================================================
#  图3-6 Agent辅助写作流程图
# ================================================================

def fig_3_6(bw=False):
    w, h = 900, 500
    s = HDR(w, h, bw)
    s += T('Agent辅助写作流程图（Human-in-the-loop）', 450, 28, 18, c('#0F172A', bw), 'center', True)

    stages = [
        ('文献解析\nParseAgent', c('#7C3AED', bw), 55),
        ('大纲生成\nOutlineAgent', c('#2563EB', bw), 215),
        ('内容撰写\nWriteAgent', c('#059669', bw), 375),
        ('润色优化\nPolishAgent', c('#D97706', bw), 535),
        ('引用检查\nCiteCheckAgent', c('#DC2626', bw), 695),
    ]

    for i, (name, color, sx) in enumerate(stages):
        s += R(sx, 50, 140, 80, color, color, 1, 8)
        s += T(name, sx+70, 90, 13, '#FFF', 'center', True)
        if i > 0:
            prev = stages[i-1][2] + 140
            s += L(prev, 90, sx, 90, c('#94A3B8', bw), 1.2, 'ar')
            s += T('下一步', (prev+sx)/2, 78, 9, c('#64748B', bw), 'center')

    # 底部说明
    s += R(30, 150, 840, 75, c('#FFFBEB', bw), c('#FCD34D', bw), 1.5, 8)
    s += T('Human-in-the-Loop 用户审阅机制', 450, 168, 14, c('#92400E', bw), 'center', True)
    s += T('每个 Agent 执行完成 → 用户审阅输出 → 批准（继续）| 驳回（附意见重试）| 编辑（直接修改）',
           450, 196, 10, c('#B45309', bw), 'center')

    for _, _, sx in stages:
        mid = sx + 70
        s += L(mid, 130, mid, 150, c('#94A3B8', bw), 1, 'ar')
        s += L(mid, 225, mid, 330, c('#94A3B8', bw), 1, 'ar')

    s += L(450, 290, 450, 340, c('#64748B', bw), 1.2, 'ar')
    s += R(310, 340, 280, 40, c('#DCFCE7', bw), c('#4ADE80', bw), 2, 10)
    s += T('引用检查通过 → 论文状态: complete(已完成)', 450, 360, 14, c('#166534', bw), 'center', True)

    # Agent角色表
    s += R(30, 400, 840, 80, c('#F8FAFC', bw), c('#CBD5E1', bw), 1, 6)
    s += T('各 Agent 角色与职责', 450, 418, 12, c('#475569', bw), 'center', True)

    roles = [
        ('ParseAgent', '解析文献全文\n提取关键信息', c('#7C3AED', bw)),
        ('OutlineAgent', '根据解析结果\n生成论文大纲', c('#2563EB', bw)),
        ('WriteAgent', '按大纲逐节\n撰写论文内容', c('#059669', bw)),
        ('PolishAgent', '优化语言表达\n修正语法格式', c('#D97706', bw)),
        ('CiteCheckAgent', '验证引用格式\n确保文献匹配', c('#DC2626', bw)),
    ]

    for i, (aname, adesc, acolor) in enumerate(roles):
        x = 50 + i * 165
        s += R(x, 432, 150, 38, c('#FFF', bw), c('#CBD5E1', bw), 1, 4)
        s += T(aname, x+38, 444, 9, acolor, 'center', True)
        s += T(adesc, x+105, 444, 8, c('#64748B', bw), 'center')

    s += FTR()
    return s

# ================================================================
#  图3-7 Agent执行状态图
# ================================================================

def fig_3_7(bw=False):
    w, h = 820, 360
    s = HDR(w, h, bw)
    s += T('Agent 执行状态图', 410, 28, 18, c('#0F172A', bw), 'center', True)

    states = [
        (60, 80, 'pending\n待执行', c('#F1F5F9', bw), c('#CBD5E1', bw)),
        (210, 80, 'running\n执行中', c('#EFF6FF', bw), c('#93C5FD', bw)),
        (370, 80, 'wait_feedback\n等待用户反馈', c('#FEF3C7', bw), c('#D97706', bw)),
        (540, 80, 'approved\n已批准', c('#DCFCE7', bw), c('#4ADE80', bw)),
    ]

    for x, y, label, fill, stroke in states:
        s += R(x, y, 130, 55, fill, stroke, 2, 10)
        s += T(label, x+65, y+27, 11, c('#1E293B', bw), 'center', True)

    s += L(190, 107, 210, 107, c('#2563EB', bw), 1.2, 'ar-b' if not bw else 'ar')
    s += T('开始执行', 200, 95, 9, c('#2563EB', bw), 'center')
    s += L(340, 107, 370, 107, c('#059669', bw), 1.2, 'ar-g' if not bw else 'ar')
    s += T('执行完成', 355, 95, 9, c('#059669', bw), 'center')
    s += L(500, 107, 540, 107, c('#059669', bw), 1.2, 'ar-g' if not bw else 'ar')
    s += T('批准', 520, 95, 9, c('#059669', bw), 'center')

    s += L(435, 135, 125, 135, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += T('驳回(reject)', 280, 128, 9, c('#DC2626', bw), 'center')
    s += L(125, 135, 125, 80, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')

    s += R(210, 180, 130, 45, c('#FEF2F2', bw), c('#FCA5A5', bw), 2, 8)
    s += T('error 执行异常', 275, 202, 11, c('#991B1B', bw), 'center', True)
    s += L(275, 135, 275, 180, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += T('API异常', 240, 158, 9, c('#DC2626', bw), 'end')
    s += L(275, 225, 125, 225, c('#2563EB', bw), 1, 'ar-b' if not bw else 'ar')
    s += T('重试', 200, 218, 9, c('#2563EB', bw), 'center')
    s += L(125, 225, 125, 135, c('#2563EB', bw), 1, 'ar-b' if not bw else 'ar')

    s += R(540, 180, 130, 45, c('#F0F9FF', bw), c('#38BDF8', bw), 2, 8)
    s += T('edit 人工编辑', 605, 202, 11, c('#0369A1', bw), 'center', True)
    s += L(605, 135, 605, 180, c('#38BDF8', bw), 1, 'ar')
    s += T('编辑', 640, 158, 9, c('#0369A1', bw), 'start')

    s += R(710, 80, 60, 55, c('#DCFCE7', bw), c('#4ADE80', bw), 2, 30)
    s += T('OK', 740, 107, 18, c('#166534', bw), 'center', True)
    s += L(670, 107, 710, 107, c('#059669', bw), 1.2, 'ar-g' if not bw else 'ar')

    s += FTR()
    return s

# ================================================================
#  图3-8 Agent辅助写作时序图
# ================================================================

def fig_3_8(bw=False):
    w, h = 920, 720
    s = HDR(w, h, bw)
    s += T('Agent 辅助写作时序图', 460, 25, 18, c('#0F172A', bw), 'center', True)

    parts = [(60, '用户'), (170, '前端'), (290, 'Orchestrator'),
             (420, 'Agent'), (550, 'SSEManager'), (680, 'DeepSeek'),
             (800, '数据库')]

    for x, name in parts:
        bw2 = 65 if len(name) <= 8 else 80
        s += R(x-bw2/2, 42, bw2, 34, c('#F1F5F9', bw), c('#CBD5E1', bw), 1, 6)
        s += T(name, x, 59, 9, c('#1E293B', bw), 'center', True)
        s += L(x, 76, x, 700, c('#CBD5E1', bw), 1, 'ar', '5,3')

    def msg(fr, to, y, label, color, marker='ar'):
        return (L(fr, y, to, y, color, 1.2, marker)
                + T(label, (fr+to)/2, y-10, 9, color, 'center'))

    def sse_seg(x, y, w=8, h=60):
        return R(x, y, w, h, '#E0E7FF', '#6366F1', 1, 4)

    def sse_arc(fr, to, y):
        col = '#000' if bw else '#6366F1'
        return L(fr, y, to, y, col, 1, 'ar', '4,2')

    y0 = 95
    s += msg(60, 170, y0, '1. 点击"开始写作"', c('#475569', bw))
    s += msg(170, 290, y0+35, '2. POST /api/papers/{id}/agent/start', c('#2563EB', bw), 'ar-b' if not bw else 'ar')
    s += msg(290, 420, y0+70, '3. 执行 Agent (kickoff)', c('#2563EB', bw), 'ar-b' if not bw else 'ar')
    s += msg(420, 680, y0+105, '4. litellm.completion()', c('#2563EB', bw), 'ar-b' if not bw else 'ar')

    # 5. SSE 首次流式
    sy = y0 + 150
    s += sse_seg(415, sy, 8, 60)
    s += T('5. SSE 逐 token 流式输出', 600, sy+15, 10, c('#4338CA', bw), 'start')
    s += sse_arc(420, 550, sy+30)
    s += sse_arc(550, 290, sy+30)
    s += sse_arc(290, 170, sy+30)
    s += T('agent_stream 事件', 350, sy+22, 8, c('#4338CA', bw), 'center')

    # 6-8
    sy2 = sy + 75
    s += msg(420, 800, sy2+15, '6. 更新 paper.content', c('#059669', bw), 'ar-g' if not bw else 'ar')
    s += msg(420, 290, sy2+50, '7. Crew结果 → agent_complete', c('#059669', bw), 'ar-g' if not bw else 'ar')
    s += msg(290, 170, sy2+85, '8. SSE → 展示给用户审阅', c('#059669', bw), 'ar-g' if not bw else 'ar')

    # 9-10 用户反馈
    fy = sy2 + 130
    s += msg(60, 170, fy, '9. 确认 / 驳回 / 编辑', c('#D97706', bw), 'ar-a' if not bw else 'ar')
    s += msg(170, 290, fy+35, '10. POST /feedback', c('#D97706', bw), 'ar-a' if not bw else 'ar')

    # 10a 分支
    s += R(230, fy+65, 150, 50, c('#FFFBEB', bw), c('#D97706', bw), 1.5, 6)
    s += T('若驳回 → 重试当前 Agent', 305, fy+80, 9, c('#92400E', bw), 'center')
    s += T('若批准 → 下一 Agent', 305, fy+100, 9, c('#166534', bw), 'center')

    # 11-12
    fy2 = fy + 130
    s += msg(290, 420, fy2, '11. 批准 → 执行下一Agent', c('#059669', bw), 'ar-g' if not bw else 'ar')
    s += msg(420, 680, fy2+35, '12. 再次调用 DeepSeek', c('#2563EB', bw), 'ar-b' if not bw else 'ar')

    # 13 SSE二次流式
    sy3 = fy2 + 70
    s += sse_seg(415, sy3, 8, 40)
    s += T('13. SSE 逐 token 输出', 580, sy3+15, 9, c('#4338CA', bw), 'start')
    s += sse_arc(420, 550, sy3+20)
    s += sse_arc(550, 170, sy3+20)

    # 14-15 完成
    fy3 = sy3 + 55
    s += msg(290, 170, fy3, '14. pipeline_complete 事件', c('#059669', bw), 'ar-g' if not bw else 'ar')
    s += msg(170, 60, fy3+35, '15. 论文完成，通知用户', c('#475569', bw))
    s += R(315, fy3+55, 200, 35, c('#DCFCE7', bw), c('#4ADE80', bw), 2, 10)
    s += T('✔ 论文状态 → complete(已完成)', 415, fy3+72, 12, c('#166534', bw), 'center', True)

    s += FTR()
    return s

# ================================================================
#  图3-9 文献库操作流程图
# ================================================================

def fig_3_9(bw=False):
    w, h = 560, 520
    s = HDR(w, h, bw)
    s += T('文献库操作流程图', 280, 28, 18, c('#0F172A', bw), 'center', True)
    cx = 280

    s += BOX(cx, 48, '进入文献库页面', 170, 34, c('#EFF6FF', bw), c('#93C5FD', bw), 12, bw)
    s += ARROW(cx, 82, 112, '', c('#475569', bw), 'ar', bw)
    s += DIAMOND(cx, 112, '操作类型\n选择？', 140, 55, c('#FEF3C7', bw), c('#D97706', bw), 11, bw)

    # 添加
    s += L(cx-40, 167, cx-110, 195, c('#2563EB', bw), 1, 'ar-b' if not bw else 'ar')
    s += T('添加文献', cx-80, 180, 9, c('#2563EB', bw), 'center', True)
    s += BOX(cx-110, 195, '填写文献信息\n标题/作者/关键词/摘要', 190, 44, c('#EFF6FF', bw), c('#93C5FD', bw), 11, bw)
    s += ARROW(cx-110, 239, 269, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx-110, 269, '上传 PDF/Word/TXT\n文件自动解析全文存储', 200, 44, c('#F0F9FF', bw), c('#38BDF8', bw), 11, bw)
    s += ARROW(cx-110, 313, 343, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx-110, 343, 'INSERT user_references\n保存 full_text + abstract', 200, 44, c('#F0FDF4', bw), c('#4ADE80', bw), 11, bw)

    # 删除/查看
    s += L(cx+40, 167, cx+110, 195, c('#DC2626', bw), 1, 'ar-r' if not bw else 'ar')
    s += T('删除/查看', cx+80, 180, 9, c('#DC2626', bw), 'center', True)
    s += BOX(cx+110, 195, '选择目标文献', 150, 34, c('#FEF2F2', bw), c('#FCA5A5', bw), 12, bw)
    s += ARROW(cx+110, 229, 259, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx+110, 259, '确认删除/查看详情', 170, 34, c('#FEF2F2', bw), c('#FCA5A5', bw), 12, bw)

    s += L(cx-110, 387, cx, 430, c('#475569', bw), 1, 'ar')
    s += L(cx+110, 293, cx, 430, c('#475569', bw), 1, 'ar')
    s += BOX(cx, 430, '操作完成  刷新列表', 170, 34, c('#DCFCE7', bw), c('#4ADE80', bw), 12, bw)

    s += FTR()
    return s

# ================================================================
#  图3-10 个人中心操作流程图
# ================================================================

def fig_3_10(bw=False):
    w, h = 580, 500
    s = HDR(w, h, bw)
    s += T('个人中心操作流程图', 290, 28, 18, c('#0F172A', bw), 'center', True)
    cx = 290

    s += BOX(cx, 48, '进入个人中心', 160, 34, c('#EFF6FF', bw), c('#93C5FD', bw), 12, bw)
    s += ARROW(cx, 82, 112, '', c('#475569', bw), 'ar', bw)
    s += DIAMOND(cx, 112, '选择操作？', 140, 55, c('#FEF3C7', bw), c('#D97706', bw), 11, bw)

    s += L(cx-40, 167, cx-120, 195, c('#2563EB', bw), 1, 'ar-b' if not bw else 'ar')
    s += T('修改资料', cx-80, 180, 9, c('#2563EB', bw), 'center')
    s += BOX(cx-120, 195, '修改昵称/邮箱/头像', 190, 34, c('#EFF6FF', bw), c('#93C5FD', bw), 12, bw)
    s += ARROW(cx-120, 229, 262, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx-120, 262, 'PUT /api/user/profile', 170, 34, c('#F0FDF4', bw), c('#4ADE80', bw), 11, bw)
    s += T('保存修改', cx-120, 279, 9, c('#166534', bw), 'center')

    s += L(cx+40, 167, cx+120, 195, c('#D97706', bw), 1, 'ar-a' if not bw else 'ar')
    s += T('修改密码', cx+80, 180, 9, c('#D97706', bw), 'center')
    s += BOX(cx+120, 195, '输入旧密码/新密码', 190, 34, c('#FFFBEB', bw), c('#FCD34D', bw), 12, bw)
    s += ARROW(cx+120, 229, 262, '', c('#475569', bw), 'ar', bw)
    s += BOX(cx+120, 262, 'POST /api/user/password', 180, 34, c('#FFF', bw), c('#CBD5E1', bw), 11, bw)
    s += T('bcrypt 验证 + 更新', cx+120, 279, 9, c('#92400E', bw), 'center')

    s += L(cx-120, 296, cx, 340, c('#475569', bw), 1, 'ar')
    s += L(cx+120, 296, cx, 340, c('#475569', bw), 1, 'ar')
    s += R(65, 340, 450, 55, c('#F0FDF4', bw), c('#4ADE80', bw), 1.5, 8)
    s += T('操作成功', 290, 357, 13, c('#166534', bw), 'center', True)
    s += T('前端提示成功 → 更新状态 → 刷新页面数据', 290, 380, 11, c('#047857', bw), 'center')

    s += FTR()
    return s

# ================================================================
#  图3-11 管理员功能结构图
# ================================================================

def fig_3_11(bw=False):
    w, h = 750, 400
    s = HDR(w, h, bw)
    s += T('管理员功能结构图', 375, 28, 18, c('#0F172A', bw), 'center', True)

    s += R(250, 48, 250, 38, c('#D97706', bw), c('#D97706', bw), 0, 8)
    s += T('管理员功能', 375, 67, 15, '#FFF', 'center', True)

    s += L(375, 86, 375, 112, c('#D97706', bw), 1.5, 'ar')
    s += L(375, 112, 110, 138, c('#D97706', bw), 1.5, 'ar')
    s += L(375, 112, 375, 138, c('#D97706', bw), 1.5, 'ar')
    s += L(375, 112, 640, 138, c('#D97706', bw), 1.5, 'ar')

    cats = [
        (50, 145, '用户管理', c('#FEF2F2', bw), c('#FCA5A5', bw)),
        (280, 145, '论文管理', c('#FFFBEB', bw), c('#FCD34D', bw)),
        (480, 145, '系统日志', c('#F0F9FF', bw), c('#38BDF8', bw)),
        (610, 145, '数据统计', c('#F0FDF4', bw), c('#4ADE80', bw)),
    ]

    for cx, cy, label, fill, stroke in cats:
        s += R(cx, cy, 100, 32, fill, stroke, 1.5, 6)
        s += T(label, cx+50, cy+16, 12, c('#1E293B', bw), 'center', True)

    subs = {
        '用户管理': [('查看用户列表', 50+20, 210), ('角色权限管理', 50+20, 250)],
        '论文管理': [('查看全部论文', 280+20, 210), ('按状态筛选', 280+20, 250), ('删除异常论文', 280+20, 290)],
        '系统日志': [('查看Agent日志', 480+20, 210), ('多维筛选查询', 480+20, 250)],
        '数据统计': [('用户/论文总数', 610+20, 210), ('状态分布统计', 610+20, 250)],
    }

    for cat_name, items in subs.items():
        for cxc, cy, cname, cfill, cstroke in cats:
            if cname == cat_name:
                for iname, ix, iy in items:
                    s += L(cxc+50, 177, cxc+50, iy-3, c('#CBD5E1', bw), 1, 'ar')
                    w2 = max(len(iname)*9, 80)
                    s += R(ix-8, iy, w2, 26, c('#FFF', bw), c('#CBD5E1', bw), 1, 5)
                    s += T(iname, ix+w2/2-8, iy+13, 10, c('#475569', bw), 'center')

    s += FTR()
    return s

# ================================================================
#  图3-12 管理员用户管理时序图
# ================================================================

def fig_3_12(bw=False):
    w, h = 700, 460
    s = HDR(w, h, bw)
    s += T('管理员用户管理时序图', 350, 25, 18, c('#0F172A', bw), 'center', True)

    parts = [(80, '管理员'), (220, '管理后台'), (400, '后端API'), (580, '数据库')]
    for x, name in parts:
        s += R(x-40, 42, 80, 34, c('#FFFBEB', bw), c('#FCD34D', bw), 1, 6)
        s += T(name, x, 59, 10, c('#1E293B', bw), 'center', True)
        s += L(x, 76, x, 440, c('#CBD5E1', bw), 1, 'ar', '5,3')

    def msg(fr, to, y, label, color, marker='ar'):
        r = L(fr, y, to, y, color, 1.2, marker)
        r += T(label, (fr+to)/2, y-10, 9, color, 'center')
        return r

    s += msg(80, 220, 105, '1. 进入用户管理页面', c('#475569', bw))
    s += msg(220, 400, 142, '2. GET /api/admin/users', c('#D97706', bw), 'ar-a' if not bw else 'ar')
    s += msg(400, 580, 180, '3. SELECT * FROM users', c('#D97706', bw), 'ar-a' if not bw else 'ar')
    s += msg(580, 400, 218, '4. 返回用户列表数据', c('#059669', bw), 'ar-g' if not bw else 'ar')
    s += msg(400, 220, 256, '5. 返回 JSON 响应', c('#059669', bw), 'ar-g' if not bw else 'ar')
    s += msg(220, 80, 294, '6. 渲染表格展示所有用户', c('#475569', bw))

    # 删除操作标记
    s += R(60, 320, 180, 28, c('#FEF2F2', bw), c('#FCA5A5', bw), 1, 4)
    s += T('删除管理操作示例 ↓', 150, 334, 10, c('#991B1B', bw), 'center', True)

    s += msg(80, 220, 365, '7. 点击删除用户', c('#DC2626', bw), 'ar-r' if not bw else 'ar')
    s += msg(220, 400, 400, '8. DELETE /api/admin/users/{id}', c('#DC2626', bw), 'ar-r' if not bw else 'ar')
    s += msg(400, 80, 435, '9. 返回删除成功/失败通知', c('#059669', bw), 'ar-g' if not bw else 'ar')

    s += FTR()
    return s

# ================================================================
#  批量生成
# ================================================================

GENERATORS = [
    ('图3-1_系统架构图.svg', fig_3_1),
    ('图3-2_系统功能结构图.svg', fig_3_2),
    ('图3-3_登录与注册程序流程图.svg', fig_3_3),
    ('图3-4_登录时序图.svg', fig_3_4),
    ('图3-5_创建论文程序流程图.svg', fig_3_5),
    ('图3-6_Agent辅助写作流程图.svg', fig_3_6),
    ('图3-7_Agent执行状态图.svg', fig_3_7),
    ('图3-8_Agent辅助写作时序图.svg', fig_3_8),
    ('图3-9_文献库操作流程图.svg', fig_3_9),
    ('图3-10_个人中心操作流程图.svg', fig_3_10),
    ('图3-11_管理员功能结构图.svg', fig_3_11),
    ('图3-12_管理员用户管理时序图.svg', fig_3_12),
]

def main():
    print('=' * 60)
    print('  PaperCraft 第3章 图表生成器 v3')
    print('  生成 12 张专业 SVG 图表')
    print('=' * 60)

    for fn, gen in GENERATORS:
        print(f'\n生成 {fn} ...')
        svg = gen(bw=False)
        with open(os.path.join(OUT, fn), 'w', encoding='utf-8') as f:
            f.write(svg)
        print(f'  [CLR] {fn} ({len(svg)} bytes)')
        svg_bw = gen(bw=True)
        with open(os.path.join(OUT_BW, fn), 'w', encoding='utf-8') as f:
            f.write(svg_bw)
        print(f'  [BW]  {fn} ({len(svg_bw)} bytes)')

    print(f'\n{"=" * 60}')
    print(f'  全部完成！')
    print(f'  彩色: {OUT}/')
    print(f'  黑白: {OUT_BW}/')
    print(f'{"=" * 60}')

if __name__ == '__main__':
    main()
