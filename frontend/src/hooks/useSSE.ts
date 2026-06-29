import { useState, useEffect, useRef } from 'react';

interface SSEState {
  status: 'connecting' | 'connected' | 'error';
  events: unknown[];
}

export default function useSSE(url: string): SSEState {
  const [state, setState] = useState<SSEState>({ status: 'connecting', events: [] });
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function connect() {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setState(prev => ({ ...prev, status: 'connecting' }));

      const es = new EventSource(url);
      eventSourceRef.current = es;

      es.onopen = () => {
        setState(prev => ({ ...prev, status: 'connected' }));
      };

      es.onmessage = (event) => {
        let parsed: unknown;
        try {
          parsed = JSON.parse(event.data);
        } catch {
          parsed = { data: event.data };
        }
        setState(prev => ({ ...prev, events: [...prev.events, parsed] }));
      };

      es.onerror = () => {
        setState(prev => ({ ...prev, status: 'error' }));
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
