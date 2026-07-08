#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PaperCraft 第3章 12张黑白SVG图表 - 专业黑白风格
适用于课程设计论文打印
"""

import os, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagrams_bw')
os.makedirs(OUT, exist_ok=True)

FONT = 'SimSun, SimHei, Microsoft YaHei, Arial, sans-serif'

WHITE  = '#FFFFFF'
BGRAY  = '#F5F5F5'
LGRAY  = '#E0E0E0'
DGRAY  = '#666666'
BLACK  = '#000000'

def H(w, h):
    return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">
<rect width="%d" height="%d" fill="%s"/>
<defs>
<marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
<polygon points="0 0,8 3,0 6" fill="%s"/>
</marker>
<filter id="sh" x="-2%%" y="-2%%" width="104%%" height="108%%">
<feDropShadow dx="0" dy="1" stdDeviation="1" flood-opacity="0.08"/>
</filter>
</defs>''' % (w, h, w, h, w, h, WHITE, BLACK)

def F(): return '</svg>'

def R(s, x, y, w, h, fill=WHITE, stroke=BLACK, sw=1.5, rx=4):
    return s + '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" stroke="%s" stroke-width="%s"/>' % (x, y, w, h, rx, fill, stroke, sw)

def RF(s, x, y, w, h, fill=WHITE, stroke=BLACK, sw=1.5, rx=4):
    return s + '<rect x="%d" y="%d" width="%d" height="%d" rx="%d" fill="%s" stroke="%s" stroke-width="%s" filter="url(#sh)"/>' % (x, y, w, h, rx, fill, stroke, sw)

def T(s, txt, x, y, sz=12, fill=BLACK, anchor='middle', bold=False):
    w = 'bold' if bold else 'normal'
    dy = sz * 0.35  # em-based vertical centering offset
    return s + '<text x="%d" y="%d" dy="%.1f" font-family="%s" font-size="%d" fill="%s" text-anchor="%s" font-weight="%s">%s</text>' % (x, y, dy, FONT, sz, fill, anchor, w, txt)

def L(s, x1, y1, x2, y2, color=BLACK, sw=1.2, dash=''):
    m = ' marker-end="url(#ar)"'
    d = ' stroke-dasharray="%s"' % dash if dash else ''
    t = '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="%s"%s%s/>'
    return s + t % (x1, y1, x2, y2, color, sw, m, d)

def box(s, cx, y, txt, bw=150, bh=30, fill=WHITE):
    x = cx - bw/2
    s = RF(s, x, y, bw, bh, fill, BLACK, 1.5, 4)
    return T(s, txt, cx, y+bh/2, 11, BLACK, 'center')

def dia(s, cx, y, txt, dw=120, dh=48):
    pts = "%d,%d %d,%d %d,%d %d,%d" % (cx, y, cx+dw/2, y+dh/2, cx, y+dh, cx-dw/2, y+dh/2)
    s += '<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.5"/>' % (pts, WHITE, BLACK)
    return T(s, txt, cx, y+dh/2, 10, BLACK, 'center')

def arr(s, cx, y1, y2):
    return L(s, cx, y1, cx, y2, BLACK, 1.2)

def save(fn, s):
    with open(os.path.join(OUT, fn), 'w', encoding='utf-8') as f:
        f.write(s)
    sys.stdout.write('  [OK] ' + fn + '\n')


def fig_3_1():
    s = H(800, 560)
    s = T(s, 'PaperCraft 系统架构图', 400, 25, 18, BLACK, 'center', True)
    layers = [
        ('表现层 (React SPA)', 55, ['首页\nHome','登录/注册','论文工作台','文献库','个人中心']),
        ('业务逻辑层 (FastAPI)', 155, ['认证管理','论文管理','Agent执行','文献管理','管理后台']),
        ('Agent编排层 (CrewAI)', 255, ['ParseAgent','OutlineAgent','WriteAgent','PolishAgent','CiteCheckAgent']),
        ('数据访问层 (SQLAlchemy)', 355, ['ORM映射','Session管理']),
        ('数据存储层 (MySQL)', 430, ['users','papers','user_refs','tasks','agent_logs']),
    ]
    for lname, ly, items in layers:
        n = len(items)
        tw = n * 120 + (n-1) * 12
        lx = (800 - tw) / 2
        s += '<rect x="40" y="%d" width="720" height="68" rx="4" fill="%s" stroke="%s" stroke-width="1" stroke-dasharray="4,4"/>' % (ly, BGRAY, LGRAY)
        s = T(s, lname, 48, ly+14, 10, DGRAY, 'start', True)
        for i, item in enumerate(items):
            bx = int(lx + i * 132)
            s = RF(s, bx, ly+24, 110, 36, WHITE, BLACK, 1.5, 4)
            s = T(s, item, bx+55, ly+42, 10, BLACK, 'center')
        if ly > 55:
            s = L(s, 400, ly-2, 400, ly+4, BLACK, 1)
    s += '<rect x="555" y="60" width="175" height="24" rx="4" fill="%s" stroke="%s" stroke-width="1"/>' % (BGRAY, LGRAY)
    s = T(s, 'SSE 实时流式推送', 642, 72, 10, DGRAY, 'center')
    s += L(s, 400, 60, 555, 72, DGRAY, 1, '4,3')
    s += F(); save('图3-1_系统架构图.svg', s)

def fig_3_2():
    s = H(760, 480)
    s = T(s, 'PaperCraft 系统功能结构图', 380, 25, 18, BLACK, 'center', True)
    s = RF(s, 290, 45, 180, 32, BLACK, BLACK, 0, 6)
    s = T(s, 'PaperCraft 论文写作系统', 380, 61, 13, WHITE, 'center', True)
    s = L(s, 380, 77, 380, 98, BLACK, 1.5)
    s = L(s, 380, 98, 185, 125, BLACK, 1.5)
    s = L(s, 380, 98, 575, 125, BLACK, 1.5)
    s = RF(s, 90, 128, 190, 30, WHITE, BLACK, 2, 6)
    s = T(s, '普通用户功能', 185, 143, 13, BLACK, 'center', True)
    s = RF(s, 480, 128, 190, 30, WHITE, BLACK, 2, 6)
    s = T(s, '管理员功能', 575, 143, 13, BLACK, 'center', True)
    for name, ux, uy in [('注册与登录',90,190),('论文管理',195,190),('Agent写作',295,190),('文献库管理',110,250),('个人中心',215,250),('论文导出Word',160,310)]:
        bw = 85 if len(name)<=5 else 90
        s = R(s, ux, uy, bw, 28, WHITE, BLACK, 1.5, 4)
        s = T(s, name, ux+bw//2, uy+14, 10, BLACK, 'center')
        px, py = ux+bw//2, uy-5
        if uy == 190: s = L(s, 185, 158, px, py, BLACK, 1)
        elif uy == 250: s = L(s, 215 if name=='个人中心' else 185, 218, px, py, BLACK, 1)
        else: s = L(s, 160, 278, px, py, BLACK, 1)
    for name, ax, ay in [('用户管理',480,190),('论文管理',585,190),('系统日志查看',510,250),('数据统计',620,250)]:
        bw = 85 if len(name)<=5 else 90
        s = R(s, ax, ay, bw, 28, WHITE, BLACK, 1.5, 4)
        s = T(s, name, ax+bw//2, ay+14, 10, BLACK, 'center')
        if ay == 190: s = L(s, 575, 158, ax+bw//2, ay-5, BLACK, 1)
        else: s = L(s, 575, 218, ax+bw//2, ay-5, BLACK, 1)
    s += F(); save('图3-2_系统功能结构图.svg', s)

def fig_3_3():
    s = H(520, 680)
    s = T(s, '登录与注册程序流程图', 260, 25, 18, BLACK, 'center', True)
    cx = 260
    for step in [(45,'开始',100,28,None),(178,'进入注册页面',140,28,None),(236,'填写注册信息\n用户名/密码/邮箱',170,42,None),(390,'注册成功，返回登录',170,28,None),(418,'输入账号密码登录',160,28,None),(590,'登录成功，进入首页',160,28,None)]:
        y, txt, bw, bh, _ = step; s = box(s, cx, y, txt, bw, bh)
    for step in [(100,'是否有账号？',120,48),(308,'校验通过？',120,48),(476,'验证通过？',120,48)]:
        y, txt, dw, dh = step; s = dia(s, cx, y, txt, dw, dh)
    for y1, y2 in [(73,100),(148,178),(206,236),(278,308),(356,390),(446,476),(524,558)]: s = arr(s, cx, y1, y2)
    s = T(s, '否', cx, 373, 9, BLACK, 'center')
    s = T(s, '否', cx, 541, 9, BLACK, 'center')
    s += L(s, cx, 356, cx-90, 356, BLACK, 1)
    s += L(s, cx-90, 356, cx-90, 236, BLACK, 1)
    s += L(s, cx-90, 236, cx, 236, BLACK, 1)
    s += L(s, cx, 148, cx+85, 148, BLACK, 1)
    s = T(s, '是', cx+42, 143, 9, BLACK, 'center')
    s += L(s, cx+85, 148, cx+85, 418, BLACK, 1)
    s += L(s, cx+85, 418, cx, 418, BLACK, 1)
    s += L(s, cx, 524, cx+90, 524, BLACK, 1)
    s = T(s, '是', cx+45, 519, 9, BLACK, 'center')
    s += L(s, cx+90, 524, cx+90, 590, BLACK, 1)
    s += L(s, cx+90, 590, cx, 590, BLACK, 1)
    s += F(); save('图3-3_登录与注册程序流程图.svg', s)

def fig_3_4():
    s = H(620, 420)
    s = T(s, '登录时序图', 310, 22, 18, BLACK, 'center', True)
    for x, name in [(80,'用户'),(200,'前端'),(340,'后端API'),(480,'MySQL'),(570,'JWT')]:
        s = R(s, x-30, 40, 60, 30, WHITE, BLACK, 1.5, 4)
        s = T(s, name, x, 55, 10, BLACK, 'center', True)
        s += L(s, x, 70, x, 400, BLACK, 1, '5,3')
    for fr, to, y, label in [(80,200,95,'1. 输入账号密码登录'),(200,340,130,'2. POST /api/auth/login'),(340,480,165,'3. SELECT * FROM users'),(480,340,200,'4. 返回用户信息'),(340,570,235,'5. bcrypt验证+生成JWT'),(570,340,270,'6. 返回JWT令牌'),(340,200,305,'7. 返回userInfo+token'),(200,80,340,'8. 存入localStorage跳转首页')]:
        s = L(s, fr, y, to, y, BLACK, 1.2)
        s = T(s, label, (fr+to)//2, y-10, 9, BLACK, 'center')
    s += F(); save('图3-4_登录时序图.svg', s)

def fig_3_5():
    s = H(480, 560)
    s = T(s, '创建论文程序流程图', 240, 25, 18, BLACK, 'center', True)
    cx = 240
    for y, txt, bw, bh in [(45,'开始',100,28),(103,'点击"新建论文"按钮',160,28),(161,'弹出创建论文模态框',160,28),(219,'填写论文主题\n选择模板、勾选文献',180,42),(373,'POST /api/papers\n后端创建论文',170,42),(445,'关联文献记录\n插入paper_references',180,42),(517,'论文列表刷新 / 状态：草稿',180,28)]:
        s = box(s, cx, y, txt, bw, bh)
    s = dia(s, cx, 291, '信息是否\n完整？')
    for y1, y2 in [(73,103),(131,161),(189,219),(261,291),(339,373),(415,445),(487,517)]:
        s = arr(s, cx, y1, y2)
    s = T(s, '否', cx, 356, 9, BLACK, 'center')
    s += L(s, cx, 339, cx-95, 339, BLACK, 1)
    s += L(s, cx-95, 339, cx-95, 161, BLACK, 1)
    s += L(s, cx-95, 161, cx, 161, BLACK, 1)
    s += F(); save('图3-5_创建论文程序流程图.svg', s)

def fig_3_6():
    s = H(850, 450)
    s = T(s, 'Agent辅助写作流程图（Human-in-the-loop）', 425, 22, 18, BLACK, 'center', True)
    for name, sx in [('文献解析\nParseAgent',55),('大纲生成\nOutlineAgent',200),('内容撰写\nWriteAgent',345),('润色优化\nPolishAgent',490),('引用检查\nCiteCheckAgent',635)]:
        s = RF(s, sx, 50, 125, 85, WHITE, BLACK, 2, 6)
        s = T(s, name, sx+62, 92, 12, BLACK, 'center', True)
        if sx > 55:
            s = L(s, sx-15, 92, sx, 92, BLACK, 1.2)
            s = T(s, '顺序执行', sx-8, 78, 8, DGRAY, 'end')
    fy = 170
    s += '<rect x="40" y="%d" width="770" height="65" rx="4" fill="%s" stroke="%s" stroke-width="1" stroke-dasharray="4,3"/>' % (fy, BGRAY, BLACK)
    s = T(s, '【Human-in-the-loop 用户审阅环节】', 425, fy+18, 12, BLACK, 'center', True)
    s = T(s, '每个Agent执行完成 -> 用户审阅 -> 批准（继续）/ 驳回（附意见重试）/ 编辑（直接修改）', 425, fy+45, 10, DGRAY, 'center')
    for name, sx in [('文献解析\nParseAgent',55),('大纲生成\nOutlineAgent',200),('内容撰写\nWriteAgent',345),('润色优化\nPolishAgent',490),('引用检查\nCiteCheckAgent',635)]:
        mid = sx + 62
        s = L(s, mid, 135, mid, fy, BLACK, 1)
        s = L(s, mid, fy+65, mid, 295, BLACK, 1)
    s = L(s, 425, 255, 425, 300, BLACK, 1.2)
    s = RF(s, 285, 300, 280, 35, WHITE, BLACK, 2, 8)
    s = T(s, '引用检查通过 -> 论文状态：已完成', 425, 317, 13, BLACK, 'center', True)
    s += '<rect x="40" y="360" width="770" height="70" rx="4" fill="%s" stroke="%s" stroke-width="1"/>' % (BGRAY, LGRAY)
    s = T(s, '各Agent职责说明', 425, 376, 11, DGRAY, 'center', True)
    for i, (name, role) in enumerate([('ParseAgent','文献解析'),('OutlineAgent','大纲生成'),('WriteAgent','内容撰写'),('PolishAgent','润色优化'),('CiteCheckAgent','引用检查')]):
        x = 55 + i * 150
        s = R(s, x, 388, 130, 28, WHITE, LGRAY, 1, 4)
        s = T(s, name, x+65, 394, 9, BLACK, 'center', True)
        s = T(s, role, x+65, 406, 8, DGRAY, 'center')
    s += F(); save('图3-6_Agent辅助写作流程图.svg', s)

def fig_3_7():
    s = H(750, 310)
    s = T(s, 'Agent执行状态图', 375, 22, 18, BLACK, 'center', True)
    for x, y, label in [(55,75,'pending\n待执行'),(205,75,'running\n执行中'),(360,75,'wait_feedback\n等待用户反馈'),(520,75,'approved\n已批准')]:
        s = RF(s, x, y, 115, 50, WHITE, BLACK, 2, 8)
        s = T(s, label, x+57, y+25, 10, BLACK, 'center', True)
    s = L(s, 170, 100, 205, 100, BLACK, 1.2); s = T(s, '开始执行', 187, 88, 9, DGRAY, 'center')
    s = L(s, 320, 100, 360, 100, BLACK, 1.2); s = T(s, '执行完成', 340, 88, 9, DGRAY, 'center')
    s = L(s, 475, 100, 520, 100, BLACK, 1.2); s = T(s, '用户批准', 497, 88, 9, DGRAY, 'center')
    s = L(s, 417, 125, 112, 125, BLACK, 1)
    s = T(s, '驳回 (reject)', 265, 118, 9, DGRAY, 'center')
    s += L(s, 112, 125, 112, 75, BLACK, 1)
    s = RF(s, 205, 165, 115, 42, WHITE, BLACK, 1.5, 6)
    s = T(s, 'error 执行异常', 262, 186, 10, BLACK, 'center', True)
    s = L(s, 262, 125, 262, 165, BLACK, 1); s = T(s, 'API异常', 260, 145, 9, DGRAY, 'center')
    s = L(s, 262, 207, 112, 207, BLACK, 1); s = T(s, '重试', 187, 200, 9, DGRAY, 'center')
    s += L(s, 112, 207, 112, 125, BLACK, 1)
    s = RF(s, 520, 165, 115, 42, WHITE, BLACK, 1.5, 6)
    s = T(s, 'edit 人工编辑', 577, 186, 10, BLACK, 'center', True)
    s = L(s, 577, 125, 577, 165, BLACK, 1); s = T(s, '用户编辑', 575, 145, 9, DGRAY, 'center')
    s = RF(s, 670, 75, 55, 50, WHITE, BLACK, 2, 25)
    s = T(s, 'OK', 697, 100, 16, BLACK, 'center', True)
    s = L(s, 635, 100, 670, 100, BLACK, 1.2)
    s += F(); save('图3-7_Agent执行状态图.svg', s)

def fig_3_8():
    s = H(840, 620)
    s = T(s, 'Agent辅助写作时序图', 420, 22, 18, BLACK, 'center', True)
    for x, name in [(55,'用户'),(155,'前端'),(265,'Orchestrator'),(390,'ParseAgent'),(505,'WriteAgent'),(630,'SSEManager'),(760,'DeepSeek')]:
        s = R(s, x-35, 40, 70, 30, WHITE, BLACK, 1.5, 4)
        s = T(s, name, x, 55, 9, BLACK, 'center', True)
        s += L(s, x, 70, x, 600, BLACK, 1, '5,3')
    for fr, to, y, label in [(55,155,85,'1. 点击"开始写作"'),(155,265,113,'2. POST /start'),(265,390,141,'3. 执行ParseAgent'),(390,760,169,'4. 调用DeepSeek API')]:
        s = L(s, fr, y, to, y, BLACK, 1.2); s = T(s, label, (fr+to)//2, y-8, 9, BLACK, 'center')
    sy = 195
    s += '<rect x="385" y="%d" width="8" height="50" rx="4" fill="%s" stroke="%s" stroke-width="1"/>' % (sy, LGRAY, BLACK)
    s = T(s, '5. SSE逐token流式输出', 570, sy+15, 9, DGRAY, 'start')
    s = L(s, 390, sy+25, 630, sy+25, BLACK, 1, '4,2')
    s += L(s, 630, sy+25, 265, sy+25, BLACK, 1, '4,2')
    s += L(s, 265, sy+25, 155, sy+25, BLACK, 1, '4,2')
    my = sy + 60
    s = L(s, 390, my, 265, my, BLACK, 1.2); s = T(s, '6. 返回解析结果', 327, my-8, 9, BLACK, 'center')
    s = L(s, 265, my+28, 155, my+28, BLACK, 1.2); s = T(s, '7. 展示给用户审阅', 210, my+20, 9, BLACK, 'center')
    my2 = 320
    s = L(s, 55, my2, 155, my2, BLACK, 1.2); s = T(s, '8. 用户确认/驳回', 105, my2-8, 9, BLACK, 'center')
    s = L(s, 155, my2+28, 265, my2+28, BLACK, 1.2); s = T(s, '9. POST /feedback', 210, my2+20, 9, BLACK, 'center')
    s += '<polygon points="245,%d 305,%d 305,%d 245,%d" fill="%s" stroke="%s" stroke-width="1"/>' % (my2+58, my2+58, my2+72, my2+72, WHITE, BLACK)
    s = T(s, '若驳回则重试', 275, my2+65, 9, BLACK, 'center')
    s = L(s, 265, 400, 505, 400, BLACK, 1.2); s = T(s, '若批准则执行WriteAgent', 385, 390, 9, BLACK, 'center')
    s = L(s, 505, 428, 760, 428, BLACK, 1.2); s = T(s, '调用API撰写内容', 632, 418, 9, BLACK, 'center')
    sy2 = 458
    s += '<rect x="500" y="%d" width="8" height="42" rx="4" fill="%s" stroke="%s" stroke-width="1"/>' % (sy2, LGRAY, BLACK)
    s = T(s, 'SSE流式输出', 630, sy2+13, 9, DGRAY, 'start')
    s = L(s, 505, sy2+20, 630, sy2+20, BLACK, 1, '4,2'); s += L(s, 630, sy2+20, 155, sy2+20, BLACK, 1, '4,2')
    s = L(s, 505, sy2+50, 265, sy2+50, BLACK, 1.2); s = T(s, '10. 返回撰写内容', 385, sy2+40, 9, BLACK, 'center')
    s = L(s, 265, sy2+78, 155, sy2+78, BLACK, 1.2); s = T(s, '11. 展示给用户', 210, sy2+68, 9, BLACK, 'center')
    s = L(s, 55, sy2+106, 155, sy2+106, BLACK, 1.2); s = T(s, '12. 用户确认', 105, sy2+96, 9, BLACK, 'center')
    s = L(s, 155, sy2+134, 265, sy2+134, BLACK, 1.2); s = T(s, '13. 确认继续', 210, sy2+124, 9, BLACK, 'center')
    s = RF(s, 225, sy2+142, 190, 28, WHITE, BLACK, 1.5, 6)
    s = T(s, '14. pipeline_complete', 320, sy2+156, 11, BLACK, 'center', True)
    s += F(); save('图3-8_Agent辅助写作时序图.svg', s)

def fig_3_9():
    s = H(500, 500)
    s = T(s, '文献库操作流程图', 250, 25, 18, BLACK, 'center', True)
    cx = 250
    s = box(s, cx, 45, '进入文献库页面', 160, 28)
    s = arr(s, cx, 73, 103)
    s = dia(s, cx, 103, '操作类型\n选择？')
    s = L(s, cx, 151, cx-95, 178, BLACK, 1)
    s = T(s, '添加文献', cx-47, 165, 9, BLACK, 'center')
    s = box(s, cx-95, 178, '填写文献信息\n标题/作者/关键词', 165, 42)
    s = arr(s, cx-95, 220, 250)
    s = box(s, cx-95, 250, '上传PDF/Word/TXT', 160, 28)
    s = arr(s, cx-95, 278, 308)
    s = box(s, cx-95, 308, '自动解析提取全文\n存入user_references', 180, 42)
    s = L(s, cx, 151, cx+95, 178, BLACK, 1)
    s = T(s, '删除/查看', cx+47, 165, 9, BLACK, 'center')
    s = box(s, cx+95, 178, '选择目标文献', 140, 28)
    s = arr(s, cx+95, 206, 236)
    s = box(s, cx+95, 236, '确认删除/查看详情', 160, 28)
    s = arr(s, cx, 350, 385)
    s = box(s, cx, 385, '操作完成  刷新列表', 160, 28)
    s += F(); save('图3-9_文献库操作流程图.svg', s)

def fig_3_10():
    s = H(500, 500)
    s = T(s, '个人中心操作流程图', 250, 25, 18, BLACK, 'center', True)
    cx = 250
    s = box(s, cx, 45, '进入个人中心', 150, 28)
    s = arr(s, cx, 73, 103)
    s = dia(s, cx, 103, '选择操作？')
    s = L(s, cx, 151, cx-95, 178, BLACK, 1); s = T(s, '修改资料', cx-47, 165, 9, BLACK, 'center')
    s = box(s, cx-95, 178, '修改昵称/邮箱/头像', 170, 28); s = arr(s, cx-95, 206, 236)
    s = box(s, cx-95, 236, 'PUT /api/user/profile', 160, 28)
    s = T(s, '保存修改', cx-95, 252, 9, DGRAY, 'center')
    s = L(s, cx, 151, cx+95, 178, BLACK, 1); s = T(s, '修改密码', cx+47, 165, 9, BLACK, 'center')
    s = box(s, cx+95, 178, '输入旧密码/新密码', 170, 28); s = arr(s, cx+95, 206, 236)
    s = box(s, cx+95, 236, 'POST /api/user/password', 170, 28)
    s = T(s, 'bcrypt验证+更新', cx+95, 252, 9, DGRAY, 'center')
    s = arr(s, cx, 264, 300)
    s = RF(s, 50, 300, 400, 50, WHITE, BLACK, 2, 8)
    s = T(s, '操作成功', 250, 315, 13, BLACK, 'center', True)
    s = T(s, '前端提示成功信息 -> 页面刷新展示最新数据', 250, 336, 10, DGRAY, 'center')
    s += F(); save('图3-10_个人中心操作流程图.svg', s)

def fig_3_11():
    s = H(680, 370)
    s = T(s, '管理员功能结构图', 340, 22, 18, BLACK, 'center', True)
    s = RF(s, 235, 42, 210, 32, BLACK, BLACK, 0, 6)
    s = T(s, '管理员功能', 340, 58, 14, WHITE, 'center', True)
    s = L(s, 340, 74, 340, 95, BLACK, 1.5)
    s = L(s, 340, 95, 105, 120, BLACK, 1.5)
    s = L(s, 340, 95, 340, 120, BLACK, 1.5)
    s = L(s, 340, 95, 575, 120, BLACK, 1.5)
    for x, cy, label in [(55,125,'用户管理'),(250,125,'论文管理'),(460,125,'系统日志'),(565,125,'数据统计')]:
        s = RF(s, x, cy, 85, 28, WHITE, BLACK, 2, 6)
        s = T(s, label, x+42, cy+14, 12, BLACK, 'center', True)
    subs = {'用户管理': [('查看用户列表',55,188),('管理用户状态',55,225)],'论文管理': [('查看所有论文',250,188),('按状态筛选',250,225),('删除异常',250,262)],'系统日志': [('查看Agent日志',460,188),('多维度筛选',460,225)],'数据统计': [('用户总数',565,188),('论文总数',565,225)]}
    for cname, items in subs.items():
        for xc, yc, cn2 in [(55,125,'用户管理'),(250,125,'论文管理'),(460,125,'系统日志'),(565,125,'数据统计')]:
            if cn2 == cname:
                cxc = xc + 42
                for iname, ix, iy in items:
                    s = L(s, cxc, 153, cxc, iy-3, BLACK, 1)
                    s = R(s, ix+5, iy, 72, 25, WHITE, BLACK, 1, 4)
                    s = T(s, iname, ix+41, iy+12, 9, BLACK, 'center')
    s += F(); save('图3-11_管理员功能结构图.svg', s)

def fig_3_12():
    s = H(620, 400)
    s = T(s, '管理员用户管理时序图', 310, 22, 18, BLACK, 'center', True)
    for x, name in [(75,'管理员'),(205,'管理后台'),(365,'后端API'),(530,'数据库')]:
        s = R(s, x-30, 40, 60, 30, WHITE, BLACK, 1.5, 4)
        s = T(s, name, x, 55, 10, BLACK, 'center', True)
        s += L(s, x, 70, x, 380, BLACK, 1, '5,3')
    for fr, to, y, label in [(75,205,95,'1. 进入用户管理页面'),(205,365,130,'2. GET /api/admin/users'),(365,530,165,'3. SELECT * FROM users'),(530,365,200,'4. 返回用户列表数据'),(365,205,235,'5. 返回JSON响应'),(205,75,270,'6. 渲染展示所有用户'),(75,205,305,'7. 点击删除用户'),(205,365,340,'8. DELETE /api/admin/users/{id}'),(365,75,375,'9. 删除成功/失败通知')]:
        s = L(s, fr, y, to, y, BLACK, 1.2)
        s = T(s, label, (fr+to)//2, y-10, 9, BLACK, 'center')
    s += F(); save('图3-12_管理员用户管理时序图.svg', s)


def main():
    print('生成12张黑白SVG图表...')
    fig_3_1(); fig_3_2(); fig_3_3(); fig_3_4(); fig_3_5(); fig_3_6()
    fig_3_7(); fig_3_8(); fig_3_9(); fig_3_10(); fig_3_11(); fig_3_12()
    print('\n全部生成完毕！目录: ' + OUT)

if __name__ == '__main__':
    main()
