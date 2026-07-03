import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import MDEditor from '@uiw/react-md-editor';
import api from '../services/api';
import AgentPipeline, { AgentNode } from '../components/AgentPipeline';
import useSSE from '../hooks/useSSE';

const AGENTS: { key: string; label: string }[] = [
  { key: 'parse', label: '文献解析' },
  { key: 'outline', label: '大纲生成' },
  { key: 'write', label: '内容撰写' },
  { key: 'polish', label: '润色优化' },
  { key: 'cite_check', label: '引用检查' },
];

const NEXT_STATUS: Record<string, string> = {
  draft: 'parsing',
  parsing: 'outlining',
  outlining: 'writing',
  writing: 'polishing',
  polishing: 'checking',
  checking: 'complete',
};

function getAgentIndex(status: string): number {
  const map: Record<string, number> = {
    draft: 0, parsing: 1, outlining: 2, writing: 3, polishing: 4, checking: 5, complete: 6,
  };
  return map[status] ?? 0;
}

function initAgentStates(status: string): AgentNode[] {
  const completedIndex = getAgentIndex(status);
  return AGENTS.map((a, i) => ({
    ...a,
    status: i < completedIndex ? ('success' as const) : ('pending' as const),
    output: null,
    error: null,
    finishedAt: null,
  }));
}

export default function PaperWorkbench() {
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [agentStates, setAgentStates] = useState<AgentNode[]>(AGENTS.map(a => ({
    ...a, status: 'pending' as const, output: null, error: null, finishedAt: null,
  })));
  const [running, setRunning] = useState(false);
  const [mdValue, setMdValue] = useState('');

  const sseUrl = id ? `/api/papers/${id}/agent/events` : '';

  useSSE(sseUrl, {
    onAgentStart: (agent) => {
      setRunning(true);
      setAgentStates(prev => prev.map(a =>
        a.key === agent ? { ...a, status: 'running' } : a
      ));
    },
    onAgentComplete: (agent, output) => {
      setAgentStates(prev => prev.map(a =>
        a.key === agent
          ? { ...a, status: 'success', output, finishedAt: new Date().toISOString() }
          : a
      ));
      setRunning(false);
      // Auto-fill content/outline into editor
      if (agent === 'outline' || agent === 'write' || agent === 'polish') {
        setMdValue(output);
      }
    },
    onAgentError: (agent, error) => {
      setAgentStates(prev => prev.map(a =>
        a.key === agent ? { ...a, status: 'failed', error } : a
      ));
      setRunning(false);
    },
    onPipelineComplete: () => {
      setRunning(false);
    },
  });

  useEffect(() => {
    if (!id) return;
    api.get(`/papers/${id}`).then(res => {
      setPaper(res.data);
      setMdValue(res.data.content || '');
      setAgentStates(initAgentStates(res.data.status));
    }).finally(() => setLoading(false));
  }, [id]);

  const completedIndex = agentStates.filter(a => a.status === 'success').length;
  const currentAgent = agentStates.find(a => a.status === 'pending');
  const canRunNext = !!currentAgent;

  const handleRunAgent = async () => {
    if (!id || !currentAgent || running) return;
    try {
      await api.post(`/papers/${id}/agent/${currentAgent.key.replace('_', '-')}/run`);
    } catch {
      setAgentStates(prev => prev.map(a =>
        a.key === currentAgent.key ? { ...a, status: 'failed', error: '启动失败' } : a
      ));
      setRunning(false);
    }
  };

  const handleApprove = (agentKey: string) => {
    if (!paper || !id) return;
    const nextStatus = NEXT_STATUS[paper.status];
    if (nextStatus) {
      setPaper({ ...paper, status: nextStatus });
    }
  };

  const handleReject = async (agentKey: string, comment: string) => {
    if (!id) return;
    try {
      await api.post(`/papers/${id}/agent/feedback`, {
        task_id: 0, action: 'reject', comment,
      });
    } catch { /* ignore */ }
  };

  const handleEdit = async (agentKey: string, content: string) => {
    if (!paper || !id) return;
    setMdValue(content);
    api.put(`/papers/${id}`, { content }).catch(() => {});
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
      </div>

      <AgentPipeline
        agents={agentStates}
        onApprove={handleApprove}
        onReject={handleReject}
        onEdit={handleEdit}
        onRunNext={handleRunAgent}
        running={running}
        canRunNext={canRunNext && !running}
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
