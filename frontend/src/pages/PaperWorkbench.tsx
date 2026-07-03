import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import MDEditor from '@uiw/react-md-editor';
import api from '../services/api';
import AgentPipeline, { AgentNode } from '../components/AgentPipeline';
import useSSE from '../hooks/useSSE';

const AGENT_ORDER = ['parse', 'outline', 'write', 'polish', 'cite_check'];

const AGENT_LABELS: Record<string, string> = {
  parse: '文献解析',
  outline: '大纲生成',
  write: '内容撰写',
  polish: '润色优化',
  cite_check: '引用检查',
};

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

const STATUS_ORDER = ['draft', 'parsing', 'outlining', 'writing', 'polishing', 'checking', 'complete'];

function buildAgents(status: string): AgentNode[] {
  const currentIdx = STATUS_ORDER.indexOf(status);
  return AGENT_ORDER.map((key, i) => {
    if (currentIdx > i + 1) {
      return { key, label: AGENT_LABELS[key], status: 'success' as const, output: null, error: null, finishedAt: null };
    }
    if (currentIdx === i + 1) {
      return { key, label: AGENT_LABELS[key], status: 'running' as const, output: null, error: null, finishedAt: null };
    }
    return { key, label: AGENT_LABELS[key], status: 'pending' as const, output: null, error: null, finishedAt: null };
  });
}

export default function PaperWorkbench() {
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<PaperData | null>(null);
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState<AgentNode[]>([]);
  const [running, setRunning] = useState(false);
  const [mdValue, setMdValue] = useState('');

  const sseUrl = id ? `/api/papers/${id}/agent/events` : '';
  const sse = useSSE(sseUrl);

  useEffect(() => {
    if (!id) return;
    api.get(`/papers/${id}`).then(res => {
      setPaper(res.data);
      setMdValue(res.data.content || '');
      setAgents(buildAgents(res.data.status));
    }).finally(() => setLoading(false));
  }, [id]);

  const action = paper ? STATUS_ACTIONS[paper.status] : null;
  const canRunNext = !!action && !running && !['complete', 'checking'].includes(paper?.status || '');
  const isComplete = paper?.status === 'complete';

  const handleRunNext = async () => {
    if (!id || !action || running) return;
    setRunning(true);
    try {
      // Set the current agent to running
      setAgents(prev => prev.map(a =>
        a.key === action.agent ? { ...a, status: 'running' as const } : a
      ));

      const res = await api.post(`/papers/${id}/agent/${action.agent}`);
      const output = res.data.output || '';

      if (paper) {
        const nextStatus = NEXT_STATUS[paper.status];
        if (nextStatus) {
          // Mark agent as success with output
          setAgents(prev => prev.map(a =>
            a.key === action.agent
              ? { ...a, status: 'success' as const, output, finishedAt: new Date().toISOString() }
              : a
          ));
          setPaper({ ...paper, status: nextStatus });
        }
      }
    } catch {
      // Mark agent as failed
      setAgents(prev => prev.map(a =>
        a.key === action.agent
          ? { ...a, status: 'failed' as const, error: '执行失败' }
          : a
      ));
    } finally {
      setRunning(false);
    }
  };

  const handleApprove = (_agentKey: string) => {
    if (!paper || isComplete) return;
    const nextStatus = NEXT_STATUS[paper.status];
    if (nextStatus) {
      setPaper({ ...paper, status: nextStatus });
    }
  };

  const handleReject = async (_agentKey: string, comment: string) => {
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
  };

  const handleEdit = (_agentKey: string, content: string) => {
    if (!paper) return;
    setMdValue(content);
    if (id) {
      api.put(`/papers/${id}`, { content }).catch(() => {});
    }
    if (!isComplete) {
      const nextStatus = NEXT_STATUS[paper.status];
      if (nextStatus) {
        setPaper({ ...paper, status: nextStatus });
      }
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
              onClick={handleRunNext}
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

      <AgentPipeline
        agents={agents}
        onApprove={handleApprove}
        onReject={handleReject}
        onEdit={handleEdit}
        onRunNext={handleRunNext}
        running={running}
        canRunNext={canRunNext}
      />

      <div data-color-mode="light" style={{ border: '1px solid #E2E8F0', borderRadius: 8, overflow: 'hidden', background: '#fff' }}>
        <MDEditor
          value={mdValue}
          onChange={val => setMdValue(val || '')}
          height={600}
        />
      </div>
    </div>
  );
}
