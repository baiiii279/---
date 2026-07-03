import { useState, useEffect } from 'react';
import api from '../services/api';

interface Reference {
  id: number;
  title: string;
  authors: string | null;
  source: string | null;
  abstract: string | null;
  url: string | null;
  keywords: string | null;
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

const emptyForm = { title: '', authors: '', source: '', abstract: '', url: '', keywords: '' };

export default function References() {
  const [references, setReferences] = useState<Reference[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [viewingRef, setViewingRef] = useState<Reference | null>(null);

  const fetchReferences = () => {
    api.get('/user/references').then((res) => {
      setReferences(res.data);
    }).catch(() => {});
  };

  useEffect(() => {
    fetchReferences();
  }, []);

  const handleCreate = async () => {
    setMsg('');
    setError('');
    if (!form.title.trim()) {
      setError('标题为必填项');
      return;
    }
    try {
      const body: Record<string, string | null> = { title: form.title.trim() };
      if (form.authors.trim()) body.authors = form.authors.trim();
      if (form.source.trim()) body.source = form.source.trim();
      if (form.abstract.trim()) body.abstract = form.abstract.trim();
      if (form.url.trim()) body.url = form.url.trim();
      if (form.keywords.trim()) body.keywords = form.keywords.trim();

      await api.post('/user/references', body);
      setMsg('文献添加成功');
      setForm(emptyForm);
      setShowForm(false);
      fetchReferences();
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    }
  };

  const handleView = async (ref: Reference) => {
    try {
      const res = await api.get(`/user/references/${ref.id}`);
      setViewingRef(res.data);
    } catch {
      setViewingRef(ref); // fallback to list data
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除这篇文献吗？')) return;
    try {
      await api.delete(`/user/references/${id}`);
      fetchReferences();
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setMsg('');
    setError('');
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      await api.post('/user/references/upload', fd);
      setMsg(`"${file.name}" 上传成功`);
      fetchReferences();
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const inputStyle = {
    width: '100%', padding: 10, marginBottom: 12, border: '1px solid #E2E8F0',
    borderRadius: 6, boxSizing: 'border-box' as const, fontSize: 14,
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontFamily: 'serif', color: '#0F172A', margin: 0 }}>文献库</h1>
        <button
          onClick={() => { setShowForm(!showForm); setMsg(''); setError(''); }}
          style={{
            padding: '10px 24px', background: '#2563EB', color: '#fff',
            border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600,
          }}
        >
          {showForm ? '取消' : '新增文献'}
        </button>
      </div>

      {msg && <p style={{ color: '#22C55E', marginBottom: 16, fontSize: 14 }}>{msg}</p>}
      {error && <p style={{ color: '#EF4444', marginBottom: 16, fontSize: 14 }}>{error}</p>}

      {/* Upload area */}
      <div style={{
        background: '#fff', borderRadius: 8, padding: 24, marginBottom: 24,
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        border: '2px dashed #CBD5E1', textAlign: 'center',
      }}>
        <label style={{ cursor: 'pointer', display: 'block' }}>
          <input type="file" accept=".pdf,.docx,.doc,.txt" onChange={handleFileUpload} style={{ display: 'none' }} />
          <div style={{ color: uploading ? '#3B82F6' : '#64748B', fontSize: 14 }}>
            {uploading ? '正在上传并解析...' : '点击上传 PDF / Word /  TXT 文件'}
          </div>
          <div style={{ color: '#94A3B8', fontSize: 12, marginTop: 4 }}>支持 .pdf .docx .doc .txt</div>
        </label>
      </div>

      {/* Inline create form */}
      {showForm && (
        <div style={{ background: '#fff', borderRadius: 8, padding: 24, marginBottom: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ fontSize: 16, color: '#0F172A', marginBottom: 16, fontWeight: 600 }}>新增文献</h3>
          <input placeholder="标题 *" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} style={inputStyle} />
          <input placeholder="作者" value={form.authors} onChange={(e) => setForm({ ...form, authors: e.target.value })} style={inputStyle} />
          <input placeholder="来源" value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })} style={inputStyle} />
          <textarea placeholder="摘要" value={form.abstract} onChange={(e) => setForm({ ...form, abstract: e.target.value })} rows={3}
            style={{ ...inputStyle, resize: 'vertical' }} />
          <input placeholder="URL" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} style={inputStyle} />
          <input placeholder="关键词（逗号分隔）" value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} style={inputStyle} />
          <button
            onClick={handleCreate}
            style={{
              padding: '10px 24px', background: '#2563EB', color: '#fff',
              border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600,
            }}
          >
            提交
          </button>
        </div>
      )}

      {/* Table */}
      {references.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#94A3B8', background: '#fff', borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          暂无文献
        </div>
      ) : (
        <div style={{ background: '#fff', borderRadius: 8, overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr style={{ background: '#F8FAFC', borderBottom: '1px solid #E2E8F0' }}>
                <th style={{ textAlign: 'left', padding: '12px 16px', color: '#475569', fontWeight: 600, width: '30%' }}>标题</th>
                <th style={{ textAlign: 'left', padding: '12px 16px', color: '#475569', fontWeight: 600, width: '45%' }}>摘要</th>
                <th style={{ textAlign: 'left', padding: '12px 16px', color: '#475569', fontWeight: 600, width: '25%' }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {references.map((ref) => (
                <tr key={ref.id} style={{ borderBottom: '1px solid #F1F5F9' }}>
                  <td style={{ padding: '12px 16px', color: '#0F172A', fontWeight: 500, verticalAlign: 'top' }}>{ref.title}</td>
                  <td style={{ padding: '12px 16px', color: '#64748B', fontSize: 13, lineHeight: 1.6, verticalAlign: 'top' }}>
                    {(ref.abstract || ref.full_text || '').slice(0, 120)}{(ref.abstract || ref.full_text) && ((ref.abstract || ref.full_text || '').length > 120 ? '…' : '') || '暂无摘要'}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <button
                      onClick={() => handleView(ref)}
                      style={{
                        padding: '4px 14px', background: '#3B82F6', color: '#fff',
                        border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12, marginRight: 8,
                      }}
                    >
                      查看
                    </button>
                    <button
                      onClick={() => handleDelete(ref.id)}
                      style={{
                        padding: '4px 14px', background: '#EF4444', color: '#fff',
                        border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12,
                      }}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 文献详情弹窗 */}
      {viewingRef && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center',
            justifyContent: 'center', zIndex: 1000,
          }}
          onClick={() => setViewingRef(null)}
        >
          <div
            style={{
              background: '#fff', borderRadius: 12, maxWidth: 800, width: '90%',
              maxHeight: '80vh', overflow: 'auto', padding: 32, boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
              <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#0F172A', flex: 1 }}>
                {viewingRef.title}
              </h2>
              <button
                onClick={() => setViewingRef(null)}
                style={{
                  background: 'none', border: 'none', fontSize: 24, cursor: 'pointer',
                  color: '#94A3B8', padding: '0 0 0 16px', lineHeight: 1,
                }}
              >
                ✕
              </button>
            </div>

            {/* 元信息 */}
            <div style={{ display: 'flex', gap: 24, marginBottom: 20, fontSize: 13, color: '#64748B' }}>
              {viewingRef.authors && <span>作者：{viewingRef.authors}</span>}
              {viewingRef.source && <span>来源：{viewingRef.source}</span>}
              {viewingRef.keywords && <span>关键词：{viewingRef.keywords}</span>}
              <span>上传时间：{new Date(viewingRef.created_at).toLocaleDateString('zh-CN')}</span>
            </div>

            {/* 摘要 */}
            {viewingRef.abstract && (
              <div style={{ marginBottom: 20, padding: 16, background: '#F8FAFC', borderRadius: 8, borderLeft: '3px solid #3B82F6' }}>
                <h4 style={{ margin: '0 0 8px', fontSize: 14, fontWeight: 600, color: '#0F172A' }}>摘要</h4>
                <p style={{ margin: 0, fontSize: 14, color: '#475569', lineHeight: 1.8 }}>{viewingRef.abstract}</p>
              </div>
            )}

            {/* 全文 */}
            {viewingRef.full_text && (
              <div>
                <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 600, color: '#0F172A' }}>
                  全文内容（{viewingRef.full_text.length} 字符）
                </h4>
                <div style={{
                  padding: 20, background: '#F8FAFC', borderRadius: 8,
                  border: '1px solid #E2E8F0', fontSize: 14, color: '#334155',
                  lineHeight: 2, whiteSpace: 'pre-wrap', maxHeight: 400,
                  overflow: 'auto', fontFamily: 'serif',
                }}>
                  {viewingRef.full_text}
                </div>
              </div>
            )}

            {!viewingRef.abstract && !viewingRef.full_text && (
              <p style={{ color: '#94A3B8', textAlign: 'center', padding: 40 }}>
                该文献暂无详细内容
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
