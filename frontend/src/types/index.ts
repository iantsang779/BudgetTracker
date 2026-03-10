// ── Accounts ──────────────────────────────────────────────────────────────────

export interface AccountCreate {
  name: string
  currency_code: string
  balance_initial: number
}

export interface AccountUpdate {
  name?: string
  currency_code?: string
  balance_initial?: number
}

export interface AccountRead {
  id: number
  name: string
  currency_code: string
  balance_initial: number
  deleted_at: string | null
}

// ── Categories ────────────────────────────────────────────────────────────────

export interface CategoryCreate {
  name: string
  color_hex: string
  icon: string
  is_income: boolean
}

export interface CategoryUpdate {
  name?: string
  color_hex?: string
  icon?: string
  is_income?: boolean
}

export interface CategoryRead {
  id: number
  name: string
  color_hex: string
  icon: string
  is_income: boolean
  deleted_at: string | null
}

// ── Transactions ──────────────────────────────────────────────────────────────

export type TransactionSource = 'manual' | 'voice'

export interface TransactionCreate {
  account_id: number
  category_id?: number | null
  amount_local: number
  currency_code: string
  amount_base: number
  description?: string | null
  merchant?: string | null
  transaction_date: string
  source?: TransactionSource
  voice_transcript?: string | null
}

export interface TransactionUpdate {
  account_id?: number
  category_id?: number | null
  amount_local?: number
  currency_code?: string
  amount_base?: number
  description?: string | null
  merchant?: string | null
  transaction_date?: string
  source?: TransactionSource
  voice_transcript?: string | null
}

export interface TransactionRead {
  id: number
  account_id: number
  category_id: number | null
  amount_local: number
  currency_code: string
  amount_base: number
  description: string | null
  merchant: string | null
  transaction_date: string
  source: TransactionSource
  voice_transcript: string | null
  deleted_at: string | null
}

export interface TransactionFilters {
  account_id?: number
  category_id?: number
  currency_code?: string
  source?: TransactionSource
  date_from?: string
  date_to?: string
}

// ── Income ────────────────────────────────────────────────────────────────────

export type Recurrence = 'monthly' | 'yearly' | 'one_off'

export interface IncomeCreate {
  account_id: number
  amount_local: number
  currency_code: string
  amount_base: number
  recurrence: Recurrence
  description?: string | null
  effective_date: string
  end_date?: string | null
}

export interface IncomeUpdate {
  account_id?: number
  amount_local?: number
  currency_code?: string
  amount_base?: number
  recurrence?: Recurrence
  description?: string | null
  effective_date?: string
  end_date?: string | null
}

export interface IncomeRead {
  id: number
  account_id: number
  amount_local: number
  currency_code: string
  amount_base: number
  recurrence: Recurrence
  description: string | null
  effective_date: string
  end_date: string | null
  deleted_at: string | null
}

export interface IncomeSummary {
  monthly_total_base: number
  yearly_total_base: number
  active_sources: number
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface MetricsResponse {
  total_spending_base: number
  predicted_monthly_base: number
  savings_rate: number
  inflation_adjusted_spending: number
  monthly_income_base: number
  regression_slope: number
  regression_r2: number
}

export interface ProjectionPoint {
  period: string
  actual: number | null
  predicted: number
  upper_band: number
  lower_band: number
}

export interface SavingsProjectionResponse {
  points: ProjectionPoint[]
  slope: number
  r2_score: number
  error_std: number
}

export interface CategorySpending {
  category_id: number | null
  category_name: string
  total_base: number
}

export interface SpendingByCategoryResponse {
  groups: CategorySpending[]
}

export interface SpendingOverTimePoint {
  period: string
  total_base: number
}

export interface SpendingOverTimeResponse {
  points: SpendingOverTimePoint[]
}

// ── Currency ──────────────────────────────────────────────────────────────────

export interface CurrencyRateRead {
  id: number
  base_code: string
  target_code: string
  rate: number
  fetched_at: string
}

export interface ConvertRequest {
  amount: number
  from_currency: string
  to_currency: string
}

export interface ConvertResponse {
  amount: number
  from_currency: string
  to_currency: string
  converted_amount: number
  rate: number
}
