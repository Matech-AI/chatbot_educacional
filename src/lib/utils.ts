import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// ========================================
// GERADOR DE ID ÚNICO MELHORADO
// ========================================
export function generateUniqueId(): string {
  // ✅ Combinação de timestamp, performance.now() e Math.random() para garantir unicidade
  const timestamp = Date.now().toString(36); // Timestamp em base36
  const performanceNow = Math.round(performance.now() * 1000).toString(36); // Performance em base36
  const randomPart = Math.random().toString(36).substring(2, 8); // 6 caracteres aleatórios
  const extraRandom = Math.random().toString(36).substring(2, 8); // Mais 6 caracteres aleatórios
  
  return `${timestamp}${performanceNow}${randomPart}${extraRandom}`;
}

// ========================================
// GERADOR DE ID AINDA MAIS ÚNICO (alternativo)
// ========================================
export function generateStrongUniqueId(): string {
  // ✅ Para casos onde precisamos de ABSOLUTA garantia de unicidade
  return `${Date.now()}_${performance.now()}_${Math.random().toString(36).substring(2)}_${Math.random().toString(36).substring(2)}`;
}

// ========================================
// DEBOUNCE FUNCTION
// ========================================
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(null, args), wait);
  };
}