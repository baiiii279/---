import { Outlet, Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';

export default function Layout() {
  const navigate = useNavigate();
  const [username, setUsername] = useState(localStorage.getItem('username'));
  const [role, setRole] = useState(localStorage.getItem('role'));

  useEffect(() => {
    const check = () => {
      setUsername(localStorage.getItem('username'));
      setRole(localStorage.getItem('role'));
    };
    window.addEventListener('storage', check);
    return () => window.removeEventListener('storage', check);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    setUsername(null);
    navigate('/login');
  };

  const isAdmin = role === 'admin';

  return (
    <div style={{ minHeight: '100vh', background: '#F8FAFC' }}>
      <nav style={{
        background: 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)',
        padding: '0 clamp(16px, 4vw, 48px)',
        display: 'flex', gap: 4, alignItems: 'center', height: 56,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        position: 'sticky', top: 0, zIndex: 100,
        overflowX: 'auto',
      }}>
        <Link to="/" style={{
          color: '#fff', fontWeight: 700, fontSize: 20, textDecoration: 'none',
          marginRight: 12, letterSpacing: -0.5, whiteSpace: 'nowrap',
        }}>
          PaperCraft
        </Link>
        <Link to="/papers" style={navLinkStyle}>我的论文</Link>
        <Link to="/references" style={navLinkStyle}>文献库</Link>
        <Link to="/profile" style={navLinkStyle}>个人中心</Link>

        {isAdmin && (
          <Link to="/admin" style={{
            color: '#FCD34D', textDecoration: 'none',
            padding: '6px 12px', borderRadius: 6, fontSize: 14, fontWeight: 600,
            whiteSpace: 'nowrap',
          }}>
            管理后台
          </Link>
        )}

        <div style={{ flex: 1 }} />

        {username && (
          <>
            {isAdmin && (
              <span style={{
                background: '#FCD34D', color: '#0F172A', fontSize: 11,
                padding: '2px 8px', borderRadius: 10, fontWeight: 700,
                marginRight: 8,
              }}>
                管理员
              </span>
            )}
            <span style={{ color: '#94A3B8', fontSize: 13, whiteSpace: 'nowrap' }}>{username}</span>
            <button onClick={handleLogout} style={{
              background: 'rgba(255,255,255,0.1)', color: '#CBD5E1',
              border: '1px solid rgba(255,255,255,0.15)', borderRadius: 6,
              padding: '6px 14px', cursor: 'pointer', fontSize: 13, marginLeft: 8,
              whiteSpace: 'nowrap',
            }}>
              退出
            </button>
          </>
        )}
      </nav>
      <main style={{
        maxWidth: 1200, margin: '0 auto',
        padding: 'clamp(16px, 4vw, 32px) clamp(16px, 4vw, 24px) 64px',
      }}>
        <Outlet />
      </main>
    </div>
  );
}

const navLinkStyle: React.CSSProperties = {
  color: '#94A3B8', textDecoration: 'none',
  padding: '6px 12px', borderRadius: 6, fontSize: 14, fontWeight: 500,
  whiteSpace: 'nowrap',
};
