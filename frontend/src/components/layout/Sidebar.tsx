import { NavLink } from 'react-router-dom'

const links = [
  { to: '/',             label: 'Dashboard' },
  { to: '/transactions', label: 'Transactions' },
  { to: '/income',       label: 'Income' },
]

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    width: 200,
    background: '#1e1e2e',
    color: '#cdd6f4',
    display: 'flex',
    flexDirection: 'column',
    padding: '24px 0',
    gap: 4,
    flexShrink: 0,
  },
  title: {
    fontSize: 14,
    fontWeight: 700,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    color: '#6c7086',
    padding: '0 20px 16px',
  },
}

function navStyle(isActive: boolean): React.CSSProperties {
  return {
    display: 'block',
    padding: '10px 20px',
    color: isActive ? '#cba6f7' : '#cdd6f4',
    background: isActive ? '#313244' : 'transparent',
    textDecoration: 'none',
    borderLeft: isActive ? '3px solid #cba6f7' : '3px solid transparent',
    fontWeight: isActive ? 600 : 400,
    fontSize: 14,
  }
}

export default function Sidebar() {
  return (
    <nav style={styles.sidebar}>
      <div style={styles.title}>BudgetTracker</div>
      {links.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          style={({ isActive }) => navStyle(isActive)}
        >
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
