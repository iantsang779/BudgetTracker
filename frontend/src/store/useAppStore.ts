import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  displayCurrency: string
  inflationOverride: number | null
  sidebarOpen: boolean
  setDisplayCurrency: (c: string) => void
  setInflationOverride: (r: number | null) => void
  toggleSidebar: () => void
}

const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      displayCurrency: 'USD',
      inflationOverride: null,
      sidebarOpen: true,
      setDisplayCurrency: (c) => set({ displayCurrency: c }),
      setInflationOverride: (r) => set({ inflationOverride: r }),
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
    }),
    {
      name: 'budget-tracker-app',
      partialize: (s) => ({
        displayCurrency: s.displayCurrency,
        inflationOverride: s.inflationOverride,
      }),
    },
  ),
)

export default useAppStore
