import { create } from "zustand"
import type { NotificationItem } from "../../types"

interface NotificationState {
  notifications: NotificationItem[]
  unreadCount: number
  isOpen: boolean
  setIsOpen: (isOpen: boolean) => void
  addNotification: (
    item: Omit<NotificationItem, "id" | "created_at" | "read"> & {
      id?: string
      created_at?: string
      read?: boolean
    },
  ) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  clearAll: () => void
}

const STORAGE_KEY = "shopzone-notifications"

function readStoredNotifications(): NotificationItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveNotifications(items: NotificationItem[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, 50)))
  } catch {
    // ignore
  }
}

const initial = readStoredNotifications()

export const useNotificationStore = create<NotificationState>()((set) => ({
  notifications: initial,
  unreadCount: initial.filter((n) => !n.read).length,
  isOpen: false,
  setIsOpen: (isOpen) => set({ isOpen }),

  addNotification: (item) => {
    const newItem: NotificationItem = {
      id: item.id ?? `notif-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      order_id: item.order_id,
      title: item.title,
      message: item.message,
      type: item.type,
      created_at: item.created_at ?? new Date().toISOString(),
      read: item.read ?? false,
    }

    set((state) => {
      // Prevent exact duplicate notifications within short time
      const exists = state.notifications.some((n) => n.id === newItem.id)
      if (exists) return state

      const updated = [newItem, ...state.notifications].slice(0, 50)
      saveNotifications(updated)
      return {
        notifications: updated,
        unreadCount: updated.filter((n) => !n.read).length,
      }
    })
  },

  markAsRead: (id) => {
    set((state) => {
      const updated = state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n,
      )
      saveNotifications(updated)
      return {
        notifications: updated,
        unreadCount: updated.filter((n) => !n.read).length,
      }
    })
  },

  markAllAsRead: () => {
    set((state) => {
      const updated = state.notifications.map((n) => ({ ...n, read: true }))
      saveNotifications(updated)
      return {
        notifications: updated,
        unreadCount: 0,
      }
    })
  },

  clearAll: () => {
    saveNotifications([])
    set({
      notifications: [],
      unreadCount: 0,
    })
  },
}))
