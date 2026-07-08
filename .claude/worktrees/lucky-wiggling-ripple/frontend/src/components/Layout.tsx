import { Outlet, Link } from 'react-router-dom';

export default function Layout() {
  return (
    <div style={{ minHeight: '100vh', background: '#F8FAFC' }}>
      <nav style={{ background: '#0F172A', padding: '16px 48px', display: 'flex', gap: 24, alignItems: 'center' }}>
        <Link to="/" style={{ color: '#fff', fontWeight: 700, fontSize: 20, textDecoration: 'none' }}>
          PaperCraft
        </Link>
        <Link to="/papers" style={{ color: '#94A3B8', textDecoration: 'none' }}>我的论文</Link>
        <Link to="/profile" style={{ color: '#94A3B8', textDecoration: 'none' }}>个人中心</Link>
      </nav>
      <main style={{ maxWidth: 1200, margin: '0 auto', padding: '48px 24px' }}>
        <Outlet />
      </main>
    </div>
  );
}
