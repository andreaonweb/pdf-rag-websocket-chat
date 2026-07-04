export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}
