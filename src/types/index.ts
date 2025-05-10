export type UserRole = 'admin' | 'instructor' | 'student';

export interface User {
  id: string;
  name: string;
  email?: string;
  role: UserRole;
  avatarUrl?: string;
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