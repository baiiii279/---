#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用 Mermaid.js 生成12张图表"""
import os, re, json
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'diagrams_bw')
os.makedirs(OUT, exist_ok=True)

with open(os.path.expanduser('~/node_modules/mermaid/dist/mermaid.min.js'), 'r', encoding='utf-8') as f:
    MERMAID_JS = f.read()

HTML_TEMPLATE = '<html><body><div id="m"></div><script>' + MERMAID_JS + '</script></body></html>'

def render(name, code):
    svg_path = os.path.join(OUT, name + '.svg')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        page.set_content(HTML_TEMPLATE, wait_until='load')
        result = page.evaluate('''(c) => {
            mermaid.initialize({
                theme:'default',
                themeVariables:{
                    primaryColor:'#FFFFFF', primaryBorderColor:'#000000', primaryTextColor:'#000000',
                    lineColor:'#000000', secondaryColor:'#FFFFFF', tertiaryColor:'#F5F5F5',
                    fontSize:'14px', fontFamily:'SimSun, SimHei, sans-serif',
                    edgeLabelBackground:'#FFFFFF'
                },
                flowchart:{useMaxWidth:false, htmlLabels:true}
            });
            return mermaid.render('m', c).then(r => r.svg);
        }''', code)
        browser.close()

    # Extract viewBox and write clean SVG
    m_vb = re.search(r'viewBox="([^"]*)"', result)
    if m_vb:
        parts = m_vb.group(1).split()
        w, h = int(float(parts[2])), int(float(parts[3]))
    else:
        w, h = 600, 400

    # Clean up the SVG (remove outer svg tag attributes we want to replace)
    inner = re.sub(r'^<svg[^>]*>', '', result)
    inner = re.sub(r'</svg>\s*$', '', inner)

    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n')
        f.write(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>\n')
        f.write(inner)
        f.write('\n</svg>')
    print(f'  [OK] {name}.svg ({w}x{h})')


def main():
    print('用 Mermaid.js 生成12张图表...\n')

    render('图3-1_系统架构图', '''flowchart TD
P1["React SPA (表现层)"]
P2["FastAPI (业务逻辑层)"]
P3["CrewAI (Agent编排层)"]
P4["DeepSeek API (AI能力层)"]
P5["MySQL (数据存储层)"]
P1 --> P2 --> P3 --> P4 --> P5''')

    render('图3-2_系统功能结构图', '''flowchart TD
Root["PaperCraft 论文写作系统"]
User["普通用户功能"]
Admin["管理员功能"]
Root --> User & Admin
User --> U1["注册与登录"] & U2["论文管理"] & U3["Agent写作"]
User --> U4["文献库管理"] & U5["个人中心"] & U6["论文导出"]
Admin --> A1["用户管理"] & A2["论文管理"] & A3["系统日志"] & A4["数据统计"]''')

    render('图3-3_登录与注册程序流程图', '''flowchart TD
Start(["开始"])
Q1{"是否有账号？"}
Reg["进入注册页面"]
Fill["填写注册信息"]
Q2{"校验通过？"}
RegOk["注册成功\n返回登录"]
Login["输入账号密码"]
Q3{"验证通过？"}
Done["登录成功\n进入首页"]
Start --> Q1
Q1 -->|否| Reg --> Fill --> Q2
Q2 -->|否| Fill
Q2 -->|是| RegOk --> Login
Q1 -->|是| Login --> Q3
Q3 -->|否| Login
Q3 -->|是| Done''')

    render('图3-4_登录时序图', '''sequenceDiagram
actor 用户
participant 前端
participant 后端API
participant 数据库
participant JWT
用户->>前端: 1.输入账号密码
前端->>后端API: 2.POST /api/auth/login
后端API->>数据库: 3.SELECT users
数据库-->>后端API: 4.返回用户信息
后端API->>JWT: 5.bcrypt验证
JWT-->>后端API: 6.生成JWT令牌
后端API-->>前端: 7.返回token
前端-->>用户: 8.登录成功''')

    render('图3-5_创建论文程序流程图', '''flowchart TD
Start(["开始"])
Click["点击新建论文"]
Modal["弹出创建模态框"]
Fill["填写主题\\n选择模板/文献"]
Q{"信息完整？"}
Post["POST /api/papers\\n后端创建记录"]
Link["关联文献\\n插入关联表"]
Done["列表刷新\\n状态：草稿"]
Start --> Click --> Modal --> Fill --> Q
Q -->|否| Fill
Q -->|是| Post --> Link --> Done''')

    render('图3-6_Agent辅助写作流程图', '''flowchart LR
P[文献解析<br>ParseAgent]
O[大纲生成<br>OutlineAgent]
W[内容撰写<br>WriteAgent]
Po[润色优化<br>PolishAgent]
C[引用检查<br>CiteCheckAgent]
D[已完成<br>Complete]
P -->|顺序| O -->|顺序| W -->|顺序| Po -->|顺序| C -->|通过| D''')

    render('图3-7_Agent执行状态图', '''stateDiagram-v2
[*] --> 待执行: 初始
待执行 --> 执行中: 开始
执行中 --> 等待反馈: 完成
等待反馈 --> 已批准: 批准
等待反馈 --> 待执行: 驳回
等待反馈 --> 执行中: 修改
已批准 --> 完成: 下一阶段
执行中 --> 异常: API错误
异常 --> 待执行: 重试
完成 --> [*]''')

    render('图3-8_Agent辅助写作时序图', '''sequenceDiagram
actor 用户
participant 前端
participant Orchestrator
participant Agent
participant DeepSeek
participant SSE
用户->>前端: 1.点击开始
前端->>Orchestrator: 2.POST /start
Orchestrator->>Agent: 3.执行Agent
Agent->>DeepSeek: 4.调用API
DeepSeek-->>Agent: 5.返回结果
Agent->>SSE: 6.SSE推送
SSE-->>前端: 7.流式输出
前端-->>用户: 8.实时展示
用户->>前端: 9.确认/驳回
前端->>Orchestrator: 10.POST feedback
Orchestrator->>Agent: 11.下一Agent''')

    render('图3-9_文献库操作流程图', '''flowchart TD
In["进入文献库"]
Q{"操作类型？"}
In --> Q
Q -->|添加| Add["添加文献"] --> Fill["填写信息<br>上传文件"] --> Save["存入数据库"] --> Ok["完成<br>刷新列表"]
Q -->|删除/查看| Del["删除/查看"] --> Sel["选择目标"] --> Cfm["确认操作"] --> Ok''')

    render('图3-10_个人中心操作流程图', '''flowchart TD
In["进入个人中心"]
Q{"选择操作？"}
In --> Q
Q -->|修改资料| E["修改资料"] --> Ef["修改昵称/邮箱/头像<br>PUT /api/user/profile"] --> Ok["操作成功<br>页面刷新"]
Q -->|修改密码| P["修改密码"] --> Pf["输入旧密码/新密码<br>POST /api/user/password"] --> Ok''')

    render('图3-11_管理员功能结构图', '''flowchart TD
Root["管理员功能"]
Root --> C1["用户管理"] & C2["论文管理"] & C3["系统日志"] & C4["数据统计"]
C1 --> C1a["查看列表"] & C1b["管理状态"]
C2 --> C2a["查看全部"] & C2b["按状态筛选"] & C2c["删除异常"]
C3 --> C3a["查看日志"] & C3b["多维筛选"]
C4 --> C4a["用户总数"] & C4b["论文总数"]''')

    render('图3-12_管理员用户管理时序图', '''sequenceDiagram
actor 管理员
participant 管理后台
participant 后端API
participant 数据库
管理员->>管理后台: 1.进入管理页面
管理后台->>后端API: 2.GET /api/admin/users
后端API->>数据库: 3.SELECT
数据库-->>后端API: 4.返回数据
后端API-->>管理后台: 5.返回JSON
管理后台-->>管理员: 6.展示列表
管理员->>管理后台: 7.点击删除
管理后台->>后端API: 8.DELETE
后端API-->>管理员: 9.通知结果''')

    print('\n全部生成完毕！')


if __name__ == '__main__':
    main()
