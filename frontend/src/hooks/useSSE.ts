import { useState, useEffect, useRef } from 'react';

interface SSEOptions {
  onAgentStart?: (agent: string) => void;
  onAgentComplete?: (agent: string, output: string) => void;
  onAgentError?: (agent: string, error: string) => void;
  onAgentStream?: (agent: string, token: string) => void;
  onAgentStreamEnd?: (agent: string) => void;
  onPipelineComplete?: () => void;
}

interface SSEState {
  status: 'connecting' | 'connected' | 'error';
}

export default function useSSE(url: string, options?: SSEOptions): SSEState {
  const [state, setState] = useState<SSEState>({ status: 'connecting' });
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function connect() {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setState({ status: 'connecting' });

      const token = localStorage.getItem('token');
      const separator = url.includes('?') ? '&' : '?';
      const authUrl = token ? `${url}${separator}token=${encodeURIComponent(token)}` : url;
      const es = new EventSource(authUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        setState({ status: 'connected' });
      };

      es.addEventListener('agent_start', (event) => {
        const data = JSON.parse(event.data);
        options?.onAgentStart?.(data.agent);
      });

      es.addEventListener('agent_complete', (event) => {
        const data = JSON.parse(event.data);
        options?.onAgentComplete?.(data.agent, data.output);
      });

      es.addEventListener('agent_error', (event) => {
        const data = JSON.parse(event.data);
        options?.onAgentError?.(data.agent, data.error);
      });

      es.addEventListener('agent_stream', (event) => {
        const data = JSON.parse(event.data);
        options?.onAgentStream?.(data.agent, data.token);
      });

      es.addEventListener('agent_stream_end', (event) => {
        const data = JSON.parse(event.data);
        options?.onAgentStreamEnd?.(data.agent);
      });

      es.addEventListener('pipeline_complete', () => {
        options?.onPipelineComplete?.();
      });

      es.onerror = () => {
        setState({ status: 'error' });
        es.close();
        reconnectTimerRef.current = setTimeout(connect, 3000);
      };
    }

    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, [url]);

  return state;
}
