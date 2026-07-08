import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const validate = (): string => {
    if (username.length < 2) return '用户名至少2个字符';
    if (password.length < 6) return '密码至少6个字符';
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return '邮箱格式不正确';
    return '';
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    try {
      const body: Record<string, string> = { username, password };
      if (email) body.email = email;
      const res = await api.post('/auth/register', body);
      localStorage.setItem('token', res.data.token);
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
          : '注册失败';
      setError(detail);
    }
  };

  return (
    <div style={{ maxWidth: 400, margin: '80px auto', padding: 24 }}>
      <h1 style={{ fontSize: 28, marginBottom: 32, fontFamily: 'serif' }}>注册 PaperCraft</h1>
      {error && <p style={{ color: 'red', marginBottom: 16 }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <input
          placeholder="用户名（至少2个字符）"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{
            width: '100%',
            padding: 12,
            marginBottom: 16,
            border: '1px solid #E2E8F0',
            borderRadius: 6,
            boxSizing: 'border-box',
          }}
        />
        <input
          type="password"
          placeholder="密码（至少6个字符）"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{
            width: '100%',
            padding: 12,
            marginBottom: 16,
            border: '1px solid #E2E8F0',
            borderRadius: 6,
            boxSizing: 'border-box',
          }}
        />
        <input
          placeholder="邮箱（选填）"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            width: '100%',
            padding: 12,
            marginBottom: 16,
            border: '1px solid #E2E8F0',
            borderRadius: 6,
            boxSizing: 'border-box',
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
          注册
        </button>
      </form>
      <p style={{ marginTop: 16, textAlign: 'center' }}>
        已有账号？<a href="/login">登录</a>
      </p>
    </div>
  );
}
