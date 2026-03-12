import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  displayCurrency: string
  sidebarOpen: boolean
  setDisplayCurrency: (c: string) => void
  toggleSidebar: () => void
}

const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      displayCurrency: 'GBP',
      sidebarOpen: true,
      setDisplayCurrency: (c) => set({ displayCurrency: c }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
    }),
    {
      name: 'budget-tracker-app',
      partialize: (s) => ({
        displayCurrency: s.displayCurrency,
      }),
    },
  ),
)

export default useAppStore
