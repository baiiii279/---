import { Link } from 'react-router-dom';

export default function Home() {
  return (
    <div style={{ textAlign: 'center', paddingTop: 64 }}>
      <h1 style={{ fontSize: 48, fontFamily: 'serif', color: '#0F172A', marginBottom: 16 }}>
        PaperCraft
      </h1>
      <p
        style={{
          fontSize: 22,
          color: '#475569',
          fontFamily: 'serif',
          marginBottom: 40,
        }}
      >
        多智能体论文写作助手
      </p>
      <p
        style={{
          maxWidth: 600,
          margin: '0 auto 48px',
          fontSize: 16,
          lineHeight: 1.8,
          color: '#64748B',
          fontFamily: 'sans-serif',
        }}
      >
        PaperCraft 是一款基于多智能体协作的论文写作辅助工具。
        它利用多个 AI 智能体协同工作，帮助你完成从选题、文献综述到论文撰写的全过程，
        让学术写作更高效、更专注。
      </p>
      <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
        <Link
          to="/papers"
          style={{
            padding: '14px 36px',
            background: '#2563EB',
            color: '#fff',
            textDecoration: 'none',
            borderRadius: 8,
            fontSize: 16,
            fontWeight: 600,
          }}
        >
          开始写作
        </Link>
        <Link
          to="/papers/new"
          style={{
            padding: '14px 36px',
            background: '#fff',
            color: '#2563EB',
            textDecoration: 'none',
            borderRadius: 8,
            fontSize: 16,
            fontWeight: 600,
            border: '1px solid #2563EB',
          }}
        >
          创建论文
        </Link>
      </div>
    </div>
  );
}
