import { useState } from 'react';

interface FeedbackPanelProps {
  output: string;
  onApprove: () => void;
  onReject: (comment: string) => void;
  onEdit: (content: string) => void;
}

export default function FeedbackPanel({ output, onApprove, onReject, onEdit }: FeedbackPanelProps) {
  const [rejecting, setRejecting] = useState(false);
  const [comment, setComment] = useState('');
  const [editing, setEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(output);

  const handleReject = () => {
    if (rejecting) {
      if (comment.trim()) {
        onReject(comment.trim());
        setRejecting(false);
        setComment('');
      }
    } else {
      setRejecting(true);
    }
  };

  const handleEdit = () => {
    if (editing) {
      onEdit(editedContent);
      setEditing(false);
    } else {
      setEditedContent(output);
      setEditing(true);
    }
  };

  return (
    <div style={{ border: '1px solid #E2E8F0', borderRadius: 8, padding: 24, marginTop: 24, background: '#fff' }}>
      <h3 style={{ margin: '0 0 16px', color: '#0F172A', fontSize: 18, fontWeight: 700 }}>Agent 输出</h3>
      {editing ? (
        <textarea
          value={editedContent}
          onChange={e => setEditedContent(e.target.value)}
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
          {output}
        </div>
      )}
      {rejecting && (
        <textarea
          value={comment}
          onChange={e => setComment(e.target.value)}
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
          onClick={onApprove}
          style={{
            padding: '8px 24px', borderRadius: 6, border: 'none',
            background: '#2563EB', color: '#fff', fontSize: 14,
            fontWeight: 600, cursor: 'pointer',
          }}
        >
          批准
        </button>
        <button
          onClick={handleReject}
          style={{
            padding: '8px 24px', borderRadius: 6, border: 'none',
            background: '#EF4444', color: '#fff', fontSize: 14,
            fontWeight: 600, cursor: 'pointer',
          }}
        >
          {rejecting ? '确认驳回' : '驳回'}
        </button>
        <button
          onClick={handleEdit}
          style={{
            padding: '8px 24px', borderRadius: 6, border: 'none',
            background: '#F59E0B', color: '#fff', fontSize: 14,
            fontWeight: 600, cursor: 'pointer',
          }}
        >
          {editing ? '保存编辑' : '编辑'}
        </button>
      </div>
    </div>
  );
}
