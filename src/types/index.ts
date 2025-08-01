export type UserRole = 'admin' | 'instructor' | 'student';

export interface User {
  id: string;
  username: string;
  name?: string; // For backward compatibility, maps to full_name
  full_name?: string;
  email?: string;
  role: UserRole;
  avatarUrl?: string;
  disabled?: boolean;
  approved?: boolean;
  created_at?: string;
  updated_at?: string;
  external_id?: string;
  last_login?: string;
}

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: Date;
  sources?: Source[];
  isLoading?: boolean;
}

export interface Source {
  title: string;
  source: string;
  page?: number | null;
  chunk: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
  userId: string; // ID do usuário que criou a conversa
}

export interface Material {
  id: string;
  title: string;
  description?: string;
  type: 'pdf' | 'docx' | 'txt' | 'video';
  path: string;
  size: number;
  uploadedAt: Date;
  uploadedBy: string;
  tags?: string[];
}

export interface AssistantConfig {
  name: string;
  description?: string;
  prompt: string;
  model: string;
  temperature: number;
  chunkSize: number;
  chunkOverlap: number;
  retrievalSearchType: string;
  embeddingModel: string;
}