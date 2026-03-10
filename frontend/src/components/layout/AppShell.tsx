import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import useAppStore from '../../store/useAppStore'

export default function AppShell() {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#1e1e2e', color: '#cdd6f4' }}>
      {sidebarOpen && <Sidebar />}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <TopBar />
        <main style={{ flex: 1, overflowY: 'auto', padding: 24 }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
