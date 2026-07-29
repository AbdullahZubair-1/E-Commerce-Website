import { useEffect, useRef, useState, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  PaperAirplaneIcon,
  UserPlusIcon,
  CheckIcon,
  XMarkIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { useAuth } from '@/hooks/useAuth';
import { useChatSocket } from '@/hooks/useChatSocket';
import { getErrorMessage } from '@/services/api';
import {
  socialService,
  type Friend,
  type FriendRequestItem,
  type ChatMessage,
  type SocialUserSearchResult,
} from '@/services/social.service';

type SidebarTab = 'friends' | 'requests';

export function MessagesPage() {
  const { user } = useAuth();
  const [tab, setTab] = useState<SidebarTab>('friends');
  const [friends, setFriends] = useState<Friend[]>([]);
  const [incoming, setIncoming] = useState<FriendRequestItem[]>([]);
  const [outgoing, setOutgoing] = useState<FriendRequestItem[]>([]);
  const [loadingLists, setLoadingLists] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SocialUserSearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  const [activeFriendId, setActiveFriendId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Record<string, ChatMessage[]>>({});
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [draft, setDraft] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const activeFriend = friends.find((f) => f.id === activeFriendId) ?? null;

  const refreshLists = useCallback(async () => {
    try {
      const [f, inc, out] = await Promise.all([
        socialService.listFriends(),
        socialService.listIncomingRequests(),
        socialService.listOutgoingRequests(),
      ]);
      setFriends(f);
      setIncoming(inc);
      setOutgoing(out);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoadingLists(false);
    }
  }, []);

  useEffect(() => {
    refreshLists();
  }, [refreshLists]);

  // Real-time incoming messages: append to whichever conversation they
  // belong to (works whether the chat is open or not, since the cache
  // covers every friend, not just the active one).
  const handleIncoming = useCallback(
    (message: ChatMessage) => {
      const otherId = message.sender_id === user?.id ? message.recipient_id : message.sender_id;
      setConversations((current) => {
        const existing = current[otherId] ?? [];
        if (existing.some((m) => m.id === message.id)) return current;
        return { ...current, [otherId]: [...existing, message] };
      });
    },
    [user?.id]
  );
  
  const { connected, sendMessage } = useChatSocket({ onMessage: handleIncoming });

  useEffect(() => {
messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, [activeFriendId, conversations]);

  const openConversation = async (friendId: string) => {
    setActiveFriendId(friendId);
    if (conversations[friendId]) return; // already loaded
    setLoadingConversation(true);
    try {
      const history = await socialService.getConversation(friendId);
      setConversations((current) => ({ ...current, [friendId]: history }));
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setLoadingConversation(false);
    }
  };

  const handleSend = () => {
    const content = draft.trim();
    if (!content || !activeFriendId) return;

    const sentViaSocket = sendMessage(activeFriendId, content);
    if (!sentViaSocket) {
      // Socket not connected right now -- fall back to REST so the message
      // still goes through.
      socialService
        .sendMessage(activeFriendId, content)
        .then((message) => handleIncoming(message))
        .catch((error) => toast.error(getErrorMessage(error)));
    }
    setDraft('');
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    if (query.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const results = await socialService.search(query.trim());
      setSearchResults(results);
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setSearching(false);
    }
  };

  const handleAddFriend = async (userId: string) => {
    try {
      await socialService.sendFriendRequest(userId);
      toast.success('Friend request sent.');
      setSearchResults((current) => current.filter((r) => r.id !== userId));
      refreshLists();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const handleAccept = async (requestId: string) => {
    try {
      await socialService.acceptFriendRequest(requestId);
      toast.success('Friend request accepted.');
      refreshLists();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const handleDecline = async (requestId: string) => {
    try {
      await socialService.declineFriendRequest(requestId);
      refreshLists();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const activeMessages = activeFriendId ? conversations[activeFriendId] ?? [] : [];

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">Messages</h1>
        <span className={`text-xs px-2 py-1 rounded-full ${connected ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {connected ? 'Live' : 'Connecting…'}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-[70vh] min-h-[500px]">
        {/* Sidebar */}
        <div className="md:col-span-1 bg-white border border-gray-200 rounded-2xl flex flex-col overflow-hidden">
          <div className="p-3 border-b border-gray-100">
            <div className="relative">
              <MagnifyingGlassIcon className="h-4 w-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Find people to add..."
                className="w-full pl-9 pr-3 py-2 text-sm rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
              />
            </div>
            {searchQuery.trim().length >= 2 && (
              <div className="mt-2 space-y-1 max-h-40 overflow-y-auto">
                {searching && <p className="text-xs text-gray-400 px-2">Searching…</p>}
                {!searching && searchResults.length === 0 && (
                  <p className="text-xs text-gray-400 px-2">No matches.</p>
                )}
                {searchResults.map((r) => (
                  <div key={r.id} className="flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-gray-50">
                    <div className="text-sm text-gray-700 truncate">
                      {r.first_name} {r.last_name}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleAddFriend(r.id)}
                      className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 shrink-0 ml-2"
                    >
                      <UserPlusIcon className="h-4 w-4" />
                      Add
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex border-b border-gray-100 text-sm font-medium">
            <button
              type="button"
              onClick={() => setTab('friends')}
              className={`flex-1 py-2.5 ${tab === 'friends' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
            >
              Friends
            </button>
            <button
              type="button"
              onClick={() => setTab('requests')}
              className={`flex-1 py-2.5 relative ${tab === 'requests' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
            >
              Requests
              {incoming.length > 0 && (
                <span className="absolute top-1.5 right-6 bg-red-500 text-white text-[10px] rounded-full h-4 w-4 flex items-center justify-center">
                  {incoming.length}
                </span>
              )}
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {loadingLists && <p className="text-sm text-gray-400 text-center py-6">Loading…</p>}

            {!loadingLists && tab === 'friends' && (
              friends.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-6 px-4">
                  No friends yet — search above to send a friend request.
                </p>
              ) : (
                friends.map((f) => (
                  <button
                    key={f.id}
                    type="button"
                    onClick={() => openConversation(f.id)}
                    className={`w-full flex items-center gap-3 px-3 py-3 text-left hover:bg-gray-50 transition-colors ${activeFriendId === f.id ? 'bg-blue-50' : ''}`}
                  >
                    <div className="relative shrink-0">
                      <div className="h-9 w-9 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-semibold text-sm">
                        {f.first_name[0]}
                        {f.last_name[0]}
                      </div>
                      {f.online && (
                        <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-green-500 border-2 border-white" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {f.first_name} {f.last_name}
                      </p>
                      <p className="text-xs text-gray-400 truncate">{f.online ? 'Online' : 'Offline'}</p>
                    </div>
                  </button>
                ))
              )
            )}

            {!loadingLists && tab === 'requests' && (
              <div className="p-3 space-y-4">
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Incoming</p>
                  {incoming.length === 0 && <p className="text-xs text-gray-400">No pending requests.</p>}
                  {incoming.map((r) => (
                    <div key={r.id} className="flex items-center justify-between py-2">
                      <span className="text-sm text-gray-700 truncate">{r.other_user_name}</span>
                      <div className="flex items-center gap-1 shrink-0 ml-2">
                        <button
                          type="button"
                          onClick={() => handleAccept(r.id)}
                          className="p-1.5 rounded-lg bg-green-50 text-green-600 hover:bg-green-100"
                          aria-label="Accept"
                        >
                          <CheckIcon className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDecline(r.id)}
                          className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100"
                          aria-label="Decline"
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">Sent</p>
                  {outgoing.length === 0 && <p className="text-xs text-gray-400">No pending sent requests.</p>}
                  {outgoing.map((r) => (
                    <div key={r.id} className="flex items-center justify-between py-2">
                      <span className="text-sm text-gray-700 truncate">{r.other_user_name}</span>
                      <span className="text-xs text-gray-400 shrink-0 ml-2">Pending</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Conversation panel */}
        <div className="md:col-span-2 bg-white border border-gray-200 rounded-2xl flex flex-col overflow-hidden">
          {!activeFriend ? (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
              <ChatBubbleLeftRightIcon className="h-10 w-10 mb-2" />
              <p className="text-sm">Select a friend to start chatting</p>
            </div>
          ) : (
            <>
              <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3">
                <div className="h-9 w-9 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-semibold text-sm">
                  {activeFriend.first_name[0]}
                  {activeFriend.last_name[0]}
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    {activeFriend.first_name} {activeFriend.last_name}
                  </p>
                  <p className="text-xs text-gray-400">{activeFriend.online ? 'Online' : 'Offline'}</p>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-gray-50">
                {loadingConversation && <p className="text-sm text-gray-400 text-center">Loading…</p>}
                {!loadingConversation && activeMessages.length === 0 && (
                  <p className="text-sm text-gray-400 text-center">Say hi 👋</p>
                )}
                {activeMessages.map((m) => {
                  const mine = m.sender_id === user?.id;
                  return (
                    <div key={m.id} className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
                      <div
                        className={`rounded-2xl px-4 py-2 max-w-[75%] text-sm ${
                          mine ? 'bg-blue-600 text-white' : 'bg-white text-gray-900 shadow-sm'
                        }`}
                      >
                        {m.content}
                      </div>
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>

              <div className="p-3 border-t border-gray-100 flex gap-2">
                <input
                  type="text"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Type a message..."
                  className="flex-1 rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-400"
                />
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={!draft.trim()}
                  className="inline-flex items-center justify-center rounded-xl bg-blue-600 px-4 py-2.5 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <PaperAirplaneIcon className="h-4 w-4" />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}