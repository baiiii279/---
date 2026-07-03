import { useEffect, useRef, useState } from 'react';

const AGENT_LABELS: Record<string, string> = {
  parse: '文献解析',
  outline: '大纲生成',
  write: '内容撰写',
  polish: '润色优化',
  cite_check: '引用检查',
};

interface StreamPanelProps {
  agentKey: string;
  visible: boolean;
}

// 全局流式 token 存储（不在组件 state 中，避免每次 token 触发 re-render）
const streamBuffer: Record<string, string> = {};

export function appendToken(agent: string, token: string) {
  streamBuffer[agent] = (streamBuffer[agent] || '') + token;
}

export function clearStream(agent: string) {
  delete streamBuffer[agent];
}

export default function StreamPanel({ agentKey, visible }: StreamPanelProps) {
  const [text, setText] = useState('');
  const [elapsed, setElapsed] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 轮询 buffer，每 80ms 同步到 state
  useEffect(() => {
    if (!visible) {
      setText('');
      setElapsed(0);
      return;
    }

    setElapsed(0);
    timerRef.current = setInterval(() => {
      setElapsed((prev) => prev + 1);
      const current = streamBuffer[agentKey] || '';
      setText((prev) => {
        if (prev !== current) return current;
        return prev;
      });
    }, 80);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      // 清理当前 agent 的 buffer
      delete streamBuffer[agentKey];
    };
  }, [agentKey, visible]);

  // 自动滚动到底部
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [text]);

  if (!visible || !text) return null;

  return (
    <div style={{
      border: '1px solid #DBEAFE', borderRadius: 8, marginBottom: 16,
      background: 'linear-gradient(180deg, #EFF6FF 0%, #F8FAFC 100%)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '10px 16px', background: '#DBEAFE', borderBottom: '1px solid #BFDBFE',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
            background: '#3B82F6', animation: 'pulse 1.5s infinite',
          }} />
          <span style={{ fontSize: 13, fontWeight: 600, color: '#1E40AF' }}>
            {AGENT_LABELS[agentKey] || agentKey} 正在输出...
          </span>
        </div>
        <span style={{ fontSize: 12, color: '#64748B', fontFamily: 'monospace' }}>
          {elapsed < 60 ? `${elapsed}秒` : `${Math.floor(elapsed / 60)}分${elapsed % 60}秒`}
        </span>
      </div>

      {/* Streaming content */}
      <div
        ref={containerRef}
        style={{
          padding: '16px 20px', maxHeight: 320, overflow: 'auto',
          fontSize: 14, lineHeight: 1.8, color: '#1E293B',
          fontFamily: "'Noto Serif SC', 'Source Han Serif SC', 'SimSun', serif",
          whiteSpace: 'pre-wrap',
        }}
      >
        {text}
        <span style={{
          display: 'inline-block', width: 2, height: 16,
          background: '#3B82F6', verticalAlign: 'text-bottom',
          animation: 'blink 0.8s step-end infinite',
        }} />
      </div>

      {/* Keyframes */}
      <style>{`
        @keyframes blink { 50% { opacity: 0; } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>
    </div>
  );
}
