import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { supabase } from './utils/supabase';

type IconName =
  | 'grid'
  | 'file'
  | 'repeat'
  | 'chart'
  | 'settings'
  | 'help'
  | 'search'
  | 'bell'
  | 'arrow'
  | 'down'
  | 'up'
  | 'dots'
  | 'calendar'
  | 'coffee'
  | 'music'
  | 'shopping'
  | 'play'
  | 'check'
  | 'plus'
  | 'logout'

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    grid: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" /></>,
    file: <><path d="M7 3.75h7l4.25 4.5v11A1.75 1.75 0 0 1 16.5 21h-9A1.75 1.75 0 0 1 5.75 19.25v-13A2.5 2.5 0 0 1 8.25 3.75Z" /><path d="M14 4v5h4.25M9 13h6M9 16.5h6" /></>,
    repeat: <><path d="M17.5 7.5h2.75l-3.5-3.5-3.5 3.5H16v5a4 4 0 0 1-4 4H8" /><path d="M6.5 16.5H3.75l3.5 3.5 3.5-3.5H8v-5a4 4 0 0 1 4-4h4" /></>,
    chart: <><path d="M4 19.5V12m5.3 7.5V5m5.4 14.5v-9m5.3 9V8" /><path d="M2.75 20.25h18.5" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="m19.4 15 .1.1 1.1.9-1.6 2.8-1.4-.5a7.7 7.7 0 0 1-1.5.9l-.2 1.5h-3.2l-.2-1.5a7.7 7.7 0 0 1-1.5-.9l-1.4.5L8 16l1.1-.9A7.6 7.6 0 0 1 9 13.4L7.8 12l1.6-2.8 1.4.5a7.7 7.7 0 0 1 1.5-.9l.2-1.5h3.2l.2 1.5a7.7 7.7 0 0 1 1.5.9l1.4-.5 1.6 2.8-1.1 1a7.6 7.6 0 0 1 .1 2Z" /></>,
    help: <><circle cx="12" cy="12" r="9" /><path d="M9.6 9a2.5 2.5 0 1 1 4.4 1.6c-1.3 1.5-2 1.5-2 3.4m0 3h.01" /></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></>,
    bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-2.5 7-2.5 9h17C20.5 16 18 16 18 9ZM10 21h4" /></>,
    arrow: <><path d="M5 12h14m-6-6 6 6-6 6" /></>,
    down: <><path d="m7 10 5 5 5-5" /></>,
    up: <><path d="M7 14 12 9l5 5m-5-5v11" /></>,
    dots: <><circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" /></>,
    calendar: <><rect x="3.5" y="5" width="17" height="16" rx="2" /><path d="M7.5 3v4m9-4v4M3.5 9.5h17" /></>,
    coffee: <><path d="M5 8h12v8a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V8Zm12 2h2a2 2 0 1 1 0 4h-2M8 3.5v2m4-2v2m4-2v2" /></>,
    music: <><path d="M9 18V5l12-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="18" cy="16" r="3" /></>,
    shopping: <><path d="M4 8h16l-1.2 12H5.2L4 8Z" /><path d="M9 9V6a3 3 0 0 1 6 0v3" /></>,
    play: <><path d="m9 6 10 6-10 6V6Z" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    plus: <><path d="M12 5v14m-7-7h14" /></>,
    logout: <><path d="M10 17l5-5-5-5m5 5H3" /><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6" /></>,
  }

  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  )
}

type PageName =
  | 'dashboard'
  | 'create-mandate'
  | 'my-mandates'
  | 'payment-history'
  | 'analytics'
  | 'settings'
  | 'help'
  | 'profile'

const navigation: { label: string; icon: IconName; page: PageName }[] = [
  { label: 'Dashboard', icon: 'grid', page: 'dashboard' },
  { label: 'Create mandate', icon: 'plus', page: 'create-mandate' },
  { label: 'My mandates', icon: 'repeat', page: 'my-mandates' },
  { label: 'Payment history', icon: 'file', page: 'payment-history' },
  { label: 'Analytics', icon: 'chart', page: 'analytics' },
]

const pageTitles: Record<PageName, string> = {
  dashboard: 'Overview',
  'create-mandate': 'Create mandate',
  'my-mandates': 'My mandates',
  'payment-history': 'Payment history',
  analytics: 'Analytics',
  settings: 'Settings',
  help: 'Help & support',
  profile: 'Profile',
}

const categories = [
  { name: 'Subscriptions', amount: '₹482.00', share: '42%', color: 'sage', icon: 'play' as const },
  { name: 'Shopping', amount: '₹296.50', share: '26%', color: 'gold', icon: 'shopping' as const },
  { name: 'Food & drink', amount: '₹218.00', share: '19%', color: 'clay', icon: 'coffee' as const },
  { name: 'Other', amount: '₹146.00', share: '13%', color: 'lavender', icon: 'music' as const },
]

const categoryChartColors: Record<string, string> = {
  Subscriptions: '#8e9e80',
  Shopping: '#c39457',
  'Food & drink': '#c77b63',
  Other: '#c6b8a2',
}

type DashboardRange = 'week' | 'month' | 'last-month' | 'last-three-months' | 'year'
type ChartInterval = 'daily' | 'weekly' | 'monthly' | 'yearly'

const chartIntervals: { id: ChartInterval; label: string }[] = [
  { id: 'daily', label: 'Daily' },
  { id: 'weekly', label: 'Weekly' },
  { id: 'monthly', label: 'Monthly' },
  { id: 'yearly', label: 'Yearly' },
]

const dashboardRanges: { id: DashboardRange; label: string }[] = [
  { id: 'week', label: 'This week' },
  { id: 'month', label: 'This month' },
  { id: 'last-month', label: 'Last month' },
  { id: 'last-three-months', label: 'Last 3 months' },
  { id: 'year', label: 'This year' },
]

function localDateKey(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function dateOffsetKey(days: number) {
  const date = new Date()
  date.setHours(0, 0, 0, 0)
  date.setDate(date.getDate() + days)
  return localDateKey(date)
}

function thisMonthDayKey(day: number) {
  const date = new Date()
  date.setDate(Math.min(day, date.getDate()))
  date.setHours(0, 0, 0, 0)
  return localDateKey(date)
}

function displayTransactionDate(dateKey: string, time?: string) {
  const todayKey = localDateKey(new Date())
  if (dateKey === todayKey) return `Today${time ? `, ${time}` : ''}`
  if (dateKey === dateOffsetKey(-1)) return 'Yesterday'
  const [year, month, day] = dateKey.split('-').map(Number)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(year, month - 1, day))
}

const transactions = [
  { name: 'Netflix Premium', detail: 'Entertainment · Monthly', dateKey: dateOffsetKey(0), date: displayTransactionDate(dateOffsetKey(0), '9:41 AM'), amountValue: 19.99, amount: '−₹19.99', category: 'Subscriptions', icon: 'play' as const, iconClass: 'transaction-icon--coral' },
  { name: 'Whole Foods Market', detail: 'Groceries · One-time', dateKey: dateOffsetKey(-1), date: displayTransactionDate(dateOffsetKey(-1)), amountValue: 84.26, amount: '−₹84.26', category: 'Shopping', icon: 'shopping' as const, iconClass: 'transaction-icon--sage' },
  { name: 'Spotify', detail: 'Entertainment · Monthly', dateKey: thisMonthDayKey(2), date: displayTransactionDate(thisMonthDayKey(2)), amountValue: 10.99, amount: '−₹10.99', category: 'Subscriptions', icon: 'music' as const, iconClass: 'transaction-icon--gold' },
]
type Transaction = (typeof transactions)[number]

function TransactionRow({
  transaction,
  onSelect,
}: {
  transaction: Transaction
  onSelect: (transaction: Transaction) => void
}) {
  return (
    <button
      aria-label={`View ${transaction.name} transaction details`}
      className="transaction-row transaction-row-button"
      onClick={() => onSelect(transaction)}
      type="button"
    >
      <span className="transaction-merchant">
        <span className={`transaction-icon ${transaction.iconClass}`}><Icon name={transaction.icon} size={18} /></span>
        <span className="transaction-copy"><strong>{transaction.name}</strong><span>{transaction.detail}</span></span>
      </span>
      <span className="transaction-date">{transaction.date}</span>
      <span><span className="status-pill"><span />Completed</span></span>
      <strong className="transaction-amount">{transaction.amount}</strong>
    </button>
  )
}

function DetailsDialog({
  titleId,
  onClose,
  children,
}: {
  titleId: string
  onClose: () => void
  children: ReactNode
}) {
  const dialogRef = useRef<HTMLElement>(null)
  const onCloseRef = useRef(onClose)

  useEffect(() => {
    onCloseRef.current = onClose
  }, [onClose])

  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null
    const dialog = dialogRef.current
    const focusableSelector = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    const firstFocusable = dialog?.querySelector<HTMLElement>('[data-dialog-initial-focus]') ??
      dialog?.querySelector<HTMLElement>(focusableSelector)
    firstFocusable?.focus()

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        onCloseRef.current()
        return
      }
      if (event.key !== 'Tab' || !dialog) return

      const focusable = Array.from(dialog.querySelectorAll<HTMLElement>(focusableSelector))
        .filter((element) => element.offsetParent !== null)
      const first = focusable[0]
      const last = focusable.at(-1)
      if (!first || !last) return
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      previousFocus?.focus()
    }
  }, [])

  return (
    <div
      className="transaction-detail-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onCloseRef.current()
      }}
    >
      <section
        aria-labelledby={titleId}
        aria-modal="true"
        className="transaction-detail-dialog"
        ref={dialogRef}
        role="dialog"
        tabIndex={-1}
      >
        {children}
      </section>
    </div>
  )
}

const dashboardDate = new Intl.DateTimeFormat('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
  year: 'numeric',
}).format(new Date()).toUpperCase()
const currentYear = new Date().getFullYear()
const localToday = (() => {
  const date = new Date()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
})()

interface MandateFormValues {
  name: string
  instruction: string
  spendingLimit: string
  category: string
  startDate: string
  expiryDate: string
  approvalRequired: boolean
}

interface SavedMandate extends Omit<MandateFormValues, 'spendingLimit'> {
  id: string
  spendingLimit: number
  createdAt: string
}

interface MandateWriteValues extends Omit<MandateFormValues, 'spendingLimit'> {
  spendingLimit: number
}

interface DatabaseMandate {
  id: string
  user_id: string
  name: string
  instruction: string
  spending_limit: number | string
  category: string
  start_date: string
  expiry_date: string
  approval_required: boolean
  created_at: string
}

interface MandateStorageState {
  mandates: SavedMandate[]
  error: string
  loadError: string
  loading: boolean
  userId: string | null
}

const mandateColumns = 'id,user_id,name,instruction,spending_limit,category,start_date,expiry_date,approval_required,created_at'

function mapDatabaseMandate(row: DatabaseMandate): SavedMandate {
  return {
    id: row.id,
    name: row.name,
    instruction: row.instruction,
    spendingLimit: Number(row.spending_limit),
    category: row.category,
    startDate: row.start_date,
    expiryDate: row.expiry_date,
    approvalRequired: row.approval_required,
    createdAt: row.created_at,
  }
}

const rupeeFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const chartCurrencyFormatter = new Intl.NumberFormat('en-IN', {
  maximumFractionDigits: 0,
})
const dashboardWholeFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

function dayIndex(dateKey: string) {
  const [year, month, day] = dateKey.split('-').map(Number)
  return Math.floor(Date.UTC(year, month - 1, day) / 86_400_000)
}

function dateKeyFromDayIndex(index: number) {
  return new Date(index * 86_400_000).toISOString().slice(0, 10)
}

function getDashboardRangeBounds(range: DashboardRange, now = new Date()) {
  const todayKey = localDateKey(now)
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate())

  if (range === 'week') {
    const weekday = (start.getDay() + 6) % 7
    start.setDate(start.getDate() - weekday)
  } else if (range === 'month') {
    start.setDate(1)
  } else if (range === 'last-month') {
    start.setDate(1)
    start.setMonth(start.getMonth() - 1)
    const end = new Date(now.getFullYear(), now.getMonth(), 0)
    return { startKey: localDateKey(start), endKey: localDateKey(end) }
  } else if (range === 'last-three-months') {
    const targetMonth = new Date(now.getFullYear(), now.getMonth() - 3, 1)
    const lastTargetDay = new Date(
      targetMonth.getFullYear(),
      targetMonth.getMonth() + 1,
      0,
    ).getDate()
    start.setFullYear(
      targetMonth.getFullYear(),
      targetMonth.getMonth(),
      Math.min(now.getDate(), lastTargetDay),
    )
  } else if (range === 'year') {
    start.setMonth(0, 1)
  }

  return { startKey: localDateKey(start), endKey: todayKey }
}

function getDashboardPeriodData(range: DashboardRange) {
  const { startKey, endKey } = getDashboardRangeBounds(range)
  const startDay = dayIndex(startKey)
  const endDay = dayIndex(endKey)
  const periodTransactions = transactions.filter(
    (transaction) => transaction.dateKey >= startKey && transaction.dateKey <= endKey,
  )
  const total = periodTransactions.reduce((sum, transaction) => sum + transaction.amountValue, 0)
  const categoryData = categories.map((category) => {
    const amount = periodTransactions
      .filter((transaction) => transaction.category === category.name)
      .reduce((sum, transaction) => sum + transaction.amountValue, 0)
    return {
      ...category,
      amountValue: amount,
      amount: rupeeFormatter.format(amount),
      shareValue: total ? (amount / total) * 100 : 0,
      share: total
        ? `${Math.round((amount / total) * 100)}%`
        : '0%',
    }
  })
  const bucketCount: Record<DashboardRange, number> = {
    week: 7,
    month: 5,
    'last-month': 5,
    'last-three-months': 6,
    year: 12,
  }
  const count = bucketCount[range]
  const bucketTotals = Array.from({ length: count }, () => 0)

  for (const transaction of periodTransactions) {
    const transactionDay = dayIndex(transaction.dateKey)
    const bucket = range === 'year'
      ? Number(transaction.dateKey.slice(5, 7)) - 1
      : Math.min(count - 1, Math.floor(((transactionDay - startDay) / Math.max(1, endDay - startDay + 1)) * count))
    bucketTotals[bucket] += transaction.amountValue
  }

  const maxBucket = Math.max(0, ...bucketTotals)
  const axisStep = maxBucket > 0 ? Math.max(50, Math.ceil(maxBucket / 4 / 50) * 50) : 50
  const axisMax = axisStep * 4
  const chartPoints = bucketTotals.map((amount, index) => ({
    x: count > 1 ? (index / (count - 1)) * 700 : 350,
    y: 190 - (amount / axisMax) * 180,
  }))
  const chartLinePath = chartPoints
    .map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x.toFixed(1)} ${point.y.toFixed(1)}`)
    .join(' ')
  const chartAreaPath = `${chartLinePath} L700 190 L0 190 Z`
  const chartLabels = Array.from({ length: range === 'year' ? 6 : count }, (_, index) => {
    if (range === 'year') {
      const monthIndex = Math.round(index * 11 / 5)
      const year = Number(startKey.slice(0, 4))
      return new Intl.DateTimeFormat('en-US', { month: 'short' }).format(new Date(year, monthIndex, 1))
    }
    const boundary = startDay + Math.floor(((endDay - startDay + 1) * index) / count)
    const [year, month, day] = dateKeyFromDayIndex(boundary).split('-').map(Number)
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(year, month - 1, day))
  })
  const categoryStops: string[] = []
  let accumulatedShare = 0
  for (const category of categoryData) {
    const share = total ? (category.amountValue / total) * 100 : 0
    if (share > 0) {
      categoryStops.push(`${categoryChartColors[category.name]} ${accumulatedShare}% ${accumulatedShare + share}%`)
      accumulatedShare += share
    }
  }
  if (accumulatedShare < 100) categoryStops.push(`#e8e3da ${accumulatedShare}% 100%`)

  return {
    startKey,
    endKey,
    transactions: periodTransactions,
    categories: categoryData,
    total,
    bucketTotals,
    axisStep,
    chartPoints,
    chartLinePath,
    chartAreaPath,
    chartLabels,
    chartGradient: `conic-gradient(${categoryStops.join(', ')})`,
  }
}

function getChartSeries(
  data: ReturnType<typeof getDashboardPeriodData>,
  interval: ChartInterval,
) {
  const [endYear, endMonth, endDate] = data.endKey.split('-').map(Number)
  const end = new Date(endYear, endMonth - 1, endDate)
  const bucketCount: Record<ChartInterval, number> = {
    daily: 7,
    weekly: 7,
    monthly: 6,
    yearly: 5,
  }
  const count = bucketCount[interval]
  const firstBucket = new Date(end)
  if (interval === 'daily') firstBucket.setDate(firstBucket.getDate() - (count - 1))
  else if (interval === 'weekly') firstBucket.setDate(firstBucket.getDate() - (count * 7 - 1))
  else if (interval === 'monthly') {
    firstBucket.setDate(1)
    firstBucket.setMonth(firstBucket.getMonth() - (count - 1))
  } else {
    firstBucket.setFullYear(firstBucket.getFullYear() - (count - 1), 0, 1)
  }
  const bucketStarts = Array.from({ length: count }, (_, index) => {
    const bucket = new Date(firstBucket)
    if (interval === 'daily') bucket.setDate(bucket.getDate() + index)
    else if (interval === 'weekly') bucket.setDate(bucket.getDate() + index * 7)
    else if (interval === 'monthly') bucket.setMonth(bucket.getMonth() + index)
    else bucket.setFullYear(bucket.getFullYear() + index)
    return bucket
  })
  const [firstYear, firstMonth] = [
    bucketStarts[0].getFullYear(),
    bucketStarts[0].getMonth() + 1,
  ]

  const bucketTotals = Array.from({ length: bucketStarts.length }, () => 0)
  let chartTransactionCount = 0
  for (const transaction of data.transactions) {
    let bucketIndex = 0
    if (interval === 'daily') {
      bucketIndex = dayIndex(transaction.dateKey) - dayIndex(localDateKey(bucketStarts[0]))
    } else if (interval === 'weekly') {
      bucketIndex = Math.floor((dayIndex(transaction.dateKey) - dayIndex(localDateKey(bucketStarts[0]))) / 7)
    } else {
      const [year, month] = transaction.dateKey.split('-').map(Number)
      bucketIndex = interval === 'monthly'
        ? (year - firstYear) * 12 + month - firstMonth
        : year - firstYear
    }
    if (bucketIndex >= 0 && bucketIndex < bucketTotals.length) {
      bucketTotals[bucketIndex] += transaction.amountValue
      chartTransactionCount += 1
    }
  }

  const maxBucket = Math.max(0, ...bucketTotals)
  const axisStep = maxBucket > 0 ? Math.max(50, Math.ceil(maxBucket / 4 / 50) * 50) : 50
  const axisMax = axisStep * 4
  const chartPoints = bucketTotals.map((amount, index) => ({
    x: bucketTotals.length > 1 ? (index / (bucketTotals.length - 1)) * 700 : 350,
    y: 190 - (amount / axisMax) * 180,
  }))
  const chartLinePath = chartPoints
    .map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x.toFixed(1)} ${point.y.toFixed(1)}`)
    .join(' ')
  const labelCount = Math.min(6, bucketStarts.length)
  const chartLabels = Array.from({ length: labelCount }, (_, index) => {
    const bucketIndex = labelCount > 1
      ? Math.round((index / (labelCount - 1)) * (bucketStarts.length - 1))
      : 0
    const date = bucketStarts[bucketIndex]
    if (interval === 'yearly') return String(date.getFullYear())
    if (interval === 'monthly') {
      return new Intl.DateTimeFormat('en-US', { month: 'short' }).format(date)
    }
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
    }).format(date)
  })

  return {
    axisStep,
    bucketTotals,
    chartAreaPath: `${chartLinePath} L700 190 L0 190 Z`,
    chartLabels,
    chartLinePath,
    chartPoints,
    total: bucketTotals.reduce((sum, amount) => sum + amount, 0),
    transactionCount: chartTransactionCount,
    windowLabel: interval === 'daily'
      ? 'last 7 days'
      : interval === 'weekly'
        ? 'last 7 weeks'
        : interval === 'monthly'
          ? 'last 6 months'
          : 'last 5 years',
  }
}

const dateFormatter = new Intl.DateTimeFormat('en-IN', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

function formatMandateDate(value: string) {
  const [year, month, day] = value.split('-').map(Number)
  return dateFormatter.format(new Date(year, month - 1, day))
}

const initialMandateForm: MandateFormValues = {
  name: '',
  instruction: '',
  spendingLimit: '',
  category: '',
  startDate: localToday,
  expiryDate: '',
  approvalRequired: true,
}

const mandateCategories = ['Subscriptions', 'Shopping', 'Food & drink', 'Other']

function CreateMandatePage({
  initialMandate,
  mandates,
  mandatesLoading,
  mandatesLoadError,
  onSaved,
}: {
  initialMandate: SavedMandate | null
  mandates: SavedMandate[]
  mandatesLoading: boolean
  mandatesLoadError: string
  onSaved: (values: MandateWriteValues, initialMandate: SavedMandate | null) => Promise<void>
}) {
  const [form, setForm] = useState<MandateFormValues>(() => initialMandate
    ? {
        ...initialMandate,
        spendingLimit: String(initialMandate.spendingLimit),
      }
    : { ...initialMandateForm })
  const [errorMessage, setErrorMessage] = useState('')
  const [isSaving, setIsSaving] = useState(false)

  function updateField<Field extends keyof MandateFormValues>(
    field: Field,
    value: MandateFormValues[Field],
  ) {
    setForm((current) => ({ ...current, [field]: value }))
    setErrorMessage('')
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')

    if (mandatesLoading) {
      setErrorMessage('Please wait for your mandates to finish loading before saving.')
      return
    }
    if (mandatesLoadError) {
      setErrorMessage(mandatesLoadError)
      return
    }

    const name = form.name.trim()
    const spendingLimit = Number(form.spendingLimit)
    if (!name) {
      setErrorMessage('Enter a merchant or mandate name.')
      return
    }
    if (!mandateCategories.includes(form.category)) {
      setErrorMessage('Choose a spending category.')
      return
    }
    if (!form.spendingLimit.trim() || !Number.isFinite(spendingLimit) || spendingLimit <= 0) {
      setErrorMessage('Enter a spending limit greater than ₹0.')
      return
    }
    if (!form.startDate) {
      setErrorMessage('Choose a start date.')
      return
    }
    if (!form.expiryDate) {
      setErrorMessage('Choose an expiry date.')
      return
    }
    if (form.expiryDate < form.startDate) {
      setErrorMessage('Expiry date must be on or after the start date.')
      return
    }

    const duplicate = mandates.some((mandate) =>
      mandate.id !== initialMandate?.id &&
      mandate.name.trim().toLocaleLowerCase() === name.toLocaleLowerCase(),
    )
    if (duplicate) {
      setErrorMessage('A mandate with this name already exists. Choose a different name.')
      return
    }
    if (initialMandate && !mandates.some((mandate) => mandate.id === initialMandate.id)) {
      setErrorMessage('This mandate no longer exists. Reload your mandate list and try again.')
      return
    }

    setIsSaving(true)
    try {
      await onSaved({
        name,
        instruction: form.instruction.trim(),
        spendingLimit,
        category: form.category,
        startDate: form.startDate,
        expiryDate: form.expiryDate,
        approvalRequired: form.approvalRequired,
      }, initialMandate)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'This mandate could not be saved. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="mandate-page" key={initialMandate?.id ?? 'new-mandate'}>
      <header className="mandate-page-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> MANDATE MANAGEMENT</div>
          <h1>{initialMandate ? 'Edit mandate' : 'Create a mandate'}<span className="heading-period">.</span></h1>
          <p className="welcome-subtitle">{initialMandate ? 'Update this merchant’s spending rule.' : 'Set a clear spending rule for a merchant or service.'}</p>
        </div>
        <span className="mandate-status-label"><span /> {initialMandate ? 'EDIT MANDATE' : 'NEW MANDATE'}</span>
      </header>

      <form className="panel mandate-form" noValidate onSubmit={handleSubmit}>
        <div className="form-section-heading">
          <span className="form-section-number">01</span>
          <div><h2>Mandate details</h2><p>Define how this mandate can spend.</p></div>
        </div>

        <div className="mandate-fields">
          <div className="form-field">
            <label htmlFor="mandate-name">Merchant / mandate name <span>*</span></label>
            <input
              autoComplete="off"
              id="mandate-name"
              maxLength={80}
              name="name"
              onChange={(event) => updateField('name', event.target.value)}
              placeholder="e.g. Netflix Premium"
              required
              value={form.name}
            />
          </div>

          <div className="form-field">
            <label htmlFor="mandate-category">Spending category <span>*</span></label>
            <select
              id="mandate-category"
              name="category"
              onChange={(event) => updateField('category', event.target.value)}
              required
              value={form.category}
            >
              <option value="" disabled>Select a category</option>
              {mandateCategories.map((category) => <option key={category}>{category}</option>)}
            </select>
          </div>

          <div className="form-field form-field--full">
            <label htmlFor="mandate-instruction">Description or payment instructions <span className="label-optional">(optional)</span></label>
            <textarea
              id="mandate-instruction"
              maxLength={500}
              name="instruction"
              onChange={(event) => updateField('instruction', event.target.value)}
              placeholder="Describe what this mandate is allowed to pay for, in your own words…"
              rows={4}
              value={form.instruction}
            />
            <span className="field-hint">Be specific about what this mandate should and shouldn’t cover.</span>
          </div>

          <div className="form-field">
            <label htmlFor="mandate-limit">Maximum spending limit <span>*</span></label>
            <div className="currency-input">
              <span aria-hidden="true">₹</span>
              <input
                id="mandate-limit"
                inputMode="decimal"
                min="0.01"
                name="spendingLimit"
                onChange={(event) => updateField('spendingLimit', event.target.value)}
                placeholder="0.00"
                required
                step="0.01"
                type="number"
                value={form.spendingLimit}
              />
            </div>
            <span className="field-hint">Maximum amount this mandate can spend.</span>
          </div>

          <div className="form-field">
            <label htmlFor="mandate-start">Start date <span>*</span></label>
            <input
              id="mandate-start"
              name="startDate"
              onChange={(event) => updateField('startDate', event.target.value)}
              required
              type="date"
              value={form.startDate}
            />
          </div>

          <div className="form-field">
            <label htmlFor="mandate-expiry">Expiry date <span>*</span></label>
            <input
              id="mandate-expiry"
              min={form.startDate}
              name="expiryDate"
              onChange={(event) => updateField('expiryDate', event.target.value)}
              required
              type="date"
              value={form.expiryDate}
            />
          </div>
        </div>

        <div className="approval-option">
          <span className="approval-option-icon"><Icon name="check" size={18} /></span>
          <span className="approval-option-copy"><strong>Approval required: {form.approvalRequired ? 'Yes' : 'No'}</strong><span>{form.approvalRequired ? 'Review each payment before it is processed.' : 'Payments may proceed without individual review.'}</span></span>
          <label className="approval-switch">
            <span className="visually-hidden">Require approval for payments</span>
            <input
              checked={form.approvalRequired}
              name="approvalRequired"
              onChange={(event) => updateField('approvalRequired', event.target.checked)}
              role="switch"
              type="checkbox"
            />
            <span className="approval-switch-track" />
          </label>
        </div>

        {mandatesLoading && <p className="field-hint" role="status">Loading your saved mandates to check for duplicates…</p>}
        {mandatesLoadError && <p className="form-message form-message--error" role="alert">{mandatesLoadError}</p>}
        {errorMessage && <p className="form-message form-message--error" role="alert">{errorMessage}</p>}

        <div className="form-actions">
          <span className="required-note"><span>*</span> Required fields</span>
          <button className="create-mandate-button" disabled={isSaving || mandatesLoading || Boolean(mandatesLoadError)} type="submit">
            {isSaving ? 'Saving…' : mandatesLoading ? 'Loading mandates…' : initialMandate ? 'Save changes' : 'Create Mandate'} <Icon name="arrow" size={17} />
          </button>
        </div>
      </form>

      <div className="mandate-security-note"><Icon name="help" size={16} /><span>Your mandate is saved securely to your account.</span></div>
    </section>
  )
}

function MyMandatesPage({
  storageState,
  onCreateMandate,
  onEditMandate,
  onDeleteMandate,
  notice,
}: {
  storageState: MandateStorageState
  onCreateMandate: () => void
  onEditMandate: (mandate: SavedMandate) => void
  onDeleteMandate: (mandate: SavedMandate) => Promise<boolean>
  notice: string
}) {
  const { mandates, error } = storageState
  const [selectedMandate, setSelectedMandate] = useState<SavedMandate | null>(null)
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  return (
    <section className="mandate-page my-mandates-page">
      <header className="mandate-page-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-dot" /> MANDATE MANAGEMENT</div>
          <h1>My mandates<span className="heading-period">.</span></h1>
          <p className="welcome-subtitle">A clear view of the spending rules you’ve set.</p>
        </div>
        <button className="create-mandate-button" onClick={onCreateMandate} type="button">
          <Icon name="plus" size={17} /> Create mandate
        </button>
      </header>

      {notice && <p className="form-message form-message--success mandate-notice" role="status">{notice}</p>}
      {error ? (
        <div className="panel mandates-feedback mandates-feedback--error" role="alert">{error}</div>
      ) : storageState.loading ? (
        <div className="panel mandates-feedback" role="status">Loading your mandates…</div>
      ) : mandates.length === 0 ? (
        <div className="panel mandates-empty-state">
          <span className="mandates-empty-icon"><Icon name="repeat" size={23} /></span>
          <h2>No mandates yet</h2>
          <p>Create a mandate to set spending limits and approval rules. Your saved mandates will appear here.</p>
          <button className="create-mandate-button" onClick={onCreateMandate} type="button">
            <Icon name="plus" size={17} /> Create your first mandate
          </button>
        </div>
      ) : (
        <div className="mandates-list" aria-label="Saved mandates">
          {mandates.map((mandate) => (
            <article className="panel mandate-item" key={mandate.id}>
              <div className="mandate-item-heading">
                <span className="mandate-item-icon"><Icon name="repeat" size={19} /></span>
                <div className="mandate-item-title">
                  <h2>{mandate.name}</h2>
                  <span>{mandate.category}</span>
                </div>
                <span className={`mandate-approval${mandate.approvalRequired ? ' mandate-approval--required' : ''}`}>
                  <span />
                  {mandate.approvalRequired ? 'Approval required' : 'Auto-approved'}
                </span>
              </div>
              <div className="mandate-item-details">
                <div><span>MAXIMUM SPENDING LIMIT</span><strong>{rupeeFormatter.format(mandate.spendingLimit)}</strong></div>
                <div><span>START DATE</span><strong>{formatMandateDate(mandate.startDate)}</strong></div>
                <div><span>EXPIRY DATE</span><strong>{formatMandateDate(mandate.expiryDate)}</strong></div>
                <div><span>APPROVAL STATUS</span><strong>{mandate.approvalRequired ? 'Required before payment' : 'Not required'}</strong></div>
              </div>
              <div className="mandate-item-actions">
                <button className="mandate-secondary-button" onClick={() => setSelectedMandate(mandate)} type="button">View details</button>
                <button className="mandate-secondary-button" onClick={() => onEditMandate(mandate)} type="button">Edit</button>
                <button className="mandate-delete-button" onClick={() => { setSelectedMandate(mandate); setConfirmingDelete(true) }} type="button">Delete</button>
              </div>
            </article>
          ))}
        </div>
      )}
      {selectedMandate && (
        <DetailsDialog
          onClose={() => { setSelectedMandate(null); setConfirmingDelete(false) }}
          titleId="mandate-detail-title"
        >
            <div className="transaction-detail-heading">
              <div>
                <span className="section-kicker">MANDATE DETAILS</span>
                <h2 id="mandate-detail-title">{selectedMandate.name}</h2>
              </div>
              <button aria-label="Close mandate details" className="popover-close" data-dialog-initial-focus onClick={() => { setSelectedMandate(null); setConfirmingDelete(false) }} type="button">Close</button>
            </div>
            <div className="transaction-detail-list mandate-detail-list">
              <div><span>CATEGORY</span><strong>{selectedMandate.category}</strong></div>
              <div><span>MAXIMUM SPENDING LIMIT</span><strong>{rupeeFormatter.format(selectedMandate.spendingLimit)}</strong></div>
              <div><span>START DATE</span><strong>{formatMandateDate(selectedMandate.startDate)}</strong></div>
              <div><span>EXPIRY DATE</span><strong>{formatMandateDate(selectedMandate.expiryDate)}</strong></div>
              <div><span>APPROVAL REQUIRED</span><strong>{selectedMandate.approvalRequired ? 'Yes' : 'No'}</strong></div>
              {selectedMandate.instruction && <div className="mandate-instruction-detail"><span>DESCRIPTION / INSTRUCTIONS</span><strong>{selectedMandate.instruction}</strong></div>}
            </div>
            {storageState.error && <p className="form-message form-message--error" role="alert">{storageState.error}</p>}
            {confirmingDelete ? (
              <div className="mandate-delete-confirm" role="group" aria-label="Confirm mandate deletion">
                <p>Delete “{selectedMandate.name}”? This cannot be undone.</p>
                <button className="mandate-delete-button" disabled={isDeleting} onClick={async () => {
                  setIsDeleting(true)
                  try {
                    if (await onDeleteMandate(selectedMandate)) {
                      setSelectedMandate(null)
                      setConfirmingDelete(false)
                    }
                  } finally {
                    setIsDeleting(false)
                  }
                }} type="button">{isDeleting ? 'Deleting…' : 'Confirm delete'}</button>
                <button className="mandate-secondary-button" disabled={isDeleting} onClick={() => setConfirmingDelete(false)} type="button">Cancel</button>
              </div>
            ) : (
              <div className="mandate-detail-actions">
                <button className="create-mandate-button" onClick={() => onEditMandate(selectedMandate)} type="button">Edit mandate</button>
                <button className="mandate-delete-button" onClick={() => setConfirmingDelete(true)} type="button">Delete mandate</button>
              </div>
            )}
        </DetailsDialog>
      )}
    </section>
  )
}

function SecondaryPageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <header className="mandate-page-heading">
      <div>
        <div className="eyebrow"><span className="eyebrow-dot" /> {eyebrow}</div>
        <h1>{title}<span className="heading-period">.</span></h1>
        <p className="welcome-subtitle">{description}</p>
      </div>
      {action}
    </header>
  )
}

function PaymentHistoryPage({
  onSelectTransaction,
}: {
  onSelectTransaction: (transaction: Transaction) => void
}) {
  return (
    <section className="mandate-page secondary-page">
      <SecondaryPageHeading
        description="Review your recent payment activity."
        eyebrow="YOUR ACTIVITY"
        title="Payment history"
      />
      <section className="panel transactions-panel history-panel" aria-label="Payment history">
        <div className="panel-heading transactions-heading">
          <div><span className="section-kicker">RECENT ACTIVITY</span><h2>All payments</h2></div>
          <span className="history-count">{transactions.length} payments</span>
        </div>
        <div className="transaction-table">
          <div className="transaction-header"><span>MERCHANT</span><span>DATE</span><span>STATUS</span><span className="amount-heading">AMOUNT</span></div>
          {transactions.map((transaction) => (
            <TransactionRow
              key={transaction.name}
              onSelect={onSelectTransaction}
              transaction={transaction}
            />
          ))}
        </div>
      </section>
      <p className="placeholder-note">Payment history is shown from the sample activity available in this dashboard.</p>
    </section>
  )
}

function AnalyticsPage({ mandateCount }: { mandateCount: number }) {
  return (
    <section className="mandate-page secondary-page">
      <SecondaryPageHeading
        description="A snapshot of your spending patterns and mandates."
        eyebrow="YOUR FINANCES"
        title="Analytics"
      />
      <div className="analytics-summary">
        <article className="metric-card metric-card--featured">
          <span className="metric-label">Tracked spending</span>
          <div className="metric-value">₹1,142<span className="metric-cents">.50</span></div>
          <div className="metric-footer"><span className="trend trend--up"><Icon name="up" size={14} /> 8.2%</span><span>vs. last month</span></div>
        </article>
        <article className="metric-card">
          <span className="metric-label">Active mandates</span>
          <div className="metric-value">{String(mandateCount).padStart(2, '0')}</div>
          <div className="metric-footer"><span className="metric-note">Saved in this browser</span></div>
        </article>
        <article className="metric-card">
          <span className="metric-label">Largest category</span>
          <div className="metric-value analytics-category-value">Subscriptions</div>
          <div className="metric-footer"><span className="metric-note">42% of tracked spending</span></div>
        </article>
      </div>
      <section className="panel analytics-breakdown">
        <div className="panel-heading">
          <div><span className="section-kicker">THIS MONTH</span><h2>Spending by category</h2></div>
        </div>
        <div className="analytics-category-list">
          {categories.map((category) => (
            <div className="analytics-category-row" key={category.name}>
              <div className="analytics-category-label"><span>{category.name}</span><strong>{category.amount}</strong></div>
              <div className="analytics-category-track"><span style={{ width: category.share }} /></div>
            </div>
          ))}
        </div>
        <p className="placeholder-note">Insights are based on the sample spending data currently shown on your dashboard.</p>
      </section>
    </section>
  )
}

interface AppSettings {
  paymentNotifications: boolean
  weeklySummary: boolean
}

interface SettingsState {
  values: AppSettings
  message: string
  error: string
}

function isAppSettings(value: unknown): value is AppSettings {
  if (typeof value !== 'object' || value === null) return false
  const settings = value as Record<string, unknown>
  return (
    typeof settings.paymentNotifications === 'boolean' &&
    typeof settings.weeklySummary === 'boolean'
  )
}

const settingsStorageKey = 'mandate-pay:settings'
const defaultSettings: AppSettings = {
  paymentNotifications: true,
  weeklySummary: false,
}

function readAppSettings(): SettingsState {
  try {
    const stored = localStorage.getItem(settingsStorageKey)
    if (!stored) return { values: defaultSettings, message: '', error: '' }
    const parsed: unknown = JSON.parse(stored)
    if (!isAppSettings(parsed)) {
      return {
        values: defaultSettings,
        message: '',
        error: 'Saved settings could not be read. Change a setting to save your preferences again.',
      }
    }
    return { values: parsed, message: '', error: '' }
  } catch {
    return {
      values: defaultSettings,
      message: '',
      error: 'Browser storage is unavailable. Settings cannot be loaded.',
    }
  }
}

function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState>(readAppSettings)

  function updateSetting(key: keyof AppSettings, value: boolean) {
    const updatedValues = { ...settings.values, [key]: value }
    try {
      localStorage.setItem(settingsStorageKey, JSON.stringify(updatedValues))
      setSettings({ values: updatedValues, message: 'Your preferences have been saved.', error: '' })
    } catch {
      setSettings({
        ...settings,
        message: '',
        error: 'Your preference could not be saved. Check browser storage and try again.',
      })
    }
  }

  return (
    <section className="mandate-page secondary-page">
      <SecondaryPageHeading
        description="Choose how you’d like to stay informed."
        eyebrow="PREFERENCES"
        title="Settings"
      />
      <section className="panel settings-panel">
        <div className="panel-heading">
          <div><span className="section-kicker">NOTIFICATIONS</span><h2>Stay in the loop</h2></div>
        </div>
        <label className="setting-row">
          <span className="setting-copy"><strong>Payment notifications</strong><span>Get notified when a mandate payment needs your attention.</span></span>
          <span className="approval-switch">
            <input checked={settings.values.paymentNotifications} onChange={(event) => updateSetting('paymentNotifications', event.target.checked)} role="switch" type="checkbox" aria-label="Payment notifications" />
            <span className="approval-switch-track" />
          </span>
        </label>
        <label className="setting-row">
          <span className="setting-copy"><strong>Weekly spending summary</strong><span>Receive a weekly overview of your spending activity.</span></span>
          <span className="approval-switch">
            <input checked={settings.values.weeklySummary} onChange={(event) => updateSetting('weeklySummary', event.target.checked)} role="switch" type="checkbox" aria-label="Weekly spending summary" />
            <span className="approval-switch-track" />
          </span>
        </label>
        {settings.message && <p className="form-message form-message--success" role="status">{settings.message}</p>}
        {settings.error && <p className="form-message form-message--error" role="alert">{settings.error}</p>}
      </section>
      <p className="placeholder-note">Preferences are saved in this browser and do not change your saved mandates.</p>
    </section>
  )
}

function HelpPage() {
  return (
    <section className="mandate-page secondary-page">
      <SecondaryPageHeading
        description="Helpful information for managing your Mandate Pay account."
        eyebrow="HERE TO HELP"
        title="Help & support"
      />
      <div className="help-grid">
        <article className="panel help-card">
          <span className="help-card-icon"><Icon name="repeat" size={19} /></span>
          <h2>How mandates work</h2>
          <p>Set a spending limit, category, dates, and a plain-language instruction. You decide whether payments need your approval.</p>
        </article>
        <article className="panel help-card">
          <span className="help-card-icon"><Icon name="settings" size={19} /></span>
          <h2>Your saved data</h2>
          <p>Mandates and preferences are stored locally in this browser. They remain on this device and are not synced to an account.</p>
        </article>
        <article className="panel help-card help-card--contact">
          <span className="help-card-icon"><Icon name="help" size={19} /></span>
          <h2>Need more help?</h2>
          <p>For account-specific assistance, contact the support representative who set up your Mandate Pay account.</p>
        </article>
      </div>
    </section>
  )
}

function ProfilePage({ email }: { email: string }) {
  return (
    <section className="mandate-page secondary-page">
      <SecondaryPageHeading
        description="Your authenticated account information."
        eyebrow="YOUR ACCOUNT"
        title="Profile"
      />
      <section className="panel profile-panel">
        <div className="profile-large-avatar">{email.charAt(0).toUpperCase() || 'A'}</div>
        <div className="profile-details">
          <div><span>EMAIL</span><strong>{email}</strong></div>
          <div><span>ACCOUNT TYPE</span><strong>Personal account</strong></div>
          <div><span>PRODUCT</span><strong>Mandate Pay</strong></div>
        </div>
      </section>
    </section>
  )
}

function AuthPage({ initialError = '' }: { initialError?: string }) {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot-password'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')
    setIsSubmitting(true)

    try {
      if (mode === 'login') {
        const { error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        })
        if (error) throw error
      } else {
        const { data, error } = await supabase.auth.signUp({
          email: email.trim(),
          password,
        })
        if (error) throw error
        setSuccessMessage(
          data.session
            ? 'Your account is ready.'
            : 'Account created. Check your email to confirm your address before signing in.',
        )
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Authentication failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handlePasswordResetRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrorMessage('')
    setSuccessMessage('')
    setIsSubmitting(true)

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: new URL('/mandate-pay.html', window.location.origin).toString(),
      })
      if (error) throw error
      setSuccessMessage('If an account exists for this email, a password-reset link is on its way.')
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to send a password-reset email. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  function switchMode(nextMode: 'login' | 'signup' | 'forgot-password') {
    setMode(nextMode)
    setErrorMessage('')
    setSuccessMessage('')
  }

  const isForgotPassword = mode === 'forgot-password'

  return (
    <main className="auth-page">
      <section aria-labelledby="auth-title" className="auth-card">
        <div aria-label="Mandate Pay" className="auth-brand">
          <span className="brand-mark"><span /><span /><span /></span>
          <span className="brand-wordmark">Mandate <span>Pay</span></span>
        </div>
        <span className="section-kicker">
          {isForgotPassword ? 'ACCOUNT RECOVERY' : mode === 'login' ? 'YOUR FINANCES, IN FOCUS' : 'GET STARTED'}
        </span>
        <h1 id="auth-title">
          {isForgotPassword ? 'Reset your password.' : mode === 'login' ? 'Welcome back.' : 'Create your account.'}
        </h1>
        <p className="auth-description">
          {isForgotPassword
            ? 'Enter your account email and we’ll send you a secure password-reset link.'
            : mode === 'login'
            ? 'Sign in to continue to your Mandate Pay workspace.'
            : 'Create an account to access your Mandate Pay workspace.'}
        </p>
        {(initialError || errorMessage) && (
          <p className="auth-message auth-message--error" role="alert">{errorMessage || initialError}</p>
        )}
        {successMessage && <p className="auth-message auth-message--success" role="status">{successMessage}</p>}
        <form
          className="auth-form"
          onSubmit={isForgotPassword ? handlePasswordResetRequest : handleSubmit}
        >
          <label className="auth-field">
            Email address
            <input
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              required
              type="email"
              value={email}
            />
          </label>
          {!isForgotPassword && (
            <label className="auth-field">
              Password
              <input
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                minLength={6}
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
              {mode === 'signup' && <span className="auth-field-hint">Use at least 6 characters.</span>}
            </label>
          )}
          {mode === 'login' && (
            <button
              className="auth-text-link auth-forgot-link"
              onClick={() => switchMode('forgot-password')}
              type="button"
            >
              Forgot password?
            </button>
          )}
          <button className="auth-submit" disabled={isSubmitting} type="submit">
            {isSubmitting
              ? 'Please wait…'
              : isForgotPassword
                ? 'Send reset link'
                : mode === 'login'
                ? 'Sign in'
                : 'Create account'}
          </button>
        </form>
        {isForgotPassword ? (
          <p className="auth-mode-switch">
            Remember your password?{' '}
            <button onClick={() => switchMode('login')} type="button">Back to sign in</button>
          </p>
        ) : (
          <p className="auth-mode-switch">
            {mode === 'login' ? 'New to Mandate Pay?' : 'Already have an account?'}{' '}
            <button
              onClick={() => switchMode(mode === 'login' ? 'signup' : 'login')}
              type="button"
            >
              {mode === 'login' ? 'Create an account' : 'Sign in'}
            </button>
          </p>
        )}
      </section>
      <p className="auth-footer">Your money, mindfully managed.</p>
    </main>
  )
}

function App() {
  const [authUser, setAuthUser] = useState<{ id: string; email?: string } | null>(null);
  const [authLoading, setAuthLoading] = useState(true)
  const [isPasswordRecovery, setIsPasswordRecovery] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [passwordResetMessage, setPasswordResetMessage] = useState('')
  const [isUpdatingPassword, setIsUpdatingPassword] = useState(false)
  const [isPasswordUpdated, setIsPasswordUpdated] = useState(false)
  const [authError, setAuthError] = useState('')
  const [isSigningOut, setIsSigningOut] = useState(false)
  const [currentPage, setCurrentPage] = useState<PageName>('dashboard')
  const [mandateStorage, setMandateStorage] = useState<MandateStorageState>({
    mandates: [],
    error: '',
    loadError: '',
    loading: false,
    userId: null,
  })
  const [mandateEditing, setMandateEditing] = useState<SavedMandate | null>(null)
  const [mandateNotice, setMandateNotice] = useState('')
  const [headerPanel, setHeaderPanel] = useState<'search' | 'notifications' | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDashboardRange, setSelectedDashboardRange] = useState<DashboardRange>('month')
  const [isDashboardRangeOpen, setIsDashboardRangeOpen] = useState(false)
  const [selectedChartInterval, setSelectedChartInterval] = useState<ChartInterval>('weekly')
  const [isChartIntervalOpen, setIsChartIntervalOpen] = useState(false)
  const [selectedCategoryName, setSelectedCategoryName] = useState<string | null>(null)
  const [isCategoryMenuOpen, setIsCategoryMenuOpen] = useState(false)
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null)

  const normalizedQuery = searchQuery.trim().toLocaleLowerCase()
  useEffect(() => {
    let mounted = true
    let receivedAuthEvent = false
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      receivedAuthEvent = true
      if (_event === 'PASSWORD_RECOVERY') {
        setIsPasswordRecovery(true)
        setPasswordResetMessage('')
        setIsPasswordUpdated(false)
      }
      setAuthUser(
        session?.user
          ? { id: session.user.id, email: session.user.email }
          : null,
      )
      if (!session?.user) {
        setMandateStorage({ mandates: [], error: '', loadError: '', loading: false, userId: null })
      }
      setAuthError('')
      setAuthLoading(false)
    })

    supabase.auth.getSession().then(({ data: { session }, error }) => {
      if (!mounted) return
      if (error) {
        setAuthError(error.message)
      } else if (!receivedAuthEvent) {
        setAuthUser(
          session?.user
            ? { id: session.user.id, email: session.user.email }
            : null,
        )
        if (!session?.user) {
          setMandateStorage({ mandates: [], error: '', loadError: '', loading: false, userId: null })
        }
      }
      setAuthLoading(false)
    }).catch((error: unknown) => {
      if (!mounted) return
      setAuthError(error instanceof Error ? error.message : 'Unable to check your sign-in status.')
      setAuthLoading(false)
    })

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    let active = true
    const userId = authUser?.id

    if (userId) {
      void (async () => {
        try {
          const { data, error } = await supabase
            .from('mandates')
            .select(mandateColumns)
            .eq('user_id', userId)
            .order('created_at', { ascending: false })
          if (!active) return
          if (error) {
            setMandateStorage({
              mandates: [],
              error: `Your mandates could not be loaded: ${error.message}`,
              loadError: `Your mandates could not be loaded: ${error.message}`,
              loading: false,
              userId,
            })
            return
          }

          const mandates = ((data ?? []) as DatabaseMandate[]).map(mapDatabaseMandate)
          setMandateStorage({
            mandates,
            error: '',
            loadError: '',
            loading: false,
            userId,
          })
        } catch (error) {
          if (!active) return
          setMandateStorage({
            mandates: [],
            error: error instanceof Error
              ? `Your mandates could not be loaded: ${error.message}`
              : 'Your mandates could not be loaded. Please try again.',
            loadError: error instanceof Error
              ? `Your mandates could not be loaded: ${error.message}`
              : 'Your mandates could not be loaded. Please try again.',
            loading: false,
            userId,
          })
        }
      })()
    }

    return () => {
      active = false
    }
  }, [authUser?.id])

  const mandateStorageForUser: MandateStorageState = authUser?.id === mandateStorage.userId
    ? mandateStorage
    : {
        mandates: [],
        error: '',
        loadError: '',
        loading: Boolean(authUser?.id),
        userId: authUser?.id ?? null,
      }
  const matchingMandates = normalizedQuery
    ? mandateStorageForUser.mandates.filter((mandate) =>
        [mandate.name, mandate.category, mandate.instruction]
          .some((value) => value.toLocaleLowerCase().includes(normalizedQuery)),
      )
    : []
  const matchingPayments = normalizedQuery
    ? transactions.filter((transaction) =>
        [transaction.name, transaction.detail, transaction.date, transaction.amount]
          .some((value) => value.toLocaleLowerCase().includes(normalizedQuery)),
      )
    : []
  const dashboardData = getDashboardPeriodData(selectedDashboardRange)
  const chartSeries = getChartSeries(dashboardData, selectedChartInterval)
  const selectedRangeLabel = dashboardRanges.find((range) => range.id === selectedDashboardRange)?.label ?? 'This month'
  const selectedChartIntervalLabel = chartIntervals.find((interval) => interval.id === selectedChartInterval)?.label ?? 'Weekly'
  const selectedCategory = dashboardData.categories.find((category) => category.name === selectedCategoryName)
  const donutCircumference = 2 * Math.PI * 43
  const donutSegments = dashboardData.categories.map((category, index) => {
    const share = dashboardData.total ? category.amountValue / dashboardData.total : 0
    const segmentLength = donutCircumference * share
    const donutOffset = dashboardData.categories
      .slice(0, index)
      .reduce((offset, previousCategory) => (
        offset + donutCircumference * (dashboardData.total ? previousCategory.amountValue / dashboardData.total : 0)
      ), 0)
    return {
      ...category,
      dashOffset: -donutOffset,
      dashLength: segmentLength,
      color: categoryChartColors[category.name],
    }
  })
  const metricTotalParts = rupeeFormatter.formatToParts(dashboardData.total)
  const metricTotalWhole = metricTotalParts
    .filter((part) => part.type !== 'decimal' && part.type !== 'fraction')
    .map((part) => part.value)
    .join('')
  const metricTotalFraction = metricTotalParts
    .filter((part) => part.type === 'decimal' || part.type === 'fraction')
    .map((part) => part.value)
    .join('')
  const chartMaximum = chartSeries.axisStep * 4
  const chartAxisLabels = Array.from({ length: 5 }, (_, index) =>
    `₹${chartCurrencyFormatter.format(chartMaximum - chartSeries.axisStep * index)}`,
  )
  const sparklineMaximum = Math.max(1, ...chartSeries.bucketTotals)
  const sparklinePath = chartSeries.bucketTotals
    .map((amount, index) => {
      const x = chartSeries.bucketTotals.length > 1
        ? (index / (chartSeries.bucketTotals.length - 1)) * 160
        : 80
      const y = 37 - (amount / sparklineMaximum) * 32
      return `${index === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')
  const sparklineAreaPath = `${sparklinePath} L160 42 L0 42 Z`

  function navigateFromHeader(page: PageName) {
    setCurrentPage(page)
    setHeaderPanel(null)
  }

  async function signOut() {
    setIsSigningOut(true)
    setAuthError('')
    try {
      const { error } = await supabase.auth.signOut()
      if (error) setAuthError(error.message)
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Unable to sign out. Please try again.')
    } finally {
      setIsSigningOut(false)
    }
  }

  async function handlePasswordUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPasswordResetMessage('')
    setIsPasswordUpdated(false)

    if (newPassword.length < 6) {
      setPasswordResetMessage('Password must be at least 6 characters.')
      return
    }

    setIsUpdatingPassword(true)

    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      })

      if (error) throw error

      setPasswordResetMessage('Your password has been updated successfully.')
      setNewPassword('')
      setIsPasswordUpdated(true)
    } catch (error) {
      setPasswordResetMessage(
        error instanceof Error ? error.message : 'Unable to update password.',
      )
    } finally {
      setIsUpdatingPassword(false)
    }
  }

  if (authLoading && !isPasswordRecovery) {
    return (
      <main className="auth-page" aria-live="polite">
        <section className="auth-card auth-loading">
          <div aria-label="Mandate Pay" className="auth-brand">
            <span className="brand-mark"><span /><span /><span /></span>
            <span className="brand-wordmark">Mandate <span>Pay</span></span>
          </div>
          <p>Checking your account…</p>
        </section>
      </main>
    )
  }

  if (isPasswordRecovery) {
    return (
      <main className="auth-page">
        <section aria-labelledby="password-reset-title" className="auth-card">
          <div aria-label="Mandate Pay" className="auth-brand">
            <span className="brand-mark"><span /><span /><span /></span>
            <span className="brand-wordmark">Mandate <span>Pay</span></span>
          </div>
          <span className="section-kicker">ACCOUNT RECOVERY</span>
          <h1 id="password-reset-title">Choose a new password.</h1>
          <p className="auth-description">Enter a new password for your Mandate Pay account.</p>

          {passwordResetMessage && (
            <p
              className={`auth-message ${isPasswordUpdated ? 'auth-message--success' : 'auth-message--error'}`}
              role={isPasswordUpdated ? 'status' : 'alert'}
            >
              {passwordResetMessage}
            </p>
          )}

          {!isPasswordUpdated ? (
            <form className="auth-form" onSubmit={handlePasswordUpdate}>
              <label className="auth-field">
                New password
                <input
                  type="password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  minLength={6}
                  required
                  autoComplete="new-password"
                />
                <span className="auth-field-hint">Use at least 6 characters.</span>
              </label>

              <button
                className="auth-submit"
                type="submit"
                disabled={isUpdatingPassword}
              >
                {isUpdatingPassword ? 'Updating…' : 'Update password'}
              </button>
            </form>
          ) : (
            <button
              className="auth-submit"
              onClick={() => setIsPasswordRecovery(false)}
              type="button"
            >
              Continue to Mandate Pay
            </button>
          )}
        </section>
        <p className="auth-footer">Your money, mindfully managed.</p>
      </main>
    )
  }

  if (!authUser) return <AuthPage initialError={authError} />
  const accountEmail = authUser.email ?? ''
  const accountInitial = accountEmail.charAt(0).toUpperCase() || 'A'

  function openCreateMandate() {
    setMandateEditing(null)
    setMandateNotice('')
    navigateFromHeader('create-mandate')
  }

  async function saveMandate(values: MandateWriteValues, existingMandate: SavedMandate | null) {
    const userId = authUser?.id
    if (!userId) throw new Error('You must be signed in to save a mandate.')
    const databaseValues = {
      name: values.name,
      instruction: values.instruction,
      spending_limit: values.spendingLimit,
      category: values.category,
      start_date: values.startDate,
      expiry_date: values.expiryDate,
      approval_required: values.approvalRequired,
    }

    const result = existingMandate
      ? await supabase
          .from('mandates')
          .update(databaseValues)
          .eq('id', existingMandate.id)
          .eq('user_id', userId)
          .select(mandateColumns)
          .single()
      : await supabase
          .from('mandates')
          .insert({
            ...databaseValues,
            id: crypto.randomUUID(),
            user_id: userId,
            created_at: new Date().toISOString(),
          })
          .select(mandateColumns)
          .single()

    if (result.error) {
      throw new Error(`The mandate could not be ${existingMandate ? 'updated' : 'created'}: ${result.error.message}`)
    }
    if (!result.data) {
      throw new Error(`The mandate could not be ${existingMandate ? 'updated' : 'created'}. No saved record was returned.`)
    }

    const savedMandate = mapDatabaseMandate(result.data as DatabaseMandate)
    setMandateStorage((current) => ({
      mandates: existingMandate
        ? current.mandates.map((mandate) => mandate.id === savedMandate.id ? savedMandate : mandate)
        : [savedMandate, ...current.mandates],
      error: '',
      loadError: '',
      loading: false,
      userId,
    }))
    setMandateEditing(null)
    setMandateNotice(`“${savedMandate.name}” ${existingMandate ? 'has been updated' : 'has been saved'} as a mandate.`)
    navigateFromHeader('my-mandates')
  }

  function editMandate(mandate: SavedMandate) {
    setMandateEditing(mandate)
    setMandateNotice('')
    navigateFromHeader('create-mandate')
  }

  async function deleteMandate(mandateToDelete: SavedMandate): Promise<boolean> {
    const userId = authUser?.id
    if (!userId) {
      setMandateStorage((current) => ({
        ...current,
        error: 'You must be signed in to delete a mandate.',
      }))
      return false
    }
    setMandateStorage((current) => ({ ...current, error: '' }))
    setMandateNotice('')
    try {
      const { data, error } = await supabase
        .from('mandates')
        .delete()
        .eq('id', mandateToDelete.id)
        .eq('user_id', userId)
        .select('id')
        .maybeSingle()

      if (error) throw error
      if (!data) {
        throw new Error('This mandate was not found or you do not have permission to delete it.')
      }

      setMandateStorage((current) => ({
        ...current,
        mandates: current.mandates.filter((mandate) => mandate.id !== mandateToDelete.id),
        error: '',
      }))
      setMandateNotice(`“${mandateToDelete.name}” was deleted.`)
      return true
    } catch (error) {
      setMandateStorage((current) => ({
        ...current,
        error: error instanceof Error
          ? `This mandate could not be deleted: ${error.message}`
          : 'This mandate could not be deleted. Please try again.',
      }))
      return false
    }
  }

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <button className="brand" aria-label="Mandate Pay home — Dashboard" onClick={() => navigateFromHeader('dashboard')} type="button">
          <span className="brand-mark"><span /><span /><span /></span>
          <span className="brand-wordmark">Mandate <span>Pay</span></span>
        </button>

        <div className="workspace-label">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {navigation.map((item) => (
            <button
              aria-label={item.label}
              aria-current={currentPage === item.page ? 'page' : undefined}
              className={`nav-link${currentPage === item.page ? ' nav-link--active' : ''}`}
              key={item.label}
              onClick={() => item.page === 'create-mandate' ? openCreateMandate() : navigateFromHeader(item.page)}
              type="button"
            >
              <Icon name={item.icon} size={19} />
              <span>{item.label}</span>
              {item.page === 'my-mandates' && mandateStorageForUser.mandates.length > 0 && (
                <span className="nav-count">{mandateStorageForUser.mandates.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="workspace-label">PREFERENCES</div>
          <button
            aria-label="Settings"
            aria-current={currentPage === 'settings' ? 'page' : undefined}
            className={`nav-link${currentPage === 'settings' ? ' nav-link--active' : ''}`}
            onClick={() => navigateFromHeader('settings')}
            type="button"
          >
            <Icon name="settings" size={19} /><span>Settings</span>
          </button>
          <button
            aria-label="Help & support"
            aria-current={currentPage === 'help' ? 'page' : undefined}
            className={`nav-link${currentPage === 'help' ? ' nav-link--active' : ''}`}
            onClick={() => navigateFromHeader('help')}
            type="button"
          >
            <Icon name="help" size={19} /><span>Help & support</span>
          </button>
          <div className="sidebar-divider" />
          <button
            aria-label="Profile"
            aria-current={currentPage === 'profile' ? 'page' : undefined}
            className={`profile profile-nav-button${currentPage === 'profile' ? ' profile-nav-button--active' : ''}`}
            onClick={() => navigateFromHeader('profile')}
            type="button"
          >
            <div className="profile-avatar">{accountInitial}</div>
            <div className="profile-copy"><strong>{accountEmail || 'Your account'}</strong><span>Personal account</span></div>
            <Icon name="dots" size={19} />
          </button>
          <button
            aria-label="Sign out"
            className="nav-link sign-out-button"
            disabled={isSigningOut}
            onClick={signOut}
            type="button"
          >
            <Icon name="logout" size={19} />
            <span>{isSigningOut ? 'Signing out…' : 'Sign out'}</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <button className="breadcrumb-home" onClick={() => navigateFromHeader('dashboard')} type="button">Workspace</button>
            <span className="breadcrumb-slash">/</span>
            {currentPage === 'dashboard' ? (
              <button
                aria-current="page"
                className="breadcrumb-overview"
                onClick={() => navigateFromHeader('dashboard')}
                type="button"
              >
                {pageTitles[currentPage]}
              </button>
            ) : (
              <strong>{pageTitles[currentPage]}</strong>
            )}
          </div>
          <div className="topbar-actions">
            <button
              type="button"
              className="icon-button"
              aria-label="Search"
              aria-expanded={headerPanel === 'search'}
              aria-controls="header-search-panel"
              onClick={() => setHeaderPanel((panel) => panel === 'search' ? null : 'search')}
            >
              <Icon name="search" />
            </button>
            <button
              type="button"
              className="icon-button notification-button"
              aria-label="Notifications"
              aria-expanded={headerPanel === 'notifications'}
              aria-controls="header-notifications-panel"
              onClick={() => setHeaderPanel((panel) => panel === 'notifications' ? null : 'notifications')}
            >
              <Icon name="bell" />
            </button>
            <div className="topbar-divider" />
            <button aria-label="Profile" className="topbar-avatar topbar-avatar-button" onClick={() => navigateFromHeader('profile')} type="button">{accountInitial}</button>
          </div>
          {headerPanel === 'search' && (
            <section className="header-popover search-popover" id="header-search-panel" aria-label="Search mandates and payment history">
              <div className="popover-heading">
                <div><span className="section-kicker">QUICK FIND</span><h2>Search</h2></div>
                <button className="popover-close" onClick={() => setHeaderPanel(null)} type="button">Close</button>
              </div>
              <label className="search-input-wrap">
                <Icon name="search" size={17} />
                <span className="visually-hidden">Search saved mandates and payment history</span>
                <input
                  autoFocus
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="Search mandates or payments…"
                  type="search"
                  value={searchQuery}
                />
              </label>
              {!normalizedQuery ? (
                <p className="popover-hint">Search mandate names, categories, instructions, merchants, and payment details.</p>
              ) : (
                <div className="search-results" aria-live="polite">
                  {matchingMandates.length > 0 && (
                    <div className="search-result-group">
                      <span className="search-result-label">MANDATES</span>
                      {matchingMandates.map((mandate) => (
                        <button className="search-result" key={mandate.id} onClick={() => navigateFromHeader('my-mandates')} type="button">
                          <span className="search-result-icon"><Icon name="repeat" size={16} /></span>
                          <span><strong>{mandate.name}</strong><small>{mandate.category} · {rupeeFormatter.format(mandate.spendingLimit)}</small></span>
                          <Icon name="arrow" size={15} />
                        </button>
                      ))}
                    </div>
                  )}
                  {matchingPayments.length > 0 && (
                    <div className="search-result-group">
                      <span className="search-result-label">PAYMENT HISTORY</span>
                      {matchingPayments.map((payment) => (
                        <button className="search-result" key={payment.name} onClick={() => navigateFromHeader('payment-history')} type="button">
                          <span className={`transaction-icon ${payment.iconClass}`}><Icon name={payment.icon} size={16} /></span>
                          <span><strong>{payment.name}</strong><small>{payment.detail} · {payment.amount}</small></span>
                          <Icon name="arrow" size={15} />
                        </button>
                      ))}
                    </div>
                  )}
                  {matchingMandates.length === 0 && matchingPayments.length === 0 && (
                    <p className="popover-empty">No mandates or payments match “{searchQuery.trim()}”.</p>
                  )}
                </div>
              )}
            </section>
          )}
          {headerPanel === 'notifications' && (
            <section className="header-popover notification-popover" id="header-notifications-panel" aria-label="Notifications">
              <div className="popover-heading">
                <div><span className="section-kicker">UPDATES</span><h2>Notifications</h2></div>
                <button className="popover-close" onClick={() => setHeaderPanel(null)} type="button">Close</button>
              </div>
              <div className="notification-empty">
                <span className="notification-empty-icon"><Icon name="bell" size={19} /></span>
                <strong>You’re all caught up</strong>
                <span>There are no new notifications right now.</span>
              </div>
            </section>
          )}
        </header>

        <div className="page-content">
          {authError && <p className="auth-session-error" role="alert">{authError}</p>}
          {currentPage === 'create-mandate' ? (
            <CreateMandatePage
              key={mandateEditing?.id ?? 'new'}
              initialMandate={mandateEditing}
              mandates={mandateStorageForUser.mandates}
              mandatesLoading={mandateStorageForUser.loading}
              mandatesLoadError={mandateStorageForUser.loadError}
              onSaved={saveMandate}
            />
          ) : currentPage === 'my-mandates' ? (
            <MyMandatesPage
              onCreateMandate={openCreateMandate}
              onDeleteMandate={deleteMandate}
              onEditMandate={editMandate}
              notice={mandateNotice}
              storageState={mandateStorageForUser}
            />
          ) : currentPage === 'payment-history' ? (
            <PaymentHistoryPage onSelectTransaction={setSelectedTransaction} />
          ) : currentPage === 'analytics' ? (
            <AnalyticsPage mandateCount={mandateStorageForUser.mandates.length} />
          ) : currentPage === 'settings' ? (
            <SettingsPage />
          ) : currentPage === 'help' ? (
            <HelpPage />
          ) : currentPage === 'profile' ? (
            <ProfilePage email={accountEmail} />
          ) : (
            <>
          <section className="welcome-row">
            <div>
              <div className="eyebrow"><span className="eyebrow-dot" /> {dashboardDate}</div>
              <h1>Good morning, Mandate Pay<span className="heading-period">.</span></h1>
              <p className="welcome-subtitle">Here’s what’s happening with your money today.</p>
            </div>
            <div className="period-picker">
              <button
                type="button"
                className="period-button"
                aria-expanded={isDashboardRangeOpen}
                aria-haspopup="listbox"
                aria-controls="dashboard-range-options"
                onClick={() => setIsDashboardRangeOpen((open) => !open)}
              >
                <Icon name="calendar" size={17} /> {selectedRangeLabel} <Icon name="down" size={16} />
              </button>
              {isDashboardRangeOpen && (
                <div className="period-options" id="dashboard-range-options" role="listbox" aria-label="Select spending period">
                  {dashboardRanges.map((range) => (
                    <button
                      aria-selected={selectedDashboardRange === range.id}
                      className={`period-option${selectedDashboardRange === range.id ? ' period-option--selected' : ''}`}
                      key={range.id}
                      onClick={() => {
                        setSelectedDashboardRange(range.id)
                        setIsDashboardRangeOpen(false)
                      }}
                      role="option"
                      type="button"
                    >
                      {range.label}
                      {selectedDashboardRange === range.id && <Icon name="check" size={15} />}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className="metrics-grid" aria-label="Account summary">
            <article className="metric-card metric-card--featured">
              <div className="metric-topline">
                <span className="metric-label">Total spent</span>
                <span className="metric-icon metric-icon--sage"><Icon name="chart" size={18} /></span>
              </div>
              <div className="metric-value">{metricTotalWhole}<span className="metric-cents">{metricTotalFraction}</span></div>
              <div className="metric-footer"><span className="metric-note">{dashboardData.transactions.length} payments</span><span>in {selectedRangeLabel.toLowerCase()}</span></div>
              <div className="metric-sparkline" aria-hidden="true">
                <svg viewBox="0 0 160 42" preserveAspectRatio="none"><path d={sparklinePath} /><path className="sparkline-fill" d={sparklineAreaPath} /></svg>
              </div>
            </article>

            <article className="metric-card">
              <div className="metric-topline">
                <span className="metric-label">Active mandates</span>
                <span className="metric-icon metric-icon--cream"><Icon name="repeat" size={18} /></span>
              </div>
              <div className="metric-value">{mandateStorageForUser.loading ? '—' : String(mandateStorageForUser.mandates.filter((mandate) => mandate.startDate <= localToday && mandate.expiryDate >= localToday).length).padStart(2, '0')}</div>
              <div className="metric-footer"><span className="metric-note">Active saved mandates</span></div>
              <div className="merchant-avatars" aria-label="Merchants include Netflix, Spotify, and more">
                <span className="merchant-avatar merchant-avatar--red">N</span><span className="merchant-avatar merchant-avatar--green">S</span><span className="merchant-avatar merchant-avatar--blue">A</span><span className="merchant-avatar merchant-avatar--more">+5</span>
              </div>
            </article>

            <article className="metric-card">
              <div className="metric-topline">
                <span className="metric-label">Approved payments</span>
                <span className="metric-icon metric-icon--cream"><Icon name="check" size={18} /></span>
              </div>
              <div className="metric-value">{dashboardData.transactions.length}</div>
              <div className="metric-footer"><span className="metric-note">{selectedRangeLabel}</span><span className="metric-divider" /><span className="metric-note">All on track</span></div>
              <div className="approval-progress"><span /></div>
            </article>
          </section>

          <section className="charts-grid" aria-label="Spending analytics">
            <article className="panel spending-panel">
              <div className="panel-heading">
                <div><span className="section-kicker">YOUR FINANCES</span><h2>Spending overview</h2></div>
                <div className="period-picker">
                  <button
                    aria-controls="chart-interval-options"
                    aria-expanded={isChartIntervalOpen}
                    aria-haspopup="listbox"
                    aria-label={`Chart interval: ${selectedChartIntervalLabel}`}
                    className="select-button"
                    onClick={() => setIsChartIntervalOpen((open) => !open)}
                    type="button"
                  >
                    {selectedChartIntervalLabel} <Icon name="down" size={15} />
                  </button>
                  {isChartIntervalOpen && (
                    <div className="period-options" id="chart-interval-options" role="listbox" aria-label="Select chart interval">
                      {chartIntervals.map((interval) => (
                        <button
                          aria-selected={selectedChartInterval === interval.id}
                          className={`period-option${selectedChartInterval === interval.id ? ' period-option--selected' : ''}`}
                          key={interval.id}
                          onClick={() => {
                            setSelectedChartInterval(interval.id)
                            setIsChartIntervalOpen(false)
                          }}
                          role="option"
                          type="button"
                        >
                          {interval.label}
                          {selectedChartInterval === interval.id && <Icon name="check" size={15} />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              <div className="chart-summary"><strong>{rupeeFormatter.format(chartSeries.total)}</strong><span className="summary-period">{chartSeries.transactionCount} payments · {chartSeries.windowLabel} · {selectedRangeLabel.toLowerCase()}</span></div>
              <div className="line-chart" role="img" aria-label={`${selectedChartIntervalLabel} spending trend for ${chartSeries.windowLabel} within ${selectedRangeLabel}, totalling ${rupeeFormatter.format(chartSeries.total)}`}>
                <div className="chart-y-labels">{chartAxisLabels.map((label) => <span key={label}>{label}</span>)}</div>
                <svg className="chart-svg" viewBox="0 0 700 205" preserveAspectRatio="none">
                  <defs><linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#91a185" stopOpacity=".24" /><stop offset="100%" stopColor="#91a185" stopOpacity="0" /></linearGradient></defs>
                  <path className="chart-gridline" d="M0 10H700M0 55H700M0 100H700M0 145H700M0 190H700" />
                  <path className="chart-area" d={chartSeries.chartAreaPath} />
                  <path className="chart-line" d={chartSeries.chartLinePath} />
                  <circle className="chart-point-halo" cx={chartSeries.chartPoints.at(-1)?.x ?? 700} cy={chartSeries.chartPoints.at(-1)?.y ?? 190} r="8" />
                  <circle className="chart-point" cx={chartSeries.chartPoints.at(-1)?.x ?? 700} cy={chartSeries.chartPoints.at(-1)?.y ?? 190} r="4" />
                </svg>
                <div className="chart-x-labels">{chartSeries.chartLabels.map((label, index) => <span key={`${label}-${index}`}>{label}</span>)}</div>
              </div>
              <div className="chart-legend"><span className="legend-dot" /> {selectedChartIntervalLabel} payment totals</div>
            </article>

            <article className="panel category-panel">
              <div className="panel-heading">
                <div><span className="section-kicker">WHERE IT GOES</span><h2>By category</h2></div>
                <div className="period-picker">
                  <button
                    aria-expanded={isCategoryMenuOpen}
                    aria-haspopup="menu"
                    aria-label="More category options"
                    className="more-button"
                    onClick={() => setIsCategoryMenuOpen((open) => !open)}
                    type="button"
                  >
                    <Icon name="dots" />
                  </button>
                  {isCategoryMenuOpen && (
                    <div className="period-options category-options" role="menu">
                      <button
                        className="period-option"
                        onClick={() => {
                          setSelectedCategoryName(null)
                          setIsCategoryMenuOpen(false)
                        }}
                        role="menuitem"
                        type="button"
                      >
                        Clear category selection
                      </button>
                    </div>
                  )}
                </div>
              </div>
              <div className="donut-wrap">
                <div className="donut-chart">
                  <svg className="donut-ring" viewBox="0 0 120 120" role="group" aria-label="Select a spending category">
                    <circle className="donut-track" cx="60" cy="60" r="43" />
                    {donutSegments.map((segment) => (
                      <circle
                        aria-label={`Select ${segment.name}: ${segment.amount}, ${segment.share}`}
                        aria-pressed={selectedCategoryName === segment.name}
                        className={`donut-segment${selectedCategoryName === segment.name ? ' donut-segment--selected' : ''}`}
                        cx="60"
                        cy="60"
                        key={segment.name}
                        onClick={() => setSelectedCategoryName(segment.name)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault()
                            setSelectedCategoryName(segment.name)
                          }
                        }}
                        r="43"
                        role="button"
                        stroke={segment.color}
                        strokeDasharray={`${segment.dashLength} ${donutCircumference - segment.dashLength}`}
                        strokeDashoffset={segment.dashOffset}
                        strokeWidth={selectedCategoryName === segment.name ? 24 : 20}
                        tabIndex={segment.amountValue > 0 ? 0 : -1}
                        transform="rotate(-90 60 60)"
                      />
                    ))}
                  </svg>
                  <div className="donut-center" aria-live="polite">
                    <span>{selectedCategory ? `${selectedCategory.name} · ${selectedCategory.share}` : 'TOTAL'}</span>
                    <strong>{selectedCategory ? selectedCategory.amount : dashboardWholeFormatter.format(dashboardData.total)}</strong>
                  </div>
                </div>
              </div>
              <div className="category-list">
                {dashboardData.categories.map((category) => (
                  <button
                    aria-label={`${category.name}: ${category.amount}, ${category.share}`}
                    aria-pressed={selectedCategoryName === category.name}
                    className={`category-row${selectedCategoryName === category.name ? ' category-row--selected' : ''}`}
                    key={category.name}
                    onClick={() => setSelectedCategoryName(category.name)}
                    type="button"
                  >
                    <span className={`category-icon category-icon--${category.color}`}><Icon name={category.icon} size={16} /></span>
                    <span className="category-name">{category.name}</span>
                    <span className="category-share">{category.share}</span>
                    <strong className="category-amount">{category.amount}</strong>
                  </button>
                ))}
              </div>
            </article>
          </section>

          <section className="panel transactions-panel">
            <div className="panel-heading transactions-heading">
              <div><span className="section-kicker">THE LATEST</span><h2>Recent transactions</h2></div>
              <button className="view-all" onClick={() => navigateFromHeader('payment-history')} type="button">View all <Icon name="arrow" size={16} /></button>
            </div>
            <div className="transaction-table">
              <div className="transaction-header"><span>MERCHANT</span><span>DATE</span><span>STATUS</span><span className="amount-heading">AMOUNT</span></div>
              {dashboardData.transactions.length > 0 ? dashboardData.transactions.map((transaction) => (
                <TransactionRow
                  key={transaction.name}
                  onSelect={setSelectedTransaction}
                  transaction={transaction}
                />
              )) : <p className="period-transactions-empty">No payments in this period.</p>}
            </div>
          </section>
            </>
          )}
          <footer className="page-footer"><span>© {currentYear} Mandate Pay</span><span>Your money, mindfully managed.</span></footer>
        </div>
        {selectedTransaction && (
          <DetailsDialog onClose={() => setSelectedTransaction(null)} titleId="transaction-detail-title">
              <div className="transaction-detail-heading">
                <div>
                  <span className="section-kicker">PAYMENT DETAILS</span>
                  <h2 id="transaction-detail-title">{selectedTransaction.name}</h2>
                </div>
                <button
                  aria-label="Close transaction details"
                  className="popover-close"
                  data-dialog-initial-focus
                  onClick={() => setSelectedTransaction(null)}
                  type="button"
                >
                  Close
                </button>
              </div>
              <strong className="transaction-detail-amount">{selectedTransaction.amount}</strong>
              <div className="transaction-detail-list">
                <div><span>STATUS</span><strong>Completed</strong></div>
                <div><span>CATEGORY</span><strong>{selectedTransaction.category}</strong></div>
                <div><span>DATE</span><strong>{selectedTransaction.date}</strong></div>
                <div><span>PAYMENT TYPE</span><strong>{selectedTransaction.detail}</strong></div>
              </div>
          </DetailsDialog>
        )}
      </main>
    </div>
  )
}

export default App
