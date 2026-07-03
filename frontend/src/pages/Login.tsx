import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/auth/login', { username, password });
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('username', res.data.username || username);
      navigate('/');
    } catch (err: unknown) {
      const detail =
        err != null &&
        typeof err === 'object' &&
        'response' in err &&
        err.response != null &&
        typeof err.response === 'object' &&
        'data' in err.response &&
        err.response.data != null &&
        typeof err.response.data === 'object' &&
        'detail' in err.response.data
          ? String(err.response.data.detail)
          : '登录失败';
      setError(detail);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', padding: 24 }}>
      <h1 style={{ fontSize: 28, marginBottom: 32, fontFamily: 'serif' }}>登录 PaperCraft</h1>
      {error && <p style={{ color: 'red', marginBottom: 16 }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          placeholder="用户名" autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{
            width: '100%', padding: 12, marginBottom: 16,
            border: '1px solid #E2E8F0', borderRadius: 6, boxSizing: 'border-box',
          }}
        />
        <input
          type="password" placeholder="密码" autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            width: '100%', padding: 12, marginBottom: 16,
            border: '1px solid #E2E8F0', borderRadius: 6, boxSizing: 'border-box',
          }}
        />
        <button
          type="submit"
          style={{
            width: '100%',
            padding: 12,
            background: '#0F172A',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            cursor: 'pointer',
          }}
        >
          登录
        </button>
      </form>
      <p style={{ marginTop: 16, textAlign: 'center' }}>
        没有账号？<a href="/register">注册</a>
      </p>
    </div>
  );
}
