"""从 .docx 模板文件中提取格式规则"""
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn


def parse_template(file_path: str) -> dict:
    """解析docx文件，提取格式规则"""
    doc = Document(file_path)
    rules = {}

    # 1. 页面设置
    section = doc.sections[0]
    rules['page'] = {
        'top_margin_cm': round(section.top_margin.cm, 2),
        'bottom_margin_cm': round(section.bottom_margin.cm, 2),
        'left_margin_cm': round(section.left_margin.cm, 2),
        'right_margin_cm': round(section.right_margin.cm, 2),
    }

    # 2. 默认样式
    style = doc.styles['Normal']
    font = style.font
    pf = style.paragraph_format
    rules['default'] = {
        'font_name': font.name,
        'font_size_pt': round(font.size.pt) if font.size else 12,
        'bold': font.bold,
        'first_line_indent_cm': round(pf.first_line_indent.cm, 2) if pf.first_line_indent else 0,
        'line_spacing': pf.line_spacing,
        'space_before_pt': round(pf.space_before.pt) if pf.space_before else 0,
        'space_after_pt': round(pf.space_after.pt) if pf.space_after else 0,
    }

    # 3. 标题样式
    for level in ['Heading 1', 'Heading 2', 'Heading 3']:
        try:
            hs = doc.styles[level]
            hf = hs.font
            hp = hs.paragraph_format
            # 获取中文字体名
            rpr = hs.element.find(qn('w:rPr'))
            ea_font = None
            if rpr is not None:
                rFonts = rpr.find(qn('w:rFonts'))
                if rFonts is not None:
                    ea_font = rFonts.get(qn('w:eastAsia'))

            rules[level.replace(' ', '_').lower()] = {
                'font_name': hf.name,
                'east_asian_font': ea_font,
                'font_size_pt': round(hf.size.pt) if hf.size else 16,
                'bold': hf.bold,
                'alignment': str(hp.alignment) if hp.alignment else 'LEFT',
            }
        except KeyError:
            continue

    return rules


def rules_to_text(rules: dict) -> str:
    """将结构化规则转为自然语言文本"""
    lines = []
    d = rules.get('default', {})
    lines.append(f"默认样式: {d.get('font_name', '宋体')}, {d.get('font_size_pt', 12)}pt")
    if d.get('first_line_indent_cm'):
        lines.append(f"首行缩进: {d['first_line_indent_cm']}cm")
    if d.get('line_spacing'):
        lines.append(f"行距: 固定值{round(d['line_spacing'])}磅")
    lines.append(f"段前: {d.get('space_before_pt', 0)}pt, 段后: {d.get('space_after_pt', 0)}pt")

    p = rules.get('page', {})
    lines.append(f"页边距: 上{p.get('top_margin_cm', 2.54)}cm 下{p.get('bottom_margin_cm', 2.54)}cm 左{p.get('left_margin_cm', 3.18)}cm 右{p.get('right_margin_cm', 3.18)}cm")

    for level_key in ['heading_1', 'heading_2', 'heading_3']:
        h = rules.get(level_key)
        if h:
            label = {'heading_1': '一级标题', 'heading_2': '二级标题', 'heading_3': '三级标题'}[level_key]
            font_name = h.get('east_asian_font') or h.get('font_name', '黑体')
            lines.append(f"{label}: {font_name}, {h.get('font_size_pt', 16)}pt, {'加粗' if h.get('bold') else '常规'}, {h.get('alignment', 'LEFT')}")

    return '\n'.join(lines)


def get_default_rules() -> str:
    """返回嘉庚学院默认格式规则（厦门大学嘉庚学院本科生毕业论文格式）"""
    return """默认样式: 宋体, 12pt(小四), 首行缩进2字符, 行距固定值20磅
页边距: 上2.54cm 下2.54cm 左3.18cm 右3.18cm
论文题目: 三号黑体(16pt), 居中, 加粗
一级标题(章标题如引言、结论): 小三号黑体(15pt), 居中, 加粗
二级标题(节标题): 四号黑体(14pt), 左对齐, 加粗
三级标题: 小四号宋体(12pt), 左对齐
摘要标题: 四号黑体加方括号[摘要], 左顶格, 标题后空一格接内容
摘要内容: 小四号宋体(12pt), 内容与关键词之间空一行
关键词标题: 四号黑体加方括号[关键词], 左顶格, 标题后空一格接关键词
关键词内容: 小四号宋体(12pt), 3-5个关键词, 词间空两格
参考文献标题: 四号黑体(14pt), 居中
参考文献内容: 五号宋体(10.5pt), 左顶格, 按GB/T 7714格式著录, 不少于10条
引用格式: 正文中引用以[1][2]方括号上标标注, 按出现顺序连续编号
正文: 小四号宋体(12pt), 每段首行缩进2字符, 行距固定值20磅"""
