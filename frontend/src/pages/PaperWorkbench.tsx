import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import MDEditor from '@uiw/react-md-editor';
import api from '../services/api';
import AgentPipeline from '../components/AgentPipeline';
import FeedbackPanel from '../components/FeedbackPanel';
import useSSE from '../hooks/useSSE';

const STATUS_ACTIONS: Record<string, { agent: string; label: string }> = {
  draft: { agent: 'parse', label: '运行文献解析' },
  parsing: { agent: 'outline', label: '运行大纲生成' },
  outlining: { agent: 'write', label: '运行内容撰写' },
  writing: { agent: 'polish', label: '运行润色优化' },
  polishing: { agent: 'cite-check', label: '运行引用检查' },
};

const NEXT_STATUS: Record<string, string> = {
  draft: 'parsing',
  parsing: 'outlining',
  outlining: 'writing',
  writing: 'polishing',
  polishing: 'checking',
  checking: 'complete',
};

interface PaperData {
  id: number;
  user_id: number;
  title: string | null;
  topic: string;
  template: string;
  status: string;
  outline: string | null;
  content: string | null;
}

export default function PaperWorkbench() {
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<PaperData | null>(null);
  const [loading, setLoading] = useState(true);
  const [agentOutput, setAgentOutput] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [mdValue, setMdValue] = useState('');

  const sseUrl = id ? `/api/papers/${id}/agent/events` : '';
  const sse = useSSE(sseUrl);

  useEffect(() => {
    if (!id) return;
    api.get(`/papers/${id}`).then(res => {
      setPaper(res.data);
      setMdValue(res.data.content || '');
    }).finally(() => setLoading(false));
  }, [id]);

  const action = paper ? STATUS_ACTIONS[paper.status] : null;

  const handleRunAgent = async () => {
    if (!id || !action || running) return;
    setRunning(true);
    try {
      const res = await api.post(`/papers/${id}/agent/${action.agent}`);
      setAgentOutput(res.data.output || null);
      if (paper) {
        const nextStatus = NEXT_STATUS[paper.status];
        if (nextStatus) {
          setPaper({ ...paper, status: nextStatus });
        }
      }
    } catch {
      setAgentOutput('执行失败');
    } finally {
      setRunning(false);
    }
  };

  const handleApprove = () => {
    if (!paper) return;
    setAgentOutput(null);
    const nextStatus = NEXT_STATUS[paper.status];
    if (nextStatus) {
      setPaper({ ...paper, status: nextStatus });
    }
  };

  const handleReject = async (comment: string) => {
    if (!id) return;
    try {
      await api.post(`/papers/${id}/agent/feedback`, {
        task_id: 0,
        action: 'reject',
        comment,
      });
    } catch {
      // ignore feedback errors
    }
    setAgentOutput(null);
  };

  const handleEdit = (content: string) => {
    if (!paper) return;
    setMdValue(content);
    setAgentOutput(null);
    if (id) {
      api.put(`/papers/${id}`, { content }).catch(() => {});
    }
    const nextStatus = NEXT_STATUS[paper.status];
    if (nextStatus) {
      setPaper({ ...paper, status: nextStatus });
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 48, color: '#64748B' }}>加载中...</div>;
  }

  if (!paper) {
    return <div style={{ textAlign: 'center', padding: 48, color: '#EF4444' }}>论文不存在</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#0F172A' }}>
            {paper.title || paper.topic}
          </h1>
          <p style={{ margin: '4px 0 0', fontSize: 14, color: '#64748B' }}>
            状态: {paper.status}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {sse.status === 'connected' && (
            <span
              style={{ width: 8, height: 8, borderRadius: '50%', background: '#22C55E', display: 'inline-block' }}
              title="实时连接中"
            />
          )}
          {action && (
            <button
              onClick={handleRunAgent}
              disabled={running}
              style={{
                padding: '10px 24px', borderRadius: 6, border: 'none',
                background: running ? '#94A3B8' : '#2563EB', color: '#fff',
                fontSize: 14, fontWeight: 600,
                cursor: running ? 'not-allowed' : 'pointer',
              }}
            >
              {running ? '执行中...' : action.label}
            </button>
          )}
        </div>
      </div>

      <AgentPipeline currentStatus={paper.status} />

      <div data-color-mode="light" style={{ border: '1px solid #E2E8F0', borderRadius: 8, overflow: 'hidden', background: '#fff' }}>
        <MDEditor
          value={mdValue}
          onChange={val => setMdValue(val || '')}
          height={600}
        />
      </div>

      {agentOutput && (
        <FeedbackPanel
          output={agentOutput}
          onApprove={handleApprove}
          onReject={handleReject}
          onEdit={handleEdit}
        />
      )}
    </div>
  );
}
