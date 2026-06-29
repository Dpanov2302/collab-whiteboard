export type UUID = string;

export type User = {
  id: UUID;
  email: string;
  username: string;
  role: 'user' | 'admin';
};

export type Workspace = {
  id: UUID;
  name: string;
  description?: string;
  owner_id: UUID;
};

export type Board = {
  id: UUID;
  workspace_id: UUID;
  title: string;
  description?: string;
  created_by_id: UUID;
  is_public: boolean;
};

export type BoardElement = {
  id: UUID;
  board_id: UUID;
  author_id: UUID;
  type: 'sticky' | 'text' | 'rectangle' | 'ellipse' | 'connector';
  x: number;
  y: number;
  width: number;
  height: number;
  z_index: number;
  content: string;
  style: Record<string, string>;
  version: number;
};
