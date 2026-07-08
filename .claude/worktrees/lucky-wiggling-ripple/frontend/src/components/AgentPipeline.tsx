import { useState } from 'react';

export interface AgentNode {
  key: string;
  label: string;
  status: 'pending' | 'running' | 'success' | 'failed';
  output: string | null;
  error: string | null;
  finishedAt: string | null;
}

interface AgentPipelineProps {
  agents: AgentNode[];
  onApprove: (agentKey: string) => void;
  onReject: (agentKey: string, comment: string) => void;
  onEdit: (agentKey: string, content: string) => void;
  onRunNext: () => void;
  running: boolean;
  canRunNext: boolean;
}

const AGENT_LABELS: Record<string, string> = {
  parse: '文献解析',
  outline: '大纲生成',
  write: '内容撰写',
  polish: '润色优化',
  cite_check: '引用检查',
};

function StatusIcon({ status }: { status: string }) {
  const icons: Record<string, string> = {
    pending: '☐',
    running: '⏳',
    success: '✅',
    failed: '❌',
  };
  return <span style={{ marginRight: 6 }}>{icons[status] || '☐'}</span>;
}

export default function AgentPipeline({
  agents, onApprove, onReject, onEdit, onRunNext, running, canRunNext,
}: AgentPipelineProps) {
  // Track which completed agent output is currently expanded
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const [rejectingKey, setRejectingKey] = useState<string | null>(null);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [rejectComments, setRejectComments] = useState<Record<string, string>>({});
  const [editContents, setEditContents] = useState<Record<string, string>>({});

  const latestSuccess = [...agents].reverse().find(a => a.status === 'success');
  const displayAgent = expandedKey
    ? agents.find(a => a.key === expandedKey)
    : latestSuccess;

  return (
    <div style={{ margin: '16px 0' }}>
      {/* Pipeline bar */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16 }}>
        {agents.map((agent) => (
          <div
            key={agent.key}
            onClick={() => {
              if (agent.status === 'success' || agent.status === 'failed') {
                setExpandedKey(expandedKey === agent.key ? null : agent.key);
              }
            }}
            style={{
              flex: 1, padding: '10px 12px', borderRadius: 6, textAlign: 'center',
              cursor: (agent.status === 'success' || agent.status === 'failed') ? 'pointer' : 'default',
              background:
                agent.status === 'running' ? '#DBEAFE' :
                agent.status === 'success' ? '#DCFCE7' :
                agent.status === 'failed' ? '#FEE2E2' :
                '#F1F5F9',
              color:
                agent.status === 'running' ? '#1D4ED8' :
                agent.status === 'success' ? '#166534' :
                agent.status === 'failed' ? '#991B1B' :
                '#64748B',
              fontWeight: agent.status === 'running' ? 700 : 400,
              border: agent.status === 'running' ? '1px solid #93C5FD' : '1px solid transparent',
              transition: 'all 0.3s',
              opacity: agent.status === 'pending' ? 0.6 : 1,
            }}
          >
            <StatusIcon status={agent.status} />
            {AGENT_LABELS[agent.key] || agent.key}
          </div>
        ))}
      </div>

      {/* Expanded output area */}
      {displayAgent && (displayAgent.status === 'success' || displayAgent.status === 'failed') && (
        <div style={{
          border: '1px solid #E2E8F0', borderRadius: 8, padding: 20,
          background: '#fff', marginBottom: 16,
        }}>
          <h4 style={{ margin: '0 0 12px', color: '#0F172A', fontSize: 15, fontWeight: 700 }}>
            {AGENT_LABELS[displayAgent.key]} 输出
          </h4>

          {displayAgent.status === 'failed' ? (
            <div style={{ color: '#DC2626', fontSize: 14 }}>
              {displayAgent.error || '执行失败'}
            </div>
          ) : editingKey === displayAgent.key ? (
            <textarea
              value={editContents[displayAgent.key] || displayAgent.output || ''}
              onChange={e => setEditContents(prev => ({ ...prev, [displayAgent.key]: e.target.value }))}
              style={{
                width: '100%', minHeight: 200, padding: 12, borderRadius: 6,
                border: '1px solid #E2E8F0', fontSize: 14, lineHeight: 1.6,
                fontFamily: 'monospace', resize: 'vertical', boxSizing: 'border-box',
              }}
            />
          ) : (
            <div style={{
              padding: 16, background: '#F8FAFC', borderRadius: 6, fontSize: 14,
              lineHeight: 1.6, whiteSpace: 'pre-wrap', maxHeight: 400, overflow: 'auto',
            }}>
              {displayAgent.output}
            </div>
          )}

          {rejectingKey === displayAgent.key && (
            <textarea
              value={rejectComments[displayAgent.key] || ''}
              onChange={e => setRejectComments(prev => ({ ...prev, [displayAgent.key]: e.target.value }))}
              placeholder="请输入驳回原因..."
              style={{
                width: '100%', minHeight: 80, marginTop: 12, padding: 12,
                borderRadius: 6, border: '1px solid #E2E8F0', fontSize: 14,
                boxSizing: 'border-box',
              }}
            />
          )}

          <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
            <button
              onClick={() => { onApprove(displayAgent.key); setExpandedKey(null); }}
              style={{
                padding: '8px 24px', borderRadius: 6, border: 'none',
                background: '#2563EB', color: '#fff', fontSize: 14,
                fontWeight: 600, cursor: 'pointer',
              }}
            >
              批准
            </button>
            <button
              onClick={() => {
                if (rejectingKey === displayAgent.key) {
                  const comment = rejectComments[displayAgent.key]?.trim();
                  if (comment) {
                    onReject(displayAgent.key, comment);
                    setRejectingKey(null);
                    setRejectComments({});
                  }
                } else {
                  setRejectingKey(displayAgent.key);
                }
              }}
              style={{
                padding: '8px 24px', borderRadius: 6, border: 'none',
                background: '#EF4444', color: '#fff', fontSize: 14,
                fontWeight: 600, cursor: 'pointer',
              }}
            >
              {rejectingKey === displayAgent.key ? '确认驳回' : '驳回'}
            </button>
            <button
              onClick={() => {
                if (editingKey === displayAgent.key) {
                  const content = editContents[displayAgent.key];
                  if (content) {
                    onEdit(displayAgent.key, content);
                    setEditingKey(null);
                    setEditContents({});
                    setExpandedKey(null);
                  }
                } else {
                  setEditContents(prev => ({ ...prev, [displayAgent.key]: displayAgent.output || '' }));
                  setEditingKey(displayAgent.key);
                }
              }}
              style={{
                padding: '8px 24px', borderRadius: 6, border: 'none',
                background: '#F59E0B', color: '#fff', fontSize: 14,
                fontWeight: 600, cursor: 'pointer',
              }}
            >
              {editingKey === displayAgent.key ? '保存编辑' : '编辑'}
            </button>
          </div>

          {/* Run next button */}
          {canRunNext && !running && (
            <button
              onClick={onRunNext}
              style={{
                marginTop: 16, padding: '10px 24px', borderRadius: 6, border: 'none',
                background: '#2563EB', color: '#fff', fontSize: 14, fontWeight: 600,
                cursor: 'pointer', display: 'block', width: '100%',
              }}
            >
              运行下一步 ({AGENT_LABELS[agents.find(a => a.status === 'pending')?.key || '']})
            </button>
          )}
        </div>
      )}
    </div>
  );
}
