import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { api, wsUrl } from '../api/client';
import type { BoardElement } from '../types';

export default function BoardPage() {
  const { boardId = '' } = useParams();
  const [elements, setElements] = useState<BoardElement[]>([]);
  const [status, setStatus] = useState('offline');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    api<BoardElement[]>(`/boards/${boardId}/elements`).then(setElements);
    const socket = new WebSocket(wsUrl(boardId));
    wsRef.current = socket;
    socket.onopen = () => setStatus('online');
    socket.onclose = () => setStatus('offline');
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'element.created') {
        api<BoardElement[]>(`/boards/${boardId}/elements`).then(setElements);
      }
      if (message.type === 'element.updated') {
        api<BoardElement[]>(`/boards/${boardId}/elements`).then(setElements);
      }
      if (message.type === 'element.deleted') {
        api<BoardElement[]>(`/boards/${boardId}/elements`).then(setElements);
      }
    };
    return () => socket.close();
  }, [boardId]);

  async function addSticky() {
    const element = await api<BoardElement>(`/boards/${boardId}/elements`, {
      method: 'POST',
      body: JSON.stringify({ type: 'sticky', x: 80 + elements.length * 30, y: 80 + elements.length * 20, content: 'Новая заметка', style: { color: '#fff7ad' } }),
    });
    setElements([...elements, element]);
    wsRef.current?.send(JSON.stringify({ type: 'element.created', payload: { id: element.id } }));
  }

  async function move(element: BoardElement) {
    const next = await api<BoardElement>(`/boards/${boardId}/elements/${element.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ x: element.x + 30, y: element.y + 20, version: element.version }),
    });
    setElements(elements.map((item) => item.id === next.id ? next : item));
    wsRef.current?.send(JSON.stringify({ type: 'element.updated', payload: { id: next.id } }));
  }

  const orderedElements = useMemo(() => [...elements].sort((a, b) => a.z_index - b.z_index), [elements]);

  return (
    <main className="board-page">
      <aside className="toolbar card">
        <h2>Доска</h2>
        <p>Realtime: <b className={status}>{status}</b></p>
        <button onClick={addSticky}>+ Стикер</button>
        <p className="hint">Клик по элементу смещает его и отправляет событие другим участникам.</p>
      </aside>
      <section className="canvas">
        {orderedElements.map((element) => (
          <button
            key={element.id}
            className={`element ${element.type}`}
            style={{ left: element.x, top: element.y, width: element.width, height: element.height, background: element.style?.color ?? '#fff' }}
            onClick={() => move(element)}
          >
            {element.content}
            <small>v{element.version}</small>
          </button>
        ))}
      </section>
    </main>
  );
}
