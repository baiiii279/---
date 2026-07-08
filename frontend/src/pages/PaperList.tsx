import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

interface PaperItem {
  id: number;
  title: string | null;
  topic: string;
  template: string;
  status: string;
  created_at: string;
}

interface Reference {
  id: number;
  title: string;
}

const STATUS_STYLES: Record<string, { color: string; bg: string; label: string }> = {
  draft:     { color: '#475569', bg: '#F1F5F9', label: '草稿' },
  parsing:   { color: '#2563EB', bg: '#EFF6FF', label: '解析中' },
  outlining: { color: '#7C3AED', bg: '#F5F3FF', label: '大纲中' },
  writing:   { color: '#D97706', bg: '#FFFBEB', label: '撰写中' },
  polishing: { color: '#8B5CF6', bg: '#F5F3FF', label: '润色中' },
  checking:  { color: '#EA580C', bg: '#FFF7ED', label: '检查中' },
  complete:  { color: '#16A34A', bg: '#F0FDF4', label: '已完成' },
};

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

export default function PaperList() {
  const navigate = useNavigate();
  const [papers, setPapers] = useState<PaperItem[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [references, setReferences] = useState<Reference[]>([]);
  const [topic, setTopic] = useState('');
  const [template, setTemplate] = useState<'course' | 'journal'>('course');
  const [selectedRefs, setSelectedRefs] = useState<number[]>([]);
  const [targetWords, setTargetWords] = useState('');
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  const fetchPapers = () => {
    api.get('/papers').then((res) => {
      setPapers(res.data);
    }).catch(() => {});
  };

  const fetchReferences = () => {
    api.get('/user/references').then((res) => {
      setReferences(res.data);
    }).catch(() => {});
  };

  useEffect(() => {
    fetchPapers();
    fetchReferences();
  }, []);

  const toggleRef = (id: number) => {
    setSelectedRefs((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleDelete = async (paperId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('确定要删除这篇论文吗？此操作不可撤销。')) return;
    try {
      await api.delete(`/papers/${paperId}`);
      fetchPapers();
    } catch {
      alert('删除失败');
    }
  };

  const handleCreate = async () => {
    setMsg('');
    setError('');
    if (!topic.trim()) {
      setError('论文主题为必填项');
      return;
    }
    try {
      const body: Record<string, unknown> = {
        topic: topic.trim(), template, reference_ids: selectedRefs,
      };
      if (targetWords.trim()) body.target_words = parseInt(targetWords.trim());
      const res = await api.post('/papers', body);
      setMsg('论文创建成功');
      setTopic('');
      setTemplate('course');
      setSelectedRefs([]);
      setShowForm(false);
      fetchPapers();
      navigate(`/papers/${res.data.id}`);
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 28, fontFamily: 'serif', color: '#0F172A', margin: 0 }}>我的论文</h1>
        <button
          onClick={() => { setShowForm(!showForm); setMsg(''); setError(''); }}
          style={{
            padding: '10px 24px', background: '#2563EB', color: '#fff',
            border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600,
          }}
        >
          {showForm ? '取消' : '创建论文'}
        </button>
      </div>

      {msg && <p style={{ color: '#22C55E', marginBottom: 16, fontSize: 14 }}>{msg}</p>}
      {error && <p style={{ color: '#EF4444', marginBottom: 16, fontSize: 14 }}>{error}</p>}

      {/* Create form */}
      {showForm && (
        <div style={{ background: '#fff', borderRadius: 8, padding: 24, marginBottom: 24, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ fontSize: 16, color: '#0F172A', marginBottom: 16, fontWeight: 600 }}>创建新论文</h3>

          <label style={{ display: 'block', fontSize: 14, color: '#475569', marginBottom: 6 }}>论文主题 *</label>
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="输入论文主题"
            style={{
              width: '100%', padding: 10, marginBottom: 16, border: '1px solid #E2E8F0',
              borderRadius: 6, boxSizing: 'border-box', fontSize: 14,
            }}
          />

          <label style={{ display: 'block', fontSize: 14, color: '#475569', marginBottom: 6 }}>模板</label>
          <select
            value={template}
            onChange={(e) => setTemplate(e.target.value as 'course' | 'journal')}
            style={{
              width: '100%', padding: 10, marginBottom: 16, border: '1px solid #E2E8F0',
              borderRadius: 6, boxSizing: 'border-box', fontSize: 14, background: '#fff',
            }}
          >
            <option value="course">课程论文</option>
            <option value="journal">期刊论文</option>
          </select>

          <label style={{ display: 'block', fontSize: 14, color: '#475569', marginBottom: 6 }}>目标字数（选填）</label>
          <input
            type="number" placeholder="5000" min="1000" max="50000"
            value={targetWords} onChange={(e) => setTargetWords(e.target.value)}
            style={{ width: '100%', padding: 10, marginBottom: 16, border: '1px solid #E2E8F0', borderRadius: 6, boxSizing: 'border-box', fontSize: 14 }}
          />

          <label style={{ display: 'block', fontSize: 14, color: '#475569', marginBottom: 6 }}>关联文献</label>
          {references.length === 0 ? (
            <p style={{ fontSize: 13, color: '#94A3B8', marginBottom: 16 }}>暂无文献，请先到文献库添加</p>
          ) : (
            <div style={{ marginBottom: 16, maxHeight: 200, overflowY: 'auto', border: '1px solid #E2E8F0', borderRadius: 6, padding: 8 }}>
              {references.map((ref) => (
                <label key={ref.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 4px', cursor: 'pointer', fontSize: 14 }}>
                  <input
                    type="checkbox"
                    checked={selectedRefs.includes(ref.id)}
                    onChange={() => toggleRef(ref.id)}
                  />
                  <span style={{ color: '#0F172A' }}>{ref.title}</span>
                </label>
              ))}
            </div>
          )}

          <button
            onClick={handleCreate}
            style={{
              padding: '10px 24px', background: '#2563EB', color: '#fff',
              border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600,
            }}
          >
            创建
          </button>
        </div>
      )}

      {/* Paper list */}
      {papers.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 48, color: '#94A3B8', background: '#fff', borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          暂无论文，点击上方"创建论文"开始写作
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {papers.map((p) => {
            const st = STATUS_STYLES[p.status] || STATUS_STYLES.draft;
            return (
              <Link
                key={p.id}
                to={`/papers/${p.id}`}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  background: '#fff', borderRadius: 8, padding: '16px 24px',
                  textDecoration: 'none', boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                  transition: 'box-shadow 0.15s',
                }}
                onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)'; }}
                onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'; }}
              >
                <div>
                  <div style={{ color: '#0F172A', fontWeight: 600, fontSize: 16, marginBottom: 4 }}>
                    {p.title || p.topic}
                  </div>
                  <div style={{ color: '#94A3B8', fontSize: 12 }}>
                    {new Date(p.created_at).toLocaleDateString('zh-CN')}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{
                    fontSize: 12, padding: '3px 12px', borderRadius: 12,
                    background: st.bg, color: st.color, fontWeight: 600, whiteSpace: 'nowrap',
                  }}>
                    {st.label}
                  </span>
                  <button
                    onClick={(e) => handleDelete(p.id, e)}
                    style={{
                      padding: '4px 12px', background: 'transparent', color: '#94A3B8',
                      border: '1px solid #E2E8F0', borderRadius: 4, cursor: 'pointer',
                      fontSize: 12, whiteSpace: 'nowrap',
                    }}
                    onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.color = '#EF4444'; (e.currentTarget as HTMLElement).style.borderColor = '#FECACA'; }}
                    onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.color = '#94A3B8'; (e.currentTarget as HTMLElement).style.borderColor = '#E2E8F0'; }}
                  >
                    删除
                  </button>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
