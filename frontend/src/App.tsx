import { BrowserRouter, Routes, Route } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import DashboardPage from './pages/DashboardPage'
import TransactionsPage from './pages/TransactionsPage'
import IncomePage from './pages/IncomePage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="transactions" element={<TransactionsPage />} />
          <Route path="income" element={<IncomePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
