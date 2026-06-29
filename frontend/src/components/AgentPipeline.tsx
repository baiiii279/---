const AGENTS = [
  { key: 'parse', label: '文献解析' },
  { key: 'outline', label: '大纲生成' },
  { key: 'write', label: '内容撰写' },
  { key: 'polish', label: '润色优化' },
  { key: 'cite_check', label: '引用检查' },
];

export default function AgentPipeline({ currentStatus }: { currentStatus: string }) {
  const currentIndex = AGENTS.findIndex(a => a.key === currentStatus);
  return (
    <div style={{ display: 'flex', gap: 8, padding: '24px 0' }}>
      {AGENTS.map((agent, i) => (
        <div key={agent.key} style={{
          flex: 1, padding: 12, borderRadius: 6, textAlign: 'center',
          background: i <= currentIndex ? '#2563EB' : '#E2E8F0',
          color: i <= currentIndex ? '#fff' : '#64748B',
          fontWeight: i === currentIndex ? 700 : 400,
        }}>
          {agent.label}
        </div>
      ))}
    </div>
  );
}
