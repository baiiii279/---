import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import MDEditor from '@uiw/react-md-editor';
import api from '../services/api';
import StreamPanel, { appendToken, clearStream } from '../components/StreamPanel';
import useSSE from '../hooks/useSSE';
import FormatTemplateSelector from '../components/FormatTemplateSelector';

interface PaperData {
  id: number; user_id: number; title: string | null; topic: string;
  template: string; status: string; outline: string | null; content: string | null;
}

const AGENTS: { key: string; label: string }[] = [
  { key: 'parse', label: '文献解析' },
  { key: 'outline', label: '大纲生成' },
  { key: 'write', label: '内容撰写' },
  { key: 'polish', label: '润色优化' },
  { key: 'cite_check', label: '引用检查' },
  { key: 'format', label: '格式排版' },
];

const STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  draft: { label: '草稿', color: '#64748B', bg: '#F1F5F9' },
  parsing: { label: '已解析', color: '#2563EB', bg: '#EFF6FF' },
  outlining: { label: '大纲已生成', color: '#7C3AED', bg: '#F5F3FF' },
  writing: { label: '已撰写', color: '#D97706', bg: '#FFFBEB' },
  polishing: { label: '已润色', color: '#059669', bg: '#ECFDF5' },
  checking: { label: '已检查', color: '#DC2626', bg: '#FEF2F2' },
  formatting: { label: '排版中', color: '#0891B2', bg: '#ECFEFF' },
  complete: { label: '已完成', color: '#16A34A', bg: '#F0FDF4' },
};

const STATUS_ORDER = ['draft', 'parsing', 'outlining', 'writing', 'polishing', 'checking', 'formatting', 'complete'];
const NEXT_STATUS: Record<string, string> = {
  draft: 'parsing', parsing: 'outlining', outlining: 'writing',
  writing: 'polishing', polishing: 'checking', checking: 'formatting',
  formatting: 'complete',
};

type AgentStatus = 'pending' | 'running' | 'success' | 'failed';
interface AgentState {
  key: string; label: string;
  status: AgentStatus; output: string | null; error: string | null;
}

export default function PaperWorkbench() {
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<PaperData | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [mdValue, setMdValue] = useState('');
  const [streamAgent, setStreamAgent] = useState<string | null>(null);
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [formatTemplateId, setFormatTemplateId] = useState<number | null>(null);

  const isComplete = paper?.status === 'complete';
  const sseUrl = id ? `/api/papers/${id}/agent/events` : '';

  // 从 paper.status 计算 agent 状态
  const getAgentStates = useCallback((status: string): AgentState[] => {
    const idx = STATUS_ORDER.indexOf(status);
    return AGENTS.map((a, i) => ({
      ...a,
      status: (i < idx ? 'success' : 'pending') as AgentStatus,
      output: null,
      error: null,
    }));
  }, []);

  const [agentStates, setAgentStates] = useState<AgentState[]>(getAgentStates('draft'));

  // 同步：paper.status 变化时只更新 status，保留已有的 output/error
  useEffect(() => {
    if (paper) {
      setAgentStates(prev => {
        const base = getAgentStates(paper!.status);
        return base.map((a, i) => ({
          ...a,
          output: prev[i]?.output || a.output,   // 保留 SSE 收到的输出
          error: prev[i]?.error || a.error,
        }));
      });
    }
  }, [paper?.status]);

  // SSE 事件订阅
  useSSE(sseUrl, {
    onAgentStart: (agent) => {
      setRunning(true);
      setStreamAgent(agent);
      setErrorMsg('');
      clearStream(agent);
      setAgentStates(prev => prev.map(a =>
        a.key === agent ? { ...a, status: 'running', error: null } : a
      ));
    },
    onAgentStream: (agent, token) => {
      appendToken(agent, token);
    },
    onAgentStreamEnd: () => {
      setTimeout(() => setStreamAgent(null), 1500);
    },
    onAgentComplete: (agent, output) => {
      setAgentStates(prev => {
        const updated = prev.map(a =>
          a.key === agent ? { ...a, status: 'success' as AgentStatus, output, error: null } : a
        );
        // 自动展开最新完成的 Agent 输出
        setExpandedAgent(agent);
        return updated;
      });
      setRunning(false);
      if (agent === 'outline' || agent === 'write' || agent === 'polish' || agent === 'format') {
        setMdValue(output);
      }
      // 刷新 paper
      if (id) {
        api.get(`/papers/${id}`).then(res => {
          setPaper(res.data);
        }).catch(() => {});
      }
    },
    onAgentError: (agent, error) => {
      setAgentStates(prev => prev.map(a =>
        a.key === agent ? { ...a, status: 'failed', error } : a
      ));
      setRunning(false);
      setStreamAgent(null);
      setErrorMsg(`${agent} 执行失败: ${error}`);
    },
  });

  // 初始加载
  useEffect(() => {
    if (!id) return;
    api.get(`/papers/${id}`).then(res => {
      const p = res.data;
      setPaper(p);
      // 优先显示 paper.content，确保编辑器永不空白
      setMdValue(p.content || p.outline || '');
      setAgentStates(getAgentStates(p.status));
    }).catch(() => setErrorMsg('加载论文失败'))
      .finally(() => setLoading(false));
  }, [id]);

  // 运行当前待执行的 Agent（同步接口，直接获取结果）
  const handleRun = async (agentKey: string) => {
    if (!id || running) return;
    setRunning(true);
    setErrorMsg('');
    setAgentStates(prev => prev.map(a =>
      a.key === agentKey ? { ...a, status: 'running', error: null } : a
    ));
    try {
      // Format agent uses a dedicated endpoint that accepts template_id
      const templateParam = formatTemplateId ? `?template_id=${formatTemplateId}` : '';
      const url = agentKey === 'format'
        ? `/papers/${id}/agent/format${templateParam}`
        : `/papers/${id}/agent/${agentKey.replace('_', '-')}`;
      const res = await api.post(url);
      // 同步接口直接返回结果，立即更新 UI
      const output = res.data.output || '';
      setAgentStates(prev => prev.map(a =>
        a.key === agentKey
          ? { ...a, status: 'success' as AgentStatus, output, error: null }
          : a
      ));
      setExpandedAgent(agentKey);
      if (agentKey === 'outline' || agentKey === 'write' || agentKey === 'polish' || agentKey === 'format') {
        setMdValue(output);
      }
      setRunning(false);
      // 刷新 paper 状态
      const paperRes = await api.get(`/papers/${id}`);
      setPaper(paperRes.data);
    } catch (err: unknown) {
      const msg = err != null && typeof err === 'object' && 'response' in err
        ? String((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || '请求失败')
        : '请求失败';
      setAgentStates(prev => prev.map(a =>
        a.key === agentKey ? { ...a, status: 'failed', error: msg } : a
      ));
      setRunning(false);
      setErrorMsg(msg);
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
      alert('导出失败');
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 48, color: '#64748B' }}>加载中...</div>;
  }
  if (!paper) {
    return <div style={{ textAlign: 'center', padding: 48, color: '#EF4444' }}>论文不存在</div>;
  }

  const statusInfo = STATUS_MAP[paper.status] || STATUS_MAP.draft;
  const currentIdx = STATUS_ORDER.indexOf(paper.status);
  const currentAgent = currentIdx >= 0 && currentIdx < AGENTS.length ? AGENTS[currentIdx] : null;

  const stageStyle = (idx: number): React.CSSProperties => {
    const isDone = idx < currentIdx;
    const isCurrent = idx === currentIdx;
    const isFuture = idx > currentIdx;
    const ag = agentStates[idx];
    const isRunning = ag?.status === 'running';
    const isFailed = ag?.status === 'failed';

    let bg = '#F1F5F9', color = '#94A3B8', border = '2px solid transparent';
    if (isFailed) { bg = '#FEE2E2'; color = '#991B1B'; border = '2px solid #FCA5A5'; }
    else if (isRunning) { bg = '#DBEAFE'; color = '#1D4ED8'; border = '2px solid #93C5FD'; }
    else if (isDone) { bg = '#DCFCE7'; color = '#166534'; }
    else if (isCurrent) { bg = '#fff'; color = '#2563EB'; border = '2px solid #93C5FD'; }

    return {
      flex: 1, padding: '12px 10px', borderRadius: 8, textAlign: 'center' as const,
      fontSize: 13, fontWeight: isCurrent || isRunning ? 700 : 500,
      background: bg, color, border, cursor: isDone ? 'pointer' : 'default',
      transition: 'all 0.3s', opacity: isFuture ? 0.5 : 1,
      position: 'relative' as const,
    };
  };

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
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
          </div>
        </div>
        {paper.content && (
          <button onClick={handleExportDocx} style={btnExport}>📄 导出 Word</button>
        )}
      </div>

      {/* Error banner */}
      {errorMsg && (
        <div style={{
          padding: '10px 16px', marginBottom: 16, borderRadius: 6,
          background: '#FEF2F2', border: '1px solid #FECACA', color: '#991B1B', fontSize: 13,
        }}>
          {errorMsg}
          <button onClick={() => setErrorMsg('')} style={{
            marginLeft: 12, background: 'none', border: 'none', color: '#991B1B',
            cursor: 'pointer', fontWeight: 600,
          }}>✕</button>
        </div>
      )}

      {/* Pipeline stages */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {AGENTS.map((ag, i) => {
          const agState = agentStates[i];
          const isDone = i < currentIdx;
          const isFailed = agState?.status === 'failed';
          const isRunning = agState?.status === 'running';
          const icons: Record<string, string> = { pending: '', running: '⏳', success: '✅', failed: '❌' };
          const icon = icons[agState?.status || 'pending'] || '';

          return (
            <div
              key={ag.key}
              onClick={() => {
                if (isDone || isFailed) {
                  setExpandedAgent(expandedAgent === ag.key ? null : ag.key);
                }
              }}
              style={stageStyle(i)}
            >
              <div style={{ fontSize: 18, marginBottom: 2 }}>{icon || (i === currentIdx ? '▶' : '○')}</div>
              <div>{ag.label}</div>
              {isFailed && agState?.error && (
                <div style={{ fontSize: 10, marginTop: 4, opacity: 0.7, wordBreak: 'break-all' }}>
                  {agState.error.slice(0, 40)}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Format template selector — shown before the run button when at format stage */}
      {currentAgent?.key === 'format' && !running && (
        <div style={{ marginBottom: 16 }}>
          <FormatTemplateSelector selectedId={formatTemplateId} onSelect={setFormatTemplateId} />
        </div>
      )}

      {/* Run button */}
      {!isComplete && currentAgent && (
        <button
          onClick={() => handleRun(currentAgent.key)}
          disabled={running}
          style={{
            display: 'block', width: '100%', marginBottom: 16,
            padding: '14px 24px', borderRadius: 8, border: 'none',
            background: running ? '#94A3B8' : 'linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)',
            color: '#fff', fontSize: 15, fontWeight: 700, cursor: running ? 'not-allowed' : 'pointer',
            boxShadow: running ? 'none' : '0 2px 12px rgba(37,99,235,0.35)',
          }}
        >
          {running ? `⏳ ${currentAgent.label} 执行中...` : `▶ 开始${currentAgent.label}`}
        </button>
      )}

      {/* Streaming panel */}
      <StreamPanel
        agentKey={streamAgent || ''}
        visible={!!streamAgent && !isComplete}
      />

      {/* Expanded agent output */}
      {expandedAgent && (() => {
        const agState = agentStates.find(a => a.key === expandedAgent);
        if (!agState || agState.status === 'pending' || agState.status === 'running') return null;
        const agLabel = AGENTS.find(a => a.key === expandedAgent)?.label || expandedAgent;

        return (
          <div style={{
            border: '1px solid #E2E8F0', borderRadius: 8, padding: 20,
            background: '#fff', marginBottom: 16,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h4 style={{ margin: 0, color: '#0F172A', fontSize: 15, fontWeight: 700 }}>
                {agState.status === 'failed' ? '❌' : '✅'} {agLabel} 输出
              </h4>
              <button
                onClick={() => setExpandedAgent(null)}
                style={{
                  background: 'none', border: 'none', fontSize: 18, cursor: 'pointer',
                  color: '#94A3B8', padding: 0,
                }}
              >✕</button>
            </div>

            {agState.status === 'failed' ? (
              <div style={{
                padding: 16, background: '#FEF2F2', borderRadius: 6,
                color: '#991B1B', fontSize: 14, lineHeight: 1.6,
              }}>
                {agState.error || '未知错误'}
              </div>
            ) : (
              <div style={{
                padding: 16, background: '#F8FAFC', borderRadius: 6, fontSize: 14,
                lineHeight: 1.6, whiteSpace: 'pre-wrap', maxHeight: 360, overflow: 'auto',
              }}>
                {agState.output}
              </div>
            )}
          </div>
        );
      })()}

      {/* Content area */}
      {isComplete ? (
        <div data-color-mode="light" style={{
          border: '1px solid #E2E8F0', borderRadius: 8, background: '#fff',
          padding: '32px 40px', minHeight: 400,
        }}>
          <MDEditor.Markdown source={mdValue || paper?.content || '暂无内容'} />
        </div>
      ) : (
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
