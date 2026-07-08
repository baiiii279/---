import { useState, useEffect } from 'react';
import api from '../services/api';

interface StatsData {
  users: number;
  papers: number;
}

interface AdminUser {
  id: number;
  username: string;
  email: string | null;
  role: string;
  created_at: string;
}

interface AdminPaper {
  id: number;
  title: string | null;
  topic: string;
  user_id: number;
  status: string;
  created_at: string;
}

interface AdminLog {
  id: number;
  task_id: number;
  step: string;
  message: string;
  level: string;
  created_at: string;
}

interface PageResponse<T> {
  total: number;
  page: number;
  size: number;
  items: T[];
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

const STATUS_COLORS: Record<string, string> = {
  draft: '#94A3B8',
  parsing: '#3B82F6',
  outlining: '#6366F1',
  writing: '#F59E0B',
  polishing: '#A855F7',
  checking: '#F97316',
  complete: '#22C55E',
};

const STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  parsing: '解析中',
  outlining: '大纲中',
  writing: '撰写中',
  polishing: '润色中',
  checking: '检查中',
  complete: '已完成',
};

const LEVEL_COLORS: Record<string, string> = {
  info: '#3B82F6',
  warn: '#F59E0B',
  error: '#EF4444',
};

const LEVEL_LABELS: Record<string, string> = {
  info: '信息',
  warn: '警告',
  error: '错误',
};

const TH_STYLE: React.CSSProperties = {
  textAlign: 'left',
  padding: '12px 16px',
  color: '#475569',
  fontWeight: 600,
  fontSize: 14,
};

const TD_STYLE: React.CSSProperties = {
  padding: '12px 16px',
  color: '#64748B',
  fontSize: 14,
};

function pageCount(total: number): number {
  return Math.max(1, Math.ceil(total / 20));
}

export default function Admin() {
  const [activeTab, setActiveTab] = useState('stats');

  // Stats state
  const [stats, setStats] = useState<StatsData | null>(null);

  // Users state
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [usersTotal, setUsersTotal] = useState(0);
  const [usersPage, setUsersPage] = useState(1);

  // Papers state
  const [papers, setPapers] = useState<AdminPaper[]>([]);
  const [papersTotal, setPapersTotal] = useState(0);
  const [papersPage, setPapersPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [papersMsg, setPapersMsg] = useState('');
  const [papersError, setPapersError] = useState('');

  // Logs state
  const [logs, setLogs] = useState<AdminLog[]>([]);
  const [logsTotal, setLogsTotal] = useState(0);
  const [logsPage, setLogsPage] = useState(1);

  // --- Effects: fetch data when tab/page/filter changes ---

  useEffect(() => {
    if (activeTab !== 'stats') return;
    api.get<StatsData>('/admin/stats')
      .then(r => setStats(r.data))
      .catch(() => {});
  }, [activeTab]);

  useEffect(() => {
    if (activeTab !== 'users') return;
    api.get<PageResponse<AdminUser>>('/admin/users', { params: { page: usersPage, size: 20 } })
      .then(r => { setUsers(r.data.items); setUsersTotal(r.data.total); })
      .catch(() => {});
  }, [activeTab, usersPage]);

  useEffect(() => {
    if (activeTab !== 'papers') return;
    const params: Record<string, string | number> = { page: papersPage, size: 20 };
    if (statusFilter) params.status = statusFilter;
    api.get<PageResponse<AdminPaper>>('/admin/papers', { params })
      .then(r => { setPapers(r.data.items); setPapersTotal(r.data.total); })
      .catch(() => {});
  }, [activeTab, papersPage, statusFilter]);

  useEffect(() => {
    if (activeTab !== 'logs') return;
    api.get<PageResponse<AdminLog>>('/admin/logs', { params: { page: logsPage, size: 20 } })
      .then(r => { setLogs(r.data.items); setLogsTotal(r.data.total); })
      .catch(() => {});
  }, [activeTab, logsPage]);

  // --- Handlers ---

  const handleDeletePaper = async (id: number) => {
    if (!confirm('确定要删除这篇论文吗？')) return;
    setPapersMsg('');
    setPapersError('');
    try {
      await api.delete(`/admin/papers/${id}`);
      setPapersMsg('论文已删除');
      const params: Record<string, string | number> = { page: papersPage, size: 20 };
      if (statusFilter) params.status = statusFilter;
      const res = await api.get<PageResponse<AdminPaper>>('/admin/papers', { params });
      setPapers(res.data.items);
      setPapersTotal(res.data.total);
    } catch (err: unknown) {
      setPapersError(getErrorMessage(err));
    }
  };

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value);
    setPapersPage(1);
  };

  // --- Render helpers ---

  const renderTabButton = (tabKey: string, label: string) => (
    <button
      onClick={() => setActiveTab(tabKey)}
      style={{
        padding: '10px 24px',
        border: 'none',
        background: activeTab === tabKey ? '#2563EB' : 'transparent',
        color: activeTab === tabKey ? '#fff' : '#64748B',
        cursor: 'pointer',
        fontSize: 14,
        fontWeight: 600,
        borderRadius: 6,
      }}
    >
      {label}
    </button>
  );

  const renderPagination = (
    page: number,
    total: number,
    setPage: (p: number) => void,
  ) => {
    const totalPages = pageCount(total);
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 16, gap: 8, padding: '0 16px 16px' }}>
        <button
          disabled={page <= 1}
          onClick={() => setPage(page - 1)}
          style={{
            padding: '6px 14px',
            border: '1px solid #E2E8F0',
            background: page <= 1 ? '#F1F5F9' : '#fff',
            color: page <= 1 ? '#94A3B8' : '#0F172A',
            cursor: page <= 1 ? 'default' : 'pointer',
            borderRadius: 4,
            fontSize: 13,
          }}
        >
          上一页
        </button>
        <span style={{ padding: '6px 12px', fontSize: 13, color: '#475569' }}>
          第 {page} / {totalPages} 页 (共 {total} 条)
        </span>
        <button
          disabled={page >= totalPages}
          onClick={() => setPage(page + 1)}
          style={{
            padding: '6px 14px',
            border: '1px solid #E2E8F0',
            background: page >= totalPages ? '#F1F5F9' : '#fff',
            color: page >= totalPages ? '#94A3B8' : '#0F172A',
            cursor: page >= totalPages ? 'default' : 'pointer',
            borderRadius: 4,
            fontSize: 13,
          }}
        >
          下一页
        </button>
      </div>
    );
  };

  const renderStatsTab = () => (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{
        flex: 1, background: '#fff', borderRadius: 8, padding: 32, textAlign: 'center',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}>
        <div style={{ fontSize: 36, fontWeight: 700, color: '#2563EB' }}>
          {stats?.users ?? '-'}
        </div>
        <div style={{ fontSize: 14, color: '#64748B', marginTop: 8 }}>用户总数</div>
      </div>
      <div style={{
        flex: 1, background: '#fff', borderRadius: 8, padding: 32, textAlign: 'center',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}>
        <div style={{ fontSize: 36, fontWeight: 700, color: '#2563EB' }}>
          {stats?.papers ?? '-'}
        </div>
        <div style={{ fontSize: 14, color: '#64748B', marginTop: 8 }}>论文总数</div>
      </div>
    </div>
  );

  const renderUsersTab = () => (
    <div style={{
      background: '#fff', borderRadius: 8, overflow: 'hidden',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr style={{ background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
            <th style={TH_STYLE}>ID</th>
            <th style={TH_STYLE}>用户名</th>
            <th style={TH_STYLE}>邮箱</th>
            <th style={TH_STYLE}>角色</th>
            <th style={TH_STYLE}>创建时间</th>
          </tr>
        </thead>
        <tbody>
          {users.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ textAlign: 'center', padding: 32, color: '#94A3B8' }}>暂无数据</td>
            </tr>
          ) : (
            users.map((u, i) => (
              <tr key={u.id} style={{
                background: i % 2 === 0 ? '#fff' : '#F8FAFC',
                borderBottom: '1px solid #F1F5F9',
              }}>
                <td style={TD_STYLE}>{u.id}</td>
                <td style={{ ...TD_STYLE, fontWeight: 500, color: '#0F172A' }}>{u.username}</td>
                <td style={TD_STYLE}>{u.email || '-'}</td>
                <td style={TD_STYLE}>
                  <span style={{
                    fontSize: 12, padding: '2px 10px', borderRadius: 12,
                    background: u.role === 'admin' ? '#2563EB' : '#94A3B8', color: '#fff',
                  }}>
                    {u.role === 'admin' ? '管理员' : '用户'}
                  </span>
                </td>
                <td style={TD_STYLE}>{new Date(u.created_at).toLocaleDateString('zh-CN')}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
      {renderPagination(usersPage, usersTotal, setUsersPage)}
    </div>
  );

  const renderPapersTab = () => (
    <div>
      {/* Filter row */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
        <label style={{ fontSize: 14, color: '#475569' }}>状态筛选：</label>
        <select
          value={statusFilter}
          onChange={(e) => handleStatusFilterChange(e.target.value)}
          style={{
            padding: '8px 12px', border: '1px solid #E2E8F0', borderRadius: 6, fontSize: 14,
            background: '#fff', color: '#0F172A',
          }}
        >
          <option value="">全部</option>
          <option value="draft">草稿</option>
          <option value="parsing">解析中</option>
          <option value="outlining">大纲中</option>
          <option value="writing">撰写中</option>
          <option value="polishing">润色中</option>
          <option value="checking">检查中</option>
          <option value="complete">已完成</option>
        </select>
      </div>

      {papersMsg && <p style={{ color: '#22C55E', marginBottom: 12, fontSize: 14 }}>{papersMsg}</p>}
      {papersError && <p style={{ color: '#EF4444', marginBottom: 12, fontSize: 14 }}>{papersError}</p>}

      <div style={{
        background: '#fff', borderRadius: 8, overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
              <th style={TH_STYLE}>ID</th>
              <th style={TH_STYLE}>标题</th>
              <th style={TH_STYLE}>用户ID</th>
              <th style={TH_STYLE}>状态</th>
              <th style={TH_STYLE}>创建时间</th>
              <th style={TH_STYLE}>操作</th>
            </tr>
          </thead>
          <tbody>
            {papers.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: 32, color: '#94A3B8' }}>暂无数据</td>
              </tr>
            ) : (
              papers.map((p, i) => (
                <tr key={p.id} style={{
                  background: i % 2 === 0 ? '#fff' : '#F8FAFC',
                  borderBottom: '1px solid #F1F5F9',
                }}>
                  <td style={TD_STYLE}>{p.id}</td>
                  <td style={{
                    ...TD_STYLE, fontWeight: 500, color: '#0F172A', maxWidth: 300,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const,
                  }}>
                    {p.title || p.topic}
                  </td>
                  <td style={TD_STYLE}>{p.user_id}</td>
                  <td style={TD_STYLE}>
                    <span style={{
                      fontSize: 12, padding: '2px 10px', borderRadius: 12,
                      background: STATUS_COLORS[p.status] || '#94A3B8', color: '#fff',
                    }}>
                      {STATUS_LABELS[p.status] || p.status}
                    </span>
                  </td>
                  <td style={TD_STYLE}>{new Date(p.created_at).toLocaleDateString('zh-CN')}</td>
                  <td style={TD_STYLE}>
                    <button
                      onClick={() => handleDeletePaper(p.id)}
                      style={{
                        padding: '4px 14px', background: '#EF4444', color: '#fff',
                        border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12,
                      }}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        {renderPagination(papersPage, papersTotal, setPapersPage)}
      </div>
    </div>
  );

  const renderLogsTab = () => (
    <div style={{
      background: '#fff', borderRadius: 8, overflow: 'hidden',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr style={{ background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
            <th style={TH_STYLE}>ID</th>
            <th style={TH_STYLE}>任务ID</th>
            <th style={TH_STYLE}>步骤</th>
            <th style={TH_STYLE}>消息</th>
            <th style={TH_STYLE}>级别</th>
            <th style={TH_STYLE}>时间</th>
          </tr>
        </thead>
        <tbody>
          {logs.length === 0 ? (
            <tr>
              <td colSpan={6} style={{ textAlign: 'center', padding: 32, color: '#94A3B8' }}>暂无数据</td>
            </tr>
          ) : (
            logs.map((log, i) => (
              <tr key={log.id} style={{
                background: i % 2 === 0 ? '#fff' : '#F8FAFC',
                borderBottom: '1px solid #F1F5F9',
              }}>
                <td style={TD_STYLE}>{log.id}</td>
                <td style={TD_STYLE}>{log.task_id}</td>
                <td style={TD_STYLE}>{log.step}</td>
                <td style={{
                  ...TD_STYLE, maxWidth: 350,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const,
                }}>
                  {log.message}
                </td>
                <td style={TD_STYLE}>
                  <span style={{
                    fontSize: 12, padding: '2px 10px', borderRadius: 12,
                    background: LEVEL_COLORS[log.level] || '#94A3B8', color: '#fff',
                  }}>
                    {LEVEL_LABELS[log.level] || log.level}
                  </span>
                </td>
                <td style={TD_STYLE}>{new Date(log.created_at).toLocaleString('zh-CN')}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
      {renderPagination(logsPage, logsTotal, setLogsPage)}
    </div>
  );

  // --- Main render ---

  return (
    <div>
      <h1 style={{ fontSize: 28, fontFamily: 'serif', color: '#0F172A', marginBottom: 24 }}>
        管理后台
      </h1>

      {/* Tab navigation */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {renderTabButton('stats', '概览')}
        {renderTabButton('users', '用户管理')}
        {renderTabButton('papers', '论文管理')}
        {renderTabButton('logs', '系统日志')}
      </div>

      {/* Tab content */}
      {activeTab === 'stats' && renderStatsTab()}
      {activeTab === 'users' && renderUsersTab()}
      {activeTab === 'papers' && renderPapersTab()}
      {activeTab === 'logs' && renderLogsTab()}
    </div>
  );
}
