import useAppStore from '../../store/useAppStore'

const CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY']

const styles: Record<string, React.CSSProperties> = {
  topbar: {
    height: 56,
    background: '#181825',
    borderBottom: '1px solid #313244',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 24px',
    flexShrink: 0,
  },
  title: {
    fontSize: 16,
    fontWeight: 600,
    color: '#cdd6f4',
  },
  select: {
    background: '#313244',
    color: '#cdd6f4',
    border: '1px solid #45475a',
    borderRadius: 6,
    padding: '4px 8px',
    fontSize: 13,
    cursor: 'pointer',
  },
}

export default function TopBar() {
  const { displayCurrency, setDisplayCurrency, toggleSidebar } = useAppStore()

  return (
    <header style={styles.topbar}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button
          onClick={toggleSidebar}
          style={{
            background: 'none',
            border: 'none',
            color: '#cdd6f4',
            cursor: 'pointer',
            fontSize: 18,
            lineHeight: 1,
          }}
          aria-label="Toggle sidebar"
        >
          ☰
        </button>
        <span style={styles.title}>BudgetTracker</span>
      </div>
      <select
        style={styles.select}
        value={displayCurrency}
        onChange={(e) => setDisplayCurrency(e.target.value)}
        aria-label="Display currency"
      >
        {CURRENCIES.map((c) => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>
    </header>
  )
}
