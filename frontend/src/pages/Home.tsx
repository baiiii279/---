import { Link, useNavigate } from 'react-router-dom';

const features = [
  { icon: '📚', title: '文献解析', desc: '上传 PDF/Word/TXT，AI 自动提取并分析文献内容' },
  { icon: '📋', title: '大纲生成', desc: '基于文献智能生成结构化论文大纲' },
  { icon: '✍️', title: '内容撰写', desc: 'AI 按大纲逐章撰写完整论文正文' },
  { icon: '✨', title: '润色优化', desc: '学术编辑智能润色，提升语言质量' },
  { icon: '🔍', title: '引用检查', desc: '自动审计引用完整性和格式规范' },
  { icon: '📄', title: '一键导出', desc: '生成 Word 文档，格式规范即拿即用' },
];

export default function Home() {
  const navigate = useNavigate();
  const username = localStorage.getItem('username');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    navigate('/login');
  };

  return (
    <div>
      {/* Hero */}
      <div style={{
        textAlign: 'center', paddingTop: 48, paddingBottom: 64,
        background: 'linear-gradient(180deg, #EEF2FF 0%, #F8FAFC 100%)',
        borderRadius: 16, marginBottom: 48,
        position: 'relative',
      }}>
        {username && (
          <div style={{
            position: 'absolute', top: 16, right: 20,
            display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <span style={{ fontSize: 13, color: '#64748B' }}>
              {localStorage.getItem('role') === 'admin' && (
                <span style={{
                  background: '#FCD34D', color: '#0F172A', fontSize: 11,
                  padding: '2px 8px', borderRadius: 10, fontWeight: 700, marginRight: 6,
                }}>管理员</span>
              )}
              {username}
            </span>
            <button onClick={handleLogout} style={{
              background: '#fff', color: '#64748B',
              border: '1px solid #E2E8F0', borderRadius: 6,
              padding: '6px 14px', cursor: 'pointer', fontSize: 13,
            }}>
              退出登录
            </button>
          </div>
        )}
        <h1 style={{
          fontSize: 44, fontFamily: 'serif', color: '#0F172A', margin: '0 0 12px',
          letterSpacing: -1,
        }}>
          PaperCraft
        </h1>
        <p style={{ fontSize: 20, color: '#475569', fontFamily: 'serif', margin: '0 0 8px' }}>
          多智能体论文写作助手
        </p>
        <p style={{ maxWidth: 560, margin: '0 auto 36px', fontSize: 15, color: '#64748B', lineHeight: 1.8 }}>
          5 个 AI 智能体协同工作——从文献解析、大纲生成、内容撰写到润色优化和引用检查，
          只需上传参考文献，即可自动生成一篇规范完整的学术论文。
        </p>
        <div style={{ display: 'flex', gap: 14, justifyContent: 'center' }}>
          <Link to="/papers" style={btnPrimary}>开始写作</Link>
          <Link to="/references" style={btnOutline}>管理文献</Link>
        </div>
      </div>

      {/* Features grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 20, marginBottom: 48,
      }}>
        {features.map((f) => (
          <div key={f.title} style={{
            background: '#fff', borderRadius: 12, padding: '28px 24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.06)', border: '1px solid #F1F5F9',
          }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>{f.icon}</div>
            <h3 style={{ margin: '0 0 6px', fontSize: 16, fontWeight: 700, color: '#0F172A' }}>
              {f.title}
            </h3>
            <p style={{ margin: 0, fontSize: 14, color: '#64748B', lineHeight: 1.7 }}>
              {f.desc}
            </p>
          </div>
        ))}
      </div>

      {/* Workflow */}
      <div style={{
        textAlign: 'center', padding: '40px 24px', background: '#fff',
        borderRadius: 12, border: '1px solid #F1F5F9',
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, color: '#0F172A', margin: '0 0 24px' }}>
          三步完成论文
        </h2>
        <div style={{
          display: 'flex', justifyContent: 'center', gap: 32, flexWrap: 'wrap',
          fontSize: 14, color: '#475569',
        }}>
          {[
            { step: '1', text: '上传参考文献' },
            { step: '2', text: '创建论文并启动 AI' },
            { step: '3', text: '导出 Word 文档' },
          ].map((s) => (
            <div key={s.step} style={{ textAlign: 'center' }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%', background: '#EEF2FF',
                color: '#2563EB', display: 'flex', alignItems: 'center',
                justifyContent: 'center', margin: '0 auto 8px',
                fontSize: 20, fontWeight: 700,
              }}>
                {s.step}
              </div>
              <span>{s.text}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const btnPrimary: React.CSSProperties = {
  padding: '14px 36px', background: '#2563EB', color: '#fff',
  textDecoration: 'none', borderRadius: 8, fontSize: 16, fontWeight: 600,
  boxShadow: '0 4px 12px rgba(37,99,235,0.3)',
};

const btnOutline: React.CSSProperties = {
  padding: '14px 36px', background: '#fff', color: '#2563EB',
  textDecoration: 'none', borderRadius: 8, fontSize: 16, fontWeight: 600,
  border: '1px solid #CBD5E1',
};
