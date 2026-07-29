import api from './api';
import type { ChatbotResponse, ChatbotMessage } from '@/types';

export const chatbotService = {
  async ask(message: string, history: ChatbotMessage[]): Promise<ChatbotResponse> {
    const res = await api.post('/chatbot/query', { message, history });
    const payload = res.data?.data ?? res.data;
    if (!payload || typeof payload.reply !== 'string') {
      throw new Error('Invalid chatbot response shape');
    }
    return payload as ChatbotResponse;
  },
};
