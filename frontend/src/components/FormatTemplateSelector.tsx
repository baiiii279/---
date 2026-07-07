import { useState, useEffect } from 'react';
import api from '../services/api';

interface Template {
  id: number;
  name: string;
  is_default: boolean;
  created_at: string;
}

interface Props {
  selectedId: number | null;
  onSelect: (id: number | null) => void;
}

export default function FormatTemplateSelector({ selectedId, onSelect }: Props) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<Template[]>('/format-templates')
      .then(r => {
        setTemplates(r.data);
        if (!selectedId && r.data.length > 0) {
          const def = r.data.find((t: Template) => t.is_default);
          onSelect(def ? def.id : r.data[0].id);
        }
      })
      .catch(() => {});
  }, []);

  const handleUpload = async () => {
    if (!uploadFile || !uploadName.trim()) return;
    setUploading(true);
    setError('');
    const form = new FormData();
    form.append('file', uploadFile);
    form.append('name', uploadName.trim());
    try {
      const res = await api.post('/format-templates/upload', form);
      setTemplates(prev => [...prev, res.data]);
      onSelect(res.data.id);
      setShowUpload(false);
      setUploadName('');
      setUploadFile(null);
    } catch (err: unknown) {
      const detail = err && typeof err === 'object' && 'response' in err
        ? String((err as any).response?.data?.detail || '上传失败') : '上传失败';
      setError(detail);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ fontSize: 14, color: '#475569', fontWeight: 600, display: 'block', marginBottom: 8 }}>
        格式模板
      </label>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <select
          value={selectedId ?? ''}
          onChange={(e) => onSelect(e.target.value ? Number(e.target.value) : null)}
          style={{
            padding: '8px 12px', border: '1px solid #E2E8F0', borderRadius: 6,
            fontSize: 14, background: '#fff', color: '#0F172A', flex: 1,
          }}
        >
          {templates.map(t => (
            <option key={t.id} value={t.id}>
              {t.name} {t.is_default ? '(默认)' : ''}
            </option>
          ))}
        </select>
        <button
          onClick={() => setShowUpload(!showUpload)}
          style={{
            padding: '8px 16px', background: '#2563EB', color: '#fff',
            border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, whiteSpace: 'nowrap',
          }}
        >
          上传模板
        </button>
      </div>

      {showUpload && (
        <div style={{ marginTop: 12, padding: 16, background: '#F8FAFC', borderRadius: 8, border: '1px solid #E2E8F0' }}>
          <input
            placeholder="模板名称"
            value={uploadName}
            onChange={(e) => setUploadName(e.target.value)}
            style={{ width: '100%', padding: 8, marginBottom: 8, border: '1px solid #E2E8F0', borderRadius: 4, fontSize: 13, boxSizing: 'border-box' }}
          />
          <input
            type="file" accept=".docx"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            style={{ fontSize: 13, marginBottom: 8, display: 'block' }}
          />
          {error && <p style={{ color: '#EF4444', fontSize: 12, margin: '0 0 8px' }}>{error}</p>}
          <button
            onClick={handleUpload}
            disabled={uploading || !uploadFile || !uploadName.trim()}
            style={{
              padding: '6px 16px', background: uploading ? '#94A3B8' : '#2563EB', color: '#fff',
              border: 'none', borderRadius: 4, cursor: uploading ? 'default' : 'pointer', fontSize: 13,
            }}
          >
            {uploading ? '解析中...' : '上传并解析'}
          </button>
        </div>
      )}
    </div>
  );
}
