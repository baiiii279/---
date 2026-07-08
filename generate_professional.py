#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Professional SVG Diagram Generator v2 - with proper layout engine
- Topological layout with back-edge handling
- Orthogonal edge routing (forward=direct, backward=right-side)
- Automatic text centering
- Pure Python, no dependencies
"""

import os, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diagrams_bw')
os.makedirs(OUT, exist_ok=True)

FONT = 'SimSun, SimHei, Microsoft YaHei, Arial, sans-serif'
FSZ = 14
CH_W = FSZ * 0.9

def tsize(text):
    lines = text.split('\n')
    return max(len(l) for l in lines), len(lines)

class Box:
    def __init__(self, nid, text, style='rect'):
        self.id = nid
        self.text = text
        self.style = style  # rect, diamond
        lines = text.split('\n')
        mc = max(len(l) for l in lines)
        self.w = max(100, mc * CH_W + 30)
        if style == 'diamond':
            self.w = max(self.w, 140)
            self.h = len(lines) * FSZ + 35
            # diamond width must be larger for visual balance
            self.w = max(self.w, self.h * 1.3)
        else:
            self.h = len(lines) * FSZ + 22
        self.layer = -1
        self.x = 0  # center
        self.y = 0

class Arrow:
    def __init__(self, src, dst, label=''):
        self.src = src
        self.dst = dst
        self.label = label

def make_flowchart(title, items, arrows):
    """
    items: [(id, text, style), ...]
    arrows: [(src, dst, label), ...]
    """
    nodes = {}
    for nid, text, style in items:
        nodes[nid] = Box(nid, text, style)

    # Build adjacency for BFS
    adj = {nid: [] for nid in nodes}
    radj = {nid: [] for nid in nodes}
    for a in arrows:
        if a[0] in nodes and a[1] in nodes:
            adj[a[0]].append(a[1])
            radj[a[1]].append(a[0])

    # Layer assignment: BFS from sources (nodes with no incoming)
    sources = [nid for nid in nodes if not radj[nid]]
    if not sources:
        sources = [list(nodes.keys())[0]]

    queue = list(sources)
    for s in sources:
        nodes[s].layer = 0
    visited = set(sources)

    while queue:
        nid = queue.pop(0)
        for nb in adj[nid]:
            new_layer = nodes[nid].layer + 1
            if nodes[nb].layer < new_layer:
                nodes[nb].layer = new_layer
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)

    # Handle unvisited nodes (cycles)
    for nid in nodes:
        if nodes[nid].layer < 0:
            nodes[nid].layer = 0

    # Group by layer
    layers = {}
    for nid, n in nodes.items():
        layers.setdefault(n.layer, []).append(n)

    max_layer = max(layers.keys())

    # Compute x positions within each layer
    PAD = 30
    GAP_H = 20
    GAP_V = 65

    for lyr in range(max_layer + 1):
        if lyr not in layers:
            continue
        ns = layers[lyr]
        x = PAD
        for n in ns:
            n.x = x + n.w / 2
            n.y = 50 + lyr * (GAP_V + 40)
            x += n.w + GAP_H

    # Diagram dimensions
    all_nodes = list(nodes.values())
    mw = max(n.x + n.w/2 for n in all_nodes) + PAD
    mh = max(n.y + n.h/2 for n in all_nodes) + 20
    dw, dh = int(mw), int(mh)

    # --- SVG Generation ---
    s = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">
<rect width="%d" height="%d" fill="#FFFFFF"/>
<defs>
<marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#000000"/></marker>
</defs>
''' % (dw, dh, dw, dh, dw, dh)

    if title:
        s += '<text x="%d" y="22" font-family="%s" font-size="18" fill="#000" text-anchor="middle" font-weight="bold">%s</text>\n' % (dw//2, FONT, title)

    # --- Edges ---
    for a in arrows:
        src, dst, label = a[0], a[1], a[2] if len(a) > 2 else ''
        if src not in nodes or dst not in nodes:
            continue
        ns = nodes[src]
        nd = nodes[dst]

        sx, sy = ns.x, ns.y + ns.h / 2 + 1  # bottom of source
        dx, dy = nd.x, nd.y - nd.h / 2 - 1   # top of dest

        if nd.layer > ns.layer:
            # Forward edge: straight then down
            my = (sy + dy) / 2
            pts = '%f,%f %f,%f %f,%f %f,%f' % (sx, sy, sx, my, dx, my, dx, dy)
        elif nd.layer == ns.layer and ns.y < nd.y:
            # Same layer, neighboring
            my = sy
            pts = '%f,%f %f,%f %f,%f %f,%f' % (sx, sy, sx+30, sy, sx+30, sy, dx, dy)
        else:
            # Back edge: route around RIGHT side
            right_x = max(n.x + n.w/2 for n in all_nodes) + 40
            my_upper = nd.y - nd.h/2 - 15
            my_lower = ns.y + ns.h/2 + 15
            pts = '%f,%f %f,%f %f,%f %f,%f %f,%f' % (sx, sy, sx, my_lower, right_x, my_lower, right_x, my_upper, dx, my_upper)
            # Add extra horizontal segment then vertical with arrow
            pts += ' %f,%f' % (dx, dy)

        s += '<polyline points="%s" fill="none" stroke="#000000" stroke-width="1.5" marker-end="url(#ar)"/>\n' % pts

        if label:
            # Position label at midpoint of first vertical segment
            if nd.layer > ns.layer:
                lx = (sx + dx) / 2
                ly = my - 8
            elif nd.layer == ns.layer and ns.y < nd.y:
                lx = sx + 15
                ly = sy - 8
            else:
                lx = right_x + 10
                ly = (my_lower + my_upper) / 2
            s += '<text x="%.1f" y="%.1f" font-family="%s" font-size="10" fill="#333" text-anchor="middle">%s</text>\n' % (lx, ly, FONT, label)

    # --- Nodes ---
    for n in all_nodes:
        x, y, w, h = n.x, n.y, n.w, n.h
        lx, ly = x - w/2, y - h/2

        if n.style == 'diamond':
            pts = '%f,%f %f,%f %f,%f %f,%f' % (x, ly, x+w/2, y, x, ly+h, x-w/2, y)
            s += '<polygon points="%s" fill="#FFFFFF" stroke="#000000" stroke-width="1.5"/>\n' % pts
        else:
            s += '<rect x="%f" y="%f" width="%f" height="%f" rx="5" fill="#FFFFFF" stroke="#000000" stroke-width="1.5"/>\n' % (lx, ly, w, h)

        # Text centered inside
        lines = n.text.split('\n')
        nlines = len(lines)
        for i, line in enumerate(lines):
            ty = y - (nlines-1) * FSZ/2 + i * FSZ + FSZ * 0.3
            s += '<text x="%f" y="%f" font-family="%s" font-size="%d" fill="#000000" text-anchor="middle">%s</text>\n' % (x, ty, FONT, FSZ, line)

    s += '</svg>'
    path = os.path.join(OUT, title + '.svg') if title else os.path.join(OUT, 'diagram.svg')
    return s


def make_sequence(title, participants, messages):
    """
    participants: [(id, name), ...]
    messages: [(src_id, dst_id, label), ...]
    """
    n_p = len(participants)
    COL_W = 110
    PAD = 40
    total_w = n_p * COL_W + PAD * 2

    # Map ids
    pid_map = {}
    for i, (nid, name) in enumerate(participants):
        pid_map[nid] = {'idx': i, 'name': name, 'x': PAD + i * COL_W + COL_W/2}

    y_rows = []  # (y_coord, src_id, dst_id, label)
    cur_y = 100
    for msg in messages:
        cur_y += 38
        src_id = msg[0]
        dst_id = msg[1]
        label = msg[2] if len(msg) > 2 else ''
        y_rows.append((cur_y, src_id, dst_id, label))

    h = cur_y + 60

    # SVG
    s = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">
<rect width="%d" height="%d" fill="#FFFFFF"/>
<defs>
<marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#000000"/></marker>
</defs>
''' % (total_w, h, total_w, h, total_w, h)

    if title:
        s += '<text x="%d" y="22" font-family="%s" font-size="18" fill="#000" text-anchor="middle" font-weight="bold">%s</text>\n' % (total_w//2, FONT, title)

    # Participants boxes and lifelines
    for nid, info in pid_map.items():
        x = info['x']
        bw = 80
        s += '<rect x="%f" y="45" width="%d" height="30" rx="4" fill="#FFFFFF" stroke="#000000" stroke-width="1.5"/>\n' % (x - bw/2, bw)
        s += '<text x="%f" y="64" font-family="%s" font-size="12" fill="#000" text-anchor="middle" font-weight="bold">%s</text>\n' % (x, FONT, info['name'])
        # Lifeline
        s += '<line x1="%f" y1="75" x2="%f" y2="%d" stroke="#000000" stroke-width="1" stroke-dasharray="5,3"/>\n' % (x, x, h-20)

    # Messages
    for y, src_id, dst_id, label in y_rows:
        src = pid_map.get(src_id)
        dst = pid_map.get(dst_id)
        if not src or not dst:
            continue
        sx, sy = src['x'], y
        dx, dy = dst['x'], y

        s += '<line x1="%f" y1="%f" x2="%f" y2="%f" stroke="#000000" stroke-width="1.2" marker-end="url(#ar)"/>\n' % (sx, sy, dx, dy)
        if label:
            s += '<text x="%f" y="%f" font-family="%s" font-size="10" fill="#000" text-anchor="middle">%s</text>\n' % ((sx+dx)/2, y-10, FONT, label)

    s += '</svg>'
    path = os.path.join(OUT, title + '.svg') if title else os.path.join(OUT, 'seq.svg')
    return s


def make_tree(title, items, edges):
    """Simple tree layout"""
    nodes = {}
    for nid, text in items:
        nodes[nid] = Box(nid, text, 'rect')

    # Build tree
    children = {nid: [] for nid in nodes}
    for p, c in edges:
        if p in children and c in nodes:
            children[p].append(c)

    # Find root
    has_p = set()
    for p, c in edges:
        has_p.add(c)
    roots = [nid for nid in nodes if nid not in has_p]
    root = roots[0] if roots else list(nodes.keys())[0]

    # Position recursively
    GAP_H = 15
    GAP_V = 60

    def place(nid, y):
        n = nodes[nid]
        n.y = y
        childs = [c for c in children[nid] if c in nodes]
        if not childs:
            return n.x, n.x  # min_x, max_x

        cx = n.x
        x_start = cx - (len(childs)-1) * GAP_H / 2 - sum(nodes[c].w for c in childs) / 2
        min_x = float('inf')
        max_x = -float('inf')
        for c in childs:
            nodes[c].x = x_start + nodes[c].w/2
            if nodes[c].x < min_x: min_x = nodes[c].x
            if nodes[c].x > max_x: max_x = nodes[c].x
            x_start += nodes[c].w + GAP_H

        for c in childs:
            cm, cxm = place(c, y + GAP_V + 40)
            if cm < min_x: min_x = cm
            if cxm > max_x: max_x = cxm

        return min_x, max_x

    # Initial x positioning - BFS level by level
    level = {root: 0}
    q = [root]
    visited = {root}
    while q:
        nid = q.pop(0)
        for c in children[nid]:
            if c not in visited and c in nodes:
                visited.add(c)
                level[c] = level[nid] + 1
                q.append(c)

    # Group by level for initial x
    levels = {}
    for nid, l in level.items():
        levels.setdefault(l, []).append(nid)

    PAD = 30
    for lyr in sorted(levels.keys()):
        ns = levels[lyr]
        x = PAD
        for nid in ns:
            if nodes[nid].x == 0 and nid != root:
                nodes[nid].x = x + nodes[nid].w / 2
                x += nodes[nid].w + 15

    # Now do proper tree layout
    def layout_node(nid, x, y):
        n = nodes[nid]
        n.x = x
        n.y = y
        childs = [c for c in children[nid] if c in nodes]
        if not childs:
            return [x]

        # Distribute children
        tw = sum(nodes[c].w for c in childs) + GAP_H * (len(childs) - 1)
        cx = x - tw / 2
        child_xs = []
        for c in childs:
            child_x = cx + nodes[c].w / 2
            child_xs.extend(layout_node(c, child_x, y + GAP_V + 40))
            cx += nodes[c].w + GAP_H
        return child_xs

    layout_node(root, nodes[root].x, 50)

    # Ensure no overlap
    all_n = list(nodes.values())
    mw = max(n.x + n.w/2 for n in all_n) + PAD
    if mw < 200: mw = 200
    mh = max(n.y + n.h/2 for n in all_n) + 20

    # SVG
    s = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">
<rect width="%d" height="%d" fill="#FFFFFF"/>
<defs>
<marker id="ar" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#000000"/></marker>
</defs>
''' % (mw, mh, mw, mh, mw, mh)

    if title:
        s += '<text x="%d" y="22" font-family="%s" font-size="18" fill="#000" text-anchor="middle" font-weight="bold">%s</text>\n' % (mw//2, FONT, title)

    # Edges
    for p, c in edges:
        if p not in nodes or c not in nodes:
            continue
        np, nc = nodes[p], nodes[c]
        sx, sy = np.x, np.y + np.h/2 + 1
        dx, dy = nc.x, nc.y - nc.h/2 - 1
        my = (sy + dy) / 2
        s += '<polyline points="%f,%f %f,%f %f,%f %f,%f" fill="none" stroke="#000000" stroke-width="1.5" marker-end="url(#ar)"/>\n' % (sx, sy, sx, my, dx, my, dx, dy)

    # Nodes
    for n in all_n:
        lx, ly = n.x - n.w/2, n.y - n.h/2
        s += '<rect x="%f" y="%f" width="%f" height="%f" rx="5" fill="#FFFFFF" stroke="#000000" stroke-width="1.5"/>\n' % (lx, ly, n.w, n.h)
        lines = n.text.split('\n')
        for i, line in enumerate(lines):
            ty = n.y - (len(lines)-1)*FSZ/2 + i*FSZ + FSZ*0.3
            s += '<text x="%f" y="%f" font-family="%s" font-size="%d" fill="#000" text-anchor="middle">%s</text>\n' % (n.x, ty, FONT, FSZ, line)

    s += '</svg>'
    return s


def save(fn, content):
    path = os.path.join(OUT, fn)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('  [OK] ' + fn)


# ========== All 12 Figures ==========

def f1():
    svg = make_flowchart('图3-1_系统架构图', [
        ('p1', 'React SPA\n(表现层)', 'rect'),
        ('p2', 'FastAPI\n(业务逻辑层)', 'rect'),
        ('p3', 'CrewAI\n(Agent编排层)', 'rect'),
        ('p4', 'DeepSeek API\n(AI能力层)', 'rect'),
        ('p5', 'MySQL\n(数据存储层)', 'rect'),
    ], [('p1','p2'),('p2','p3'),('p3','p4'),('p4','p5')])
    save('图3-1_系统架构图.svg', svg)

def f2():
    data = [
        ('root', 'PaperCraft\n论文写作系统'),
        ('u', '普通用户功能'), ('a', '管理员功能'),
        ('u1', '注册与登录'), ('u2', '论文管理'), ('u3', 'Agent写作'),
        ('u4', '文献库管理'), ('u5', '个人中心'), ('u6', '论文导出'),
        ('a1', '用户管理'), ('a2', '论文管理'), ('a3', '系统日志'), ('a4', '数据统计'),
    ]
    edges = [('root','u'),('root','a'),
             ('u','u1'),('u','u2'),('u','u3'),('u','u4'),('u','u5'),('u','u6'),
             ('a','a1'),('a','a2'),('a','a3'),('a','a4')]
    svg = make_tree('图3-2_系统功能结构图', data, edges)
    save('图3-2_系统功能结构图.svg', svg)

def f3():
    svg = make_flowchart('图3-3_登录与注册程序流程图', [
        ('start', '开始', 'rect'),
        ('q1', '是否有账号？', 'diamond'),
        ('reg', '进入注册页面', 'rect'),
        ('fill', '填写注册信息', 'rect'),
        ('q2', '校验通过？', 'diamond'),
        ('reg_ok', '注册成功\n返回登录', 'rect'),
        ('login', '输入账号密码', 'rect'),
        ('q3', '验证通过？', 'diamond'),
        ('done', '登录成功\n进入首页', 'rect'),
    ], [
        ('start', 'q1'),
        ('q1', 'reg', '否'),
        ('reg', 'fill'),
        ('fill', 'q2'),
        ('q2', 'fill', '否'),
        ('q2', 'reg_ok', '是'),
        ('reg_ok', 'login'),
        ('q1', 'login', '是'),
        ('login', 'q3'),
        ('q3', 'login', '否'),
        ('q3', 'done', '是'),
    ])
    save('图3-3_登录与注册程序流程图.svg', svg)

def f4():
    svg = make_sequence('图3-4_登录时序图', [
        ('u','用户'),('f','前端'),('api','后端API'),('db','数据库'),('jwt','JWT'),
    ], [
        ('u','f','1.输入账号密码'),('f','api','2.POST /api/auth/login'),
        ('api','db','3.SELECT users'),('db','api','4.返回用户信息'),
        ('api','jwt','5.bcrypt+JWT'),('jwt','api','6.返回令牌'),
        ('api','f','7.返回token'),('f','u','8.登录成功'),
    ])
    save('图3-4_登录时序图.svg', svg)

def f5():
    svg = make_flowchart('图3-5_创建论文程序流程图', [
        ('start', '开始', 'rect'),
        ('click', '点击新建论文', 'rect'),
        ('modal', '弹出创建模态框', 'rect'),
        ('fill', '填写主题\n选择模板/文献', 'rect'),
        ('q', '信息完整？', 'diamond'),
        ('post', 'POST /api/papers\n后端创建记录', 'rect'),
        ('link', '关联文献\n插入关联表', 'rect'),
        ('done', '列表刷新\n状态：草稿', 'rect'),
    ], [
        ('start','click'),('click','modal'),('modal','fill'),('fill','q'),
        ('q','fill','否'),('q','post','是'),('post','link'),('link','done'),
    ])
    save('图3-5_创建论文程序流程图.svg', svg)

def f6():
    svg = make_flowchart('图3-6_Agent辅助写作流程图', [
        ('p', '文献解析\nParseAgent', 'rect'),
        ('o', '大纲生成\nOutlineAgent', 'rect'),
        ('w', '内容撰写\nWriteAgent', 'rect'),
        ('po', '润色优化\nPolishAgent', 'rect'),
        ('c', '引用检查\nCiteCheckAgent', 'rect'),
        ('d', '已完成\ncomplete', 'rect'),
    ], [
        ('p','o','顺序'),('o','w','顺序'),('w','po','顺序'),('po','c','顺序'),('c','d','通过'),
    ])
    save('图3-6_Agent辅助写作流程图.svg', svg)

def f7():
    svg = make_flowchart('图3-7_Agent执行状态图', [
        ('pend', '待执行\npending', 'rect'),
        ('run', '执行中\nrunning', 'rect'),
        ('wait', '等待反馈\nwait_feedback', 'diamond'),
        ('app', '已批准\napproved', 'rect'),
        ('ok', '完成\nOK', 'rect'),
        ('err', '异常\nerror', 'rect'),
    ], [
        ('pend','run','开始'),('run','wait','完成'),
        ('wait','app','批准'),('app','ok','下一阶段'),
        ('wait','pend','驳回'),('run','err','API异常'),
        ('err','pend','重试'),('wait','run','修改'),
    ])
    save('图3-7_Agent执行状态图.svg', svg)

def f8():
    svg = make_sequence('图3-8_Agent辅助写作时序图', [
        ('u','用户'),('f','前端'),('o','Orchestrator'),('a','Agent'),('l','DeepSeek'),('s','SSE'),
    ], [
        ('u','f','1.点击开始'),('f','o','2.POST /start'),
        ('o','a','3.执行Agent'),('a','l','4.调用API'),
        ('l','a','5.返回结果'),('a','s','6.SSE推送'),
        ('s','f','7.流式输出'),('f','u','8.实时展示'),
        ('u','f','9.确认驳回'),('f','o','10.POST feedback'),
        ('o','a','11.下一Agent'),
    ])
    save('图3-8_Agent辅助写作时序图.svg', svg)

def f9():
    svg = make_flowchart('图3-9_文献库操作流程图', [
        ('in', '进入文献库', 'rect'),
        ('q', '操作类型？', 'diamond'),
        ('add', '添加文献', 'rect'),
        ('fill', '填写信息\n上传文件', 'rect'),
        ('save', '存入数据库\nuser_references', 'rect'),
        ('del', '删除/查看', 'rect'),
        ('sel', '选择目标', 'rect'),
        ('cfm', '确认操作', 'rect'),
        ('ok', '完成\n刷新列表', 'rect'),
    ], [
        ('in','q'),('q','add','添加'),('add','fill'),('fill','save'),('save','ok'),
        ('q','del','删除/查看'),('del','sel'),('sel','cfm'),('cfm','ok'),
    ])
    save('图3-9_文献库操作流程图.svg', svg)

def f10():
    svg = make_flowchart('图3-10_个人中心操作流程图', [
        ('in', '进入个人中心', 'rect'),
        ('q', '选择操作？', 'diamond'),
        ('e', '修改资料', 'rect'),
        ('ef', '修改昵称/邮箱/头像\nPUT /api/user/profile', 'rect'),
        ('p', '修改密码', 'rect'),
        ('pf', '输入旧密码/新密码\nPOST /api/user/password', 'rect'),
        ('ok', '操作成功\n页面刷新', 'rect'),
    ], [
        ('in','q'),('q','e','修改资料'),('e','ef'),('ef','ok'),
        ('q','p','修改密码'),('p','pf'),('pf','ok'),
    ])
    save('图3-10_个人中心操作流程图.svg', svg)

def f11():
    data = [
        ('root','管理员功能'),
        ('c1','用户管理'),('c2','论文管理'),('c3','系统日志'),('c4','数据统计'),
        ('c1a','查看列表'),('c1b','管理状态'),
        ('c2a','查看全部'),('c2b','按状态筛选'),('c2c','删除异常'),
        ('c3a','查看日志'),('c3b','多维筛选'),
        ('c4a','用户总数'),('c4b','论文总数'),
    ]
    edges = [('root','c1'),('root','c2'),('root','c3'),('root','c4'),
             ('c1','c1a'),('c1','c1b'),('c2','c2a'),('c2','c2b'),('c2','c2c'),
             ('c3','c3a'),('c3','c3b'),('c4','c4a'),('c4','c4b')]
    svg = make_tree('图3-11_管理员功能结构图', data, edges)
    save('图3-11_管理员功能结构图.svg', svg)

def f12():
    svg = make_sequence('图3-12_管理员用户管理时序图', [
        ('a','管理员'),('f','管理后台'),('api','后端API'),('db','数据库'),
    ], [
        ('a','f','1.进入管理页面'),('f','api','2.GET /api/admin/users'),
        ('api','db','3.SELECT'),('db','api','4.返回数据'),
        ('api','f','5.返回JSON'),('f','a','6.展示列表'),
        ('a','f','7.点击删除'),('f','api','8.DELETE'),
        ('api','a','9.通知结果'),
    ])
    save('图3-12_管理员用户管理时序图.svg', svg)


def main():
    print('用自动布局引擎 v2 生成12张图表...\n')
    f1(); f2(); f3(); f4(); f5(); f6()
    f7(); f8(); f9(); f10(); f11(); f12()
    print('\n全部生成完毕！')

if __name__ == '__main__':
    main()
