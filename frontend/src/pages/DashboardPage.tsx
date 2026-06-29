import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Board, Workspace } from '../types';

export default function DashboardPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [boards, setBoards] = useState<Board[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([api<Workspace[]>('/workspaces'), api<Board[]>('/boards')])
      .then(([workspaceData, boardData]) => { setWorkspaces(workspaceData); setBoards(boardData); })
      .catch((err) => setError(err.message));
  }, []);

  async function createWorkspace() {
    const workspace = await api<Workspace>('/workspaces', {
      method: 'POST',
      body: JSON.stringify({ name: `Проект ${workspaces.length + 1}`, description: 'Создано из интерфейса' }),
    });
    setWorkspaces([workspace, ...workspaces]);
  }

  async function createBoard(workspaceId: string) {
    const board = await api<Board>('/boards', {
      method: 'POST',
      body: JSON.stringify({ workspace_id: workspaceId, title: `Новая доска ${boards.length + 1}`, description: 'Realtime-доска' }),
    });
    setBoards([board, ...boards]);
  }

  return (
    <main className="dashboard">
      <section className="hero card">
        <h1>Интерактивные доски</h1>
        <p>Создавайте рабочие пространства, доски и синхронизируйте изменения между участниками в реальном времени.</p>
        <button onClick={createWorkspace}>Создать пространство</button>
      </section>
      {error && <p className="error">{error}</p>}
      <section className="grid">
        {workspaces.map((workspace) => (
          <article className="card" key={workspace.id}>
            <h2>{workspace.name}</h2>
            <p>{workspace.description}</p>
            <button onClick={() => createBoard(workspace.id)}>Создать доску</button>
            <ul className="board-list">
              {boards.filter((board) => board.workspace_id === workspace.id).map((board) => (
                <li key={board.id}><Link to={`/boards/${board.id}`}>{board.title}</Link></li>
              ))}
            </ul>
          </article>
        ))}
      </section>
    </main>
  );
}
