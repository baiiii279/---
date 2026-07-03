import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface UserInfo {
  id: number;
  username: string;
  email: string | null;
  role: string;
  avatar: string | null;
  created_at: string;
}

interface PaperItem {
  id: number;
  title: string | null;
  topic: string;
  status: string;
  created_at: string;
}

function getErrorMessage(err: unknown): string {
  if (err != null && typeof err === 'object' && 'response' in err) {
    const resp = (err as { response?: unknown }).response;
    if (resp != null && typeof resp === 'object' && 'data' in resp) {
      const data = (resp as { data?: unknown }).data;
      if (data != null && typeof data === 'object' && 'detail' in data) {
        return String((data as { detail: unknown }).detail);
      }
    }
  }
  return '操作失败';
}

export default function Profile() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [recentPapers, setRecentPapers] = useState<PaperItem[]>([]);
  const [email, setEmail] = useState('');
  const [profileMsg, setProfileMsg] = useState('');
  const [profileError, setProfileError] = useState('');

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [pwdMsg, setPwdMsg] = useState('');
  const [pwdError, setPwdError] = useState('');

  useEffect(() => {
    api.get('/auth/me').then((res) => {
      const u: UserInfo = res.data;
      setUser(u);
      setEmail(u.email ?? '');
    }).catch(() => {});

    api.get('/papers').then((res) => {
      const papers: PaperItem[] = res.data;
      setRecentPapers(papers.slice(0, 5));
    }).catch(() => {});
  }, []);

  const handleUpdateProfile = async () => {
    setProfileMsg('');
    setProfileError('');
    try {
      await api.put('/user/profile', { email: email || null });
      setProfileMsg('个人信息更新成功');
    } catch (err: unknown) {
      setProfileError(getErrorMessage(err));
    }
  };

  const handleChangePassword = async () => {
    setPwdMsg('');
    setPwdError('');
    if (newPassword.length < 6) {
      setPwdError('新密码至少 6 个字符');
      return;
    }
    try {
      await api.put('/user/password', { old_password: oldPassword, new_password: newPassword });
      setPwdMsg('密码修改成功');
      setOldPassword('');
      setNewPassword('');
    } catch (err: unknown) {
      setPwdError(getErrorMessage(err));
    }
  };

  if (!user) {
    return <div style={{ textAlign: 'center', padding: 48, color: '#64748B' }}>加载中...</div>;
  }

  const statusColors: Record<string, string> = {
    draft: '#94A3B8', parsing: '#3B82F6', outlining: '#6366F1',
    writing: '#F59E0B', polishing: '#A855F7', checking: '#F97316', complete: '#22C55E',
  };
  const statusLabels: Record<string, string> = {
    draft: '草稿', parsing: '解析中', outlining: '大纲中',
    writing: '撰写中', polishing: '润色中', checking: '检查中', complete: '已完成',
  };

  return (
    <div>
      <h1 style={{ fontSize: 28, fontFamily: 'serif', color: '#0F172A', marginBottom: 32 }}>
        个人中心
      </h1>

      <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
        {/* User info card */}
        <div style={{ flex: 1, minWidth: 300, background: '#fff', borderRadius: 8, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: 18, color: '#0F172A', marginBottom: 20, fontWeight: 600 }}>基本信息</h2>
          <div style={{ marginBottom: 12 }}>
            <span style={{ color: '#64748B', fontSize: 14 }}>用户名：</span>
            <span style={{ color: '#0F172A', fontWeight: 500 }}>{user.username}</span>
          </div>
          <div style={{ marginBottom: 12 }}>
            <span style={{ color: '#64748B', fontSize: 14 }}>邮箱：</span>
            <span style={{ color: '#0F172A' }}>{user.email || '未设置'}</span>
          </div>
          <div style={{ marginBottom: 12 }}>
            <span style={{ color: '#64748B', fontSize: 14 }}>角色：</span>
            <span style={{ color: '#0F172A' }}>{user.role === 'admin' ? '管理员' : '用户'}</span>
          </div>
          <div style={{ marginBottom: 12 }}>
            <span style={{ color: '#64748B', fontSize: 14 }}>注册时间：</span>
            <span style={{ color: '#0F172A' }}>{new Date(user.created_at).toLocaleDateString('zh-CN')}</span>
          </div>

          <Link
            to="/references"
            style={{
              display: 'inline-block', marginTop: 16, padding: '10px 24px',
              background: '#2563EB', color: '#fff', textDecoration: 'none',
              borderRadius: 6, fontSize: 14, fontWeight: 600,
            }}
          >
            我的文献库
          </Link>
        </div>

        {/* Edit profile */}
        <div style={{ flex: 1, minWidth: 300, background: '#fff', borderRadius: 8, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: 18, color: '#0F172A', marginBottom: 20, fontWeight: 600 }}>修改资料</h2>
          {profileMsg && <p style={{ color: '#22C55E', marginBottom: 12, fontSize: 14 }}>{profileMsg}</p>}
          {profileError && <p style={{ color: '#EF4444', marginBottom: 12, fontSize: 14 }}>{profileError}</p>}
          <label style={{ display: 'block', fontSize: 14, color: '#475569', marginBottom: 6 }}>邮箱</label>
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{
              width: '100%', padding: 10, marginBottom: 16, border: '1px solid #E2E8F0',
              borderRadius: 6, boxSizing: 'border-box', fontSize: 14,
            }}
          />
          <button
            onClick={handleUpdateProfile}
            style={{
              padding: '10px 24px', background: '#2563EB', color: '#fff',
              border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600,
            }}
          >
            保存
          </button>
        </div>

        {/* Change password */}
        <form onSubmit={(e) => { e.preventDefault(); handleChangePassword(); }} style={{ flex: 1, minWidth: 300, background: '#fff', borderRadius: 8, padding: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: 18, color: '#0F172A', marginBottom: 20, fontWeight: 600 }}>修改密码</h2>
          {pwdMsg && <p style={{ color: '#22C55E', marginBottom: 12, fontSize: 14 }}>{pwdMsg}</p>}
          {pwdError && <p style={{ color: '#EF4444', marginBottom: 12, fontSize: 14 }}>{pwdError}</p>}
          <label style={{ display: 'block', fontSize: 14, color: '#475569', marginBottom: 6 }}>原密码</label>
          <input
            type="password" autoComplete="current-password"
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            style={{
              width: '100%', padding: 10, marginBottom: 16, border: '1px solid #E2E8F0',
              borderRadius: 6, boxSizing: 'border-box', fontSize: 14,
            }}
          />
          <label style={{ display: 'block', fontSize: 14, color: '#475569', marginBottom: 6 }}>新密码</label>
          <input
            type="password" autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            style={{
              width: '100%', padding: 10, marginBottom: 16, border: '1px solid #E2E8F0',
              borderRadius: 6, boxSizing: 'border-box', fontSize: 14,
            }}
          />
          <button
            type="submit"
            style={{
              padding: '10px 24px', background: '#2563EB', color: '#fff',
              border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600,
            }}
          >
            修改密码
          </button>
        </form>
      </div>

      {/* Recent papers */}
      <div style={{ background: '#fff', borderRadius: 8, padding: 24, marginTop: 32, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <h2 style={{ fontSize: 18, color: '#0F172A', marginBottom: 20, fontWeight: 600 }}>最近论文</h2>
        {recentPapers.length === 0 ? (
          <p style={{ color: '#94A3B8', fontSize: 14 }}>暂无论文</p>
        ) : (
          <div>
            {recentPapers.map((p) => (
              <Link
                key={p.id}
                to={`/papers/${p.id}`}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '12px 0', borderBottom: '1px solid #F1F5F9', textDecoration: 'none',
                }}
              >
                <span style={{ color: '#0F172A', fontWeight: 500, fontSize: 14 }}>
                  {p.title || p.topic}
                </span>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <span style={{
                    fontSize: 12, padding: '2px 10px', borderRadius: 12,
                    background: statusColors[p.status] || '#94A3B8', color: '#fff',
                  }}>
                    {statusLabels[p.status] || p.status}
                  </span>
                  <span style={{ color: '#94A3B8', fontSize: 12 }}>
                    {new Date(p.created_at).toLocaleDateString('zh-CN')}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
