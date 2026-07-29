import api from './api';
import type { APIResponse } from '@/types';

export interface SocialUserSearchResult {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface FriendRequestItem {
  id: string;
  requester_id: string;
  addressee_id: string;
  status: string;
  created_at: string;
  other_user_id: string;
  other_user_name: string;
  other_user_email: string;
}

export interface Friend {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  online: boolean;
}

export interface ChatMessage {
  id: string;
  sender_id: string;
  recipient_id: string;
  content: string;
  created_at: string;
  read_at: string | null;
}

export const socialService = {
  async search(query: string): Promise<SocialUserSearchResult[]> {
    const res = await api.get<APIResponse<SocialUserSearchResult[]>>('/social/search', { params: { q: query } });
    return res.data.data!;
  },

  async sendFriendRequest(addresseeId: string): Promise<FriendRequestItem> {
    const res = await api.post<APIResponse<FriendRequestItem>>('/social/friend-requests', { addressee_id: addresseeId });
    return res.data.data!;
  },

  async acceptFriendRequest(requestId: string): Promise<FriendRequestItem> {
    const res = await api.patch<APIResponse<FriendRequestItem>>(`/social/friend-requests/${requestId}/accept`);
    return res.data.data!;
  },

  async declineFriendRequest(requestId: string): Promise<FriendRequestItem> {
    const res = await api.patch<APIResponse<FriendRequestItem>>(`/social/friend-requests/${requestId}/decline`);
    return res.data.data!;
  },

  async listIncomingRequests(): Promise<FriendRequestItem[]> {
    const res = await api.get<APIResponse<FriendRequestItem[]>>('/social/friend-requests/incoming');
    return res.data.data!;
  },

  async listOutgoingRequests(): Promise<FriendRequestItem[]> {
    const res = await api.get<APIResponse<FriendRequestItem[]>>('/social/friend-requests/outgoing');
    return res.data.data!;
  },

  async listFriends(): Promise<Friend[]> {
    const res = await api.get<APIResponse<Friend[]>>('/social/friends');
    return res.data.data!;
  },

  async getConversation(friendId: string): Promise<ChatMessage[]> {
    const res = await api.get<APIResponse<ChatMessage[]>>(`/social/messages/${friendId}`);
    return res.data.data!;
  },

  async sendMessage(recipientId: string, content: string): Promise<ChatMessage> {
    const res = await api.post<APIResponse<ChatMessage>>('/social/messages', { recipient_id: recipientId, content });
    return res.data.data!;
  },
};