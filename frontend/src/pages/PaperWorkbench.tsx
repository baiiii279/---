import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import MDEditor from '@uiw/react-md-editor';
import api from '../services/api';
import AgentPipeline from '../components/AgentPipeline';
import type { AgentNode } from '../components/AgentPipeline';
import StreamPanel, { appendToken, clearStream } from '../components/StreamPanel';
import useSSE from '../hooks/useSSE';

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

const AGENTS: { key: string; label: string }[] = [
  { key: 'parse', label: '文献解析' },
  { key: 'outline', label: '大纲生成' },
  { key: 'write', label: '内容撰写' },
  { key: 'polish', label: '润色优化' },
  { key: 'cite_check', label: '引用检查' },
];

const STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  draft: { label: '草稿', color: '#64748B', bg: '#F1F5F9' },
  parsing: { label: '解析中', color: '#2563EB', bg: '#EFF6FF' },
  outlining: { label: '大纲生成中', color: '#7C3AED', bg: '#F5F3FF' },
  writing: { label: '撰写中', color: '#D97706', bg: '#FFFBEB' },
  polishing: { label: '润色中', color: '#059669', bg: '#ECFDF5' },
  checking: { label: '检查中', color: '#DC2626', bg: '#FEF2F2' },
  complete: { label: '已完成', color: '#16A34A', bg: '#F0FDF4' },
};

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
  const [paper, setPaper] = useState<PaperData | null>(null);
  const [loading, setLoading] = useState(true);
  const [agentStates, setAgentStates] = useState<AgentNode[]>(AGENTS.map(a => ({
    ...a, status: 'pending' as const, output: null, error: null, finishedAt: null,
  })));
  const [running, setRunning] = useState(false);
  const [mdValue, setMdValue] = useState('');
  const [streamAgent, setStreamAgent] = useState<string | null>(null);

  const isComplete = paper?.status === 'complete';
  const statusInfo = paper ? (STATUS_MAP[paper.status] || STATUS_MAP.draft) : STATUS_MAP.draft;

  const sseUrl = id ? `/api/papers/${id}/agent/events` : '';

  useSSE(sseUrl, {
    onAgentStart: (agent) => {
      setRunning(true);
      setStreamAgent(agent);
      clearStream(agent);
      setAgentStates(prev => prev.map(a =>
        a.key === agent ? { ...a, status: 'running' } : a
      ));
    },
    onAgentStream: (agent, token) => {
      appendToken(agent, token);
    },
    onAgentStreamEnd: (agent) => {
      // Flush remaining buffer after a short delay to show last tokens
      setTimeout(() => setStreamAgent(null), 1500);
    },
    onAgentComplete: (agent, output) => {
      setAgentStates(prev => prev.map(a =>
        a.key === agent
          ? { ...a, status: 'success', output, finishedAt: new Date().toISOString() }
          : a
      ));
      setRunning(false);
      if (agent === 'outline' || agent === 'write' || agent === 'polish') {
        setMdValue(output);
      }
      if (id) {
        api.get(`/papers/${id}`).then(res => setPaper(res.data)).catch(() => {});
      }
    },
    onAgentError: (agent, error) => {
      setAgentStates(prev => prev.map(a =>
        a.key === agent ? { ...a, status: 'failed', error } : a
      ));
      setRunning(false);
      setStreamAgent(null);
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

  const currentAgent = agentStates.find(a => a.status === 'pending');
  const canRunNext = !!currentAgent;

  const handleRunAgent = async () => {
    if (!id || !currentAgent || running) return;
    setRunning(true);
    setAgentStates(prev => prev.map(a =>
      a.key === currentAgent.key ? { ...a, status: 'running' } : a
    ));
    try {
      await api.post(`/papers/${id}/agent/${currentAgent.key.replace('_', '-')}/run`);
    } catch {
      setAgentStates(prev => prev.map(a =>
        a.key === currentAgent.key ? { ...a, status: 'failed', error: '启动失败' } : a
      ));
      setRunning(false);
    }
  };

  const handleApprove = (_agentKey: string) => {
    if (!paper || !id) return;
    const nextStatus = NEXT_STATUS[paper.status];
    if (nextStatus) {
      setPaper({ ...paper, status: nextStatus });
    }
  };

  const handleReject = async (_agentKey: string, comment: string) => {
    if (!id) return;
    try {
      await api.post(`/papers/${id}/agent/feedback`, {
        task_id: 0, action: 'reject', comment,
      });
    } catch { /* ignore */ }
  };

  const handleEdit = async (_agentKey: string, content: string) => {
    if (!paper || !id) return;
    setMdValue(content);
    try {
      await api.put(`/papers/${id}`, { content });
    } catch { /* ignore */ }
    const nextStatus = NEXT_STATUS[paper.status];
    if (nextStatus) {
      setPaper({ ...paper, status: nextStatus });
    }
  };

  const handleExportDocx = async () => {
    if (!id) return;
    try {
      const res = await api.get(`/papers/${id}/export/docx`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${paper?.topic || '论文'}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch {
      alert('导出失败，请确保论文已生成内容');
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
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#0F172A' }}>
            {paper.title || paper.topic}
          </h1>
          <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{
              display: 'inline-block', padding: '3px 12px', borderRadius: 20,
              fontSize: 12, fontWeight: 600, color: statusInfo.color, background: statusInfo.bg,
            }}>
              {statusInfo.label}
            </span>
            <span style={{ fontSize: 13, color: '#94A3B8' }}>
              {paper.template === 'journal' ? '期刊论文' : '课程论文'}
            </span>
          </div>
        </div>
        {paper.content && (
          <button onClick={handleExportDocx} style={btnExport}>
            📄 导出 Word
          </button>
        )}
      </div>

      {/* Pipeline - only interactive when not complete */}
      <AgentPipeline
        agents={agentStates}
        onApprove={isComplete ? () => {} : handleApprove}
        onReject={isComplete ? () => {} : handleReject}
        onEdit={isComplete ? () => {} : handleEdit}
        onRunNext={handleRunAgent}
        running={running}
        canRunNext={canRunNext && !running && !isComplete}
      />

      {/* Streaming panel — shows live token-by-token output */}
      <StreamPanel
        agentKey={streamAgent || ''}
        visible={!!streamAgent && !isComplete}
      />

      {/* Content area */}
      {isComplete ? (
        /* Read-only preview for completed papers */
        <div data-color-mode="light" style={{
          border: '1px solid #E2E8F0', borderRadius: 8, background: '#fff',
          padding: '32px 40px', minHeight: 400,
        }}>
          <MDEditor.Markdown source={mdValue || '暂无内容'} />
        </div>
      ) : (
        /* Editable editor for in-progress papers */
        <div data-color-mode="light" style={{
          border: '1px solid #E2E8F0', borderRadius: 8, overflow: 'hidden', background: '#fff',
        }}>
          <MDEditor
            value={mdValue}
            onChange={val => setMdValue(val || '')}
            height={600}
          />
        </div>
      )}
    </div>
  );
}

const btnExport: React.CSSProperties = {
  padding: '8px 20px', background: '#3B82F6', color: '#fff',
  border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap',
};
