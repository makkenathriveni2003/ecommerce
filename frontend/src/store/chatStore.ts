import { create } from "zustand"
import type { ChatMessage } from "../../types"

interface ChatState {
  messages: ChatMessage[]
  isOpen: boolean
  setIsOpen: (isOpen: boolean) => void
  activeCustomer: string | null
  setActiveCustomer: (customer: string | null) => void
  adminOnline: boolean
  setAdminOnline: (online: boolean) => void
  addMessage: (msg: ChatMessage) => void
  setMessages: (msgs: ChatMessage[]) => void
  unreadCount: number
  incrementUnread: () => void
  resetUnread: () => void
}

export const useChatStore = create<ChatState>()((set) => ({
  messages: [],
  isOpen: false,
  setIsOpen: (isOpen) =>
    set((state) => ({
      isOpen,
      unreadCount: isOpen ? 0 : state.unreadCount,
    })),
  activeCustomer: null,
  setActiveCustomer: (activeCustomer) => set({ activeCustomer }),
  adminOnline: false,
  setAdminOnline: (adminOnline) => set({ adminOnline }),

  addMessage: (msg) =>
    set((state) => {
      // Prevent duplicate messages by ID if ID > 0
      if (msg.id && state.messages.some((m) => m.id === msg.id)) {
        return state
      }
      const updated = [...state.messages, msg]
      const newUnread = state.isOpen ? 0 : state.unreadCount + 1
      return {
        messages: updated,
        unreadCount: newUnread,
      }
    }),

  setMessages: (messages) => set({ messages }),
  unreadCount: 0,
  incrementUnread: () => set((state) => ({ unreadCount: state.unreadCount + 1 })),
  resetUnread: () => set({ unreadCount: 0 }),
}))
