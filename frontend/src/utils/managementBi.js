function toNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function normalizeDate(value) {
  if (!value) {
    return ''
  }
  const text = String(value)
  return text.length >= 10 ? text.slice(0, 10) : text
}

function toDate(value) {
  const base = normalizeDate(value)
  const parsed = new Date(base)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function addDays(value, days) {
  const date = toDate(value) || new Date()
  date.setDate(date.getDate() + days)
  return date.toISOString().slice(0, 10)
}

function dayDiff(dateA, dateB) {
  const a = toDate(dateA)
  const b = toDate(dateB)
  if (!a || !b) {
    return 0
  }
  const diff = Math.round((b.getTime() - a.getTime()) / 86400000)
  return Number.isFinite(diff) ? diff : 0
}

function percentChange(current, previous) {
  const currentValue = toNumber(current, 0)
  const previousValue = toNumber(previous, 0)
  if (!previousValue) {
    return currentValue ? 100 : 0
  }
  return ((currentValue - previousValue) * 100) / previousValue
}

function dateRangeList(dateFrom, dateTo) {
  const start = toDate(dateFrom)
  const end = toDate(dateTo)
  if (!start || !end) {
    return []
  }

  const rows = []
  const cursor = new Date(start)
  while (cursor <= end) {
    rows.push(cursor.toISOString().slice(0, 10))
    cursor.setDate(cursor.getDate() + 1)
  }
  return rows
}

function dateLabel(dateText) {
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      month: 'numeric',
      day: 'numeric',
    }).format(new Date(dateText))
  } catch (dateErr) {
    return dateText
  }
}

function mean(values) {
  if (!values.length) {
    return 0
  }
  const total = values.reduce((sum, value) => sum + toNumber(value, 0), 0)
  return total / values.length
}

function median(values) {
  if (!values.length) {
    return 0
  }
  const sorted = [...values].map((value) => toNumber(value, 0)).sort((a, b) => a - b)
  const middle = Math.floor(sorted.length / 2)
  if (sorted.length % 2 === 0) {
    return (sorted[middle - 1] + sorted[middle]) / 2
  }
  return sorted[middle]
}

function uniqueCustomerKey(order) {
  const mobile = String(order?.mobile || '').replace(/\D/g, '')
  if (mobile) {
    return `m:${mobile}`
  }
  return `n:${String(order?.customer_name || 'unknown').trim().toLowerCase()}`
}

function parseDiscountFromNote(noteText, baseAmount) {
  const note = String(noteText || '')
  const percentMatch = note.match(/DISCOUNT\s*(\d+(?:\.\d+)?)\s*%/i)
  if (percentMatch) {
    return (toNumber(baseAmount, 0) * toNumber(percentMatch[1], 0)) / 100
  }

  const amountMatch = note.match(/تخفیف\s*[:：]?\s*([\d,\.]+)/)
  if (amountMatch) {
    return toNumber(String(amountMatch[1]).replace(/,/g, ''), 0)
  }

  return 0
}

export function getPreviousWindow(dateFrom, dateTo) {
  const days = Math.max(dayDiff(dateFrom, dateTo) + 1, 1)
  const prevTo = addDays(dateFrom, -1)
  const prevFrom = addDays(prevTo, -(days - 1))
  return {
    date_from: prevFrom,
    date_to: prevTo,
  }
}

export function buildSalesFinancialSeries({
  salesTrendRows = [],
  cancellationRows = [],
  dateFrom = '',
  dateTo = '',
} = {}) {
  const dates = dateRangeList(dateFrom, dateTo)
  const salesByDate = {}
  const costByDate = {}
  let hasCostData = false
  for (const row of salesTrendRows || []) {
    salesByDate[normalizeDate(row.date)] = toNumber(row.sales, 0)
    const rawCost = row.cost
    if (rawCost !== undefined && rawCost !== null && rawCost !== '') {
      hasCostData = true
      costByDate[normalizeDate(row.date)] = toNumber(rawCost, 0)
    }
  }

  const returnsByDate = {}
  for (const row of cancellationRows || []) {
    const key = normalizeDate(row.created_at)
    returnsByDate[key] = toNumber(returnsByDate[key], 0) + toNumber(row.amount, 0)
  }

  const salesValues = dates.map((date) => toNumber(salesByDate[date], 0))
  const expectedBase = mean(salesValues)

  const expectedValues = dates.map((date, idx) => {
    const trailing = salesValues.slice(Math.max(0, idx - 6), idx + 1)
    const rolling = trailing.length ? mean(trailing) : expectedBase
    return Math.round(rolling)
  })

  const costValues = hasCostData ? dates.map((date) => toNumber(costByDate[date], 0)) : []
  const returnValues = dates.map((date) => toNumber(returnsByDate[date], 0))
  const costPercentValues = hasCostData
    ? salesValues.map((value, idx) => {
        if (!value) {
          return 0
        }
        return Number(((costValues[idx] * 100) / value).toFixed(2))
      })
    : []

  const labels = dates.map(dateLabel)

  return {
    labels,
    dates,
    salesValues,
    expectedValues,
    costValues,
    returnValues,
    costPercentValues,
    hasCostData,
    latestSales: salesValues[salesValues.length - 1] || 0,
    latestExpected: expectedValues[expectedValues.length - 1] || 0,
  }
}

export function buildHourlySeries(hourRows = []) {
  const rows = Array.from({ length: 24 }, (_, hour) => {
    const found = (hourRows || []).find((row) => Number(row.hour) === hour) || {}
    return {
      hour,
      sales: toNumber(found.sales, 0),
      orders: toNumber(found.orders, 0),
    }
  })

  const labels = rows.map((row) => `${row.hour.toString().padStart(2, '0')}:00`)
  const salesValues = rows.map((row) => row.sales)
  const expected = Math.round(mean(salesValues))
  const expectedValues = rows.map(() => expected)

  return {
    labels,
    salesValues,
    expectedValues,
    orderValues: rows.map((row) => row.orders),
  }
}

export function buildKpiSet({
  orders = [],
  salesSeries = {},
  previousOrders = [],
  previousSalesSeries = {},
  operationalMetrics = {},
  previousOperationalMetrics = {},
  lowStockCount = 0,
  outStockCount = 0,
} = {}) {
  const latestDate = salesSeries?.dates?.[salesSeries.dates.length - 1] || ''
  const latestPrevDate = previousSalesSeries?.dates?.[previousSalesSeries.dates.length - 1] || ''

  const dailyOrders = (orders || []).filter((row) => normalizeDate(row.created_at) === latestDate).length
  const prevDailyOrders = (previousOrders || []).filter((row) => normalizeDate(row.created_at) === latestPrevDate).length

  const todayCustomers = new Set(
    (orders || [])
      .filter((row) => normalizeDate(row.created_at) === latestDate)
      .map((row) => uniqueCustomerKey(row)),
  )
  const prevCustomers = new Set(
    (previousOrders || [])
      .filter((row) => normalizeDate(row.created_at) === latestPrevDate)
      .map((row) => uniqueCustomerKey(row)),
  )

  const dailyRevenue = toNumber(salesSeries.latestSales, 0)
  const prevDailyRevenue = toNumber(previousSalesSeries.latestSales, 0)
  const expectedSales = toNumber(salesSeries.latestExpected, 0)
  const prevExpectedSales = toNumber(previousSalesSeries.latestExpected, 0)
  const hasCostData = Boolean(salesSeries.hasCostData)
  const prevHasCostData = Boolean(previousSalesSeries.hasCostData)
  const dailyBalance = hasCostData
    ? Math.max(dailyRevenue - toNumber(salesSeries.costValues?.[salesSeries.costValues.length - 1], 0), 0)
    : null
  const prevDailyBalance = prevHasCostData
    ? Math.max(
        prevDailyRevenue - toNumber(previousSalesSeries.costValues?.[previousSalesSeries.costValues.length - 1], 0),
        0,
      )
    : null

  return [
    {
      key: 'daily_balance',
      label: 'موجودی روز',
      value: dailyBalance,
      unit: 'money',
      change: dailyBalance === null || prevDailyBalance === null ? null : percentChange(dailyBalance, prevDailyBalance),
      subtitle: hasCostData ? '' : 'داده بهای تمام‌شده ثبت نشده',
    },
    {
      key: 'daily_revenue',
      label: 'درآمد روز',
      value: dailyRevenue,
      unit: 'money',
      change: percentChange(dailyRevenue, prevDailyRevenue),
    },
    {
      key: 'expected_sales',
      label: 'انتظار فروش روز',
      value: expectedSales,
      unit: 'money',
      change: percentChange(expectedSales, prevExpectedSales),
    },
    {
      key: 'daily_orders',
      label: 'تعداد سفارش های روز',
      value: dailyOrders,
      unit: 'count',
      change: percentChange(dailyOrders, prevDailyOrders),
    },
    {
      key: 'daily_customers',
      label: 'مشتریان روز',
      value: todayCustomers.size,
      unit: 'count',
      change: percentChange(todayCustomers.size, prevCustomers.size),
    },
    {
      key: 'satisfaction',
      label: 'میانگین رضایت کاربران',
      value: operationalMetrics.satisfaction_avg ?? null,
      unit: 'score',
      subtitle:
        operationalMetrics.satisfaction_avg === null || operationalMetrics.satisfaction_avg === undefined
          ? 'بدون داده نظرسنجی'
          : `از10 | ${toNumber(operationalMetrics.satisfaction_count, 0).toLocaleString('fa-IR')} نظر`,
      change: percentChange(
        toNumber(operationalMetrics.satisfaction_avg, 0),
        toNumber(previousOperationalMetrics.satisfaction_avg, 0),
      ),
    },
    {
      key: 'avg_delivery',
      label: 'میانگین زمان تحویل',
      value: operationalMetrics.avg_delivery_mins ?? null,
      unit: 'minutes',
      change: percentChange(
        toNumber(operationalMetrics.avg_delivery_mins, 0),
        toNumber(previousOperationalMetrics.avg_delivery_mins, 0),
      ),
    },
    {
      key: 'max_delivery',
      label: 'دیرترین زمان تحویل',
      value: operationalMetrics.max_delivery_mins ?? null,
      unit: 'minutes',
      change: percentChange(
        toNumber(operationalMetrics.max_delivery_mins, 0),
        toNumber(previousOperationalMetrics.max_delivery_mins, 0),
      ),
      action: operationalMetrics.max_delivery_order
        ? `/desk/orders?order=${encodeURIComponent(operationalMetrics.max_delivery_order)}`
        : '/desk/orders',
      actionLabel: 'مشاهده فاکتور',
    },
    {
      key: 'low_stock',
      label: 'کالاهای نزدیک به اتمام',
      value: toNumber(lowStockCount, 0),
      unit: 'count',
      change: 0,
      action: '/desk/products',
      actionLabel: 'مشاهده',
    },
    {
      key: 'out_stock',
      label: 'کالاهای تمام شده',
      value: toNumber(outStockCount, 0),
      unit: 'count',
      change: 0,
      action: '/desk/products',
      actionLabel: 'مشاهده',
    },
  ]
}

export function buildPerformerRows({ mode = 'staff', orders = [], cashierRows = [], productMap = {} } = {}) {
  if (mode === 'staff') {
    return (cashierRows || []).slice(0, 8).map((row) => ({
      key: row.cashier,
      label: row.cashier || 'نامشخص',
      value: toNumber(row.sales, 0),
    }))
  }

  if (mode === 'place') {
    const grouped = {}
    for (const row of orders || []) {
      const key = row.channel || 'unknown'
      grouped[key] = toNumber(grouped[key], 0) + toNumber(row.grand_total, 0)
    }
    return Object.entries(grouped)
      .map(([channel, value]) => ({
        key: channel,
        label: channel,
        value,
      }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8)
  }

  const grouped = {}
  for (const order of orders || []) {
    for (const item of order.items || []) {
      const title = String(item.title || '').trim() || 'بدون دسته'
      const mapped = productMap[title] || 'بدون دسته بندی'
      grouped[mapped] = toNumber(grouped[mapped], 0) + toNumber(item.line_total, 0)
    }
  }

  return Object.entries(grouped)
    .map(([label, value]) => ({
      key: label,
      label,
      value,
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8)
}

export function buildChannelDistribution(channelRows = [], mode = 'money') {
  const mapped = {}
  for (const row of channelRows || []) {
    const channel = String(row.channel || '').toLowerCase()
    let label = `کانال ${channel || 'نامشخص'}`
    if (channel === 'takeaway') {
      label = 'بیرون بر-مشتری-سفارش از کارکنان'
    } else if (channel === 'delivery') {
      label = 'بیرون بر-پیک-سفارش تلفنی'
    } else if (channel === 'dine_in') {
      label = 'حضوری-سفارش از کارکنان'
    }

    if (!mapped[label]) {
      mapped[label] = { label, sales: 0, orders: 0 }
    }
    mapped[label].sales += toNumber(row.sales, 0)
    mapped[label].orders += toNumber(row.orders, 0)
  }

  return Object.values(mapped)
    .map((row) => ({
      key: row.label,
      label: row.label,
      value: mode === 'count' ? row.orders : row.sales,
    }))
    .sort((a, b) => b.value - a.value)
}

export function buildCustomerAnalytics({ orders = [], customers = [], dateFrom = '', dateTo = '' } = {}) {
  const revenueOrders = (orders || []).filter((row) => String(row.status || '').toLowerCase() !== 'cancelled')
  const orderedByTime = [...revenueOrders].sort((a, b) => String(a.created_at || '').localeCompare(String(b.created_at || '')))

  const days = dateRangeList(dateFrom, dateTo)
  const dailyMap = {}
  for (const day of days) {
    dailyMap[day] = { new_customers: 0, returning_customers: 0 }
  }

  const seen = new Set()
  for (const row of orderedByTime) {
    const key = uniqueCustomerKey(row)
    const day = normalizeDate(row.created_at)
    if (!dailyMap[day]) {
      continue
    }
    if (seen.has(key)) {
      dailyMap[day].returning_customers += 1
    } else {
      dailyMap[day].new_customers += 1
      seen.add(key)
    }
  }

  const grouped = {}
  for (const row of revenueOrders) {
    const key = uniqueCustomerKey(row)
    if (!grouped[key]) {
      grouped[key] = {
        key,
        customer_name: row.customer_name || 'مشتری',
        mobile: row.mobile || '',
        orders_count: 0,
        total_spent: 0,
        discount_total: 0,
        debt_total: 0,
        last_order_at: row.created_at || '',
      }
    }

    grouped[key].orders_count += 1
    grouped[key].total_spent += toNumber(row.grand_total, 0)
    grouped[key].discount_total += parseDiscountFromNote(row.note, row.grand_total)

    if (String(row.payment_status || '').toLowerCase() !== 'paid') {
      grouped[key].debt_total += toNumber(row.grand_total, 0)
    }

    if (String(row.created_at || '') > String(grouped[key].last_order_at || '')) {
      grouped[key].last_order_at = row.created_at
    }
  }

  const referenceDate = toDate(dateTo) || new Date()
  const aggregates = Object.values(grouped)
  const totals = aggregates.map((row) => row.total_spent)
  const highSpent = median(totals)

  const loyalty = {
    loyal: 0,
    near_loyal: 0,
    new_customer: 0,
    lost: 0,
  }

  const values = {
    best: 0,
    high_volume: 0,
    frequent: 0,
    at_risk: 0,
  }

  for (const row of aggregates) {
    const recency = dayDiff(normalizeDate(row.last_order_at), referenceDate.toISOString().slice(0, 10))

    if (recency > 45) {
      loyalty.lost += 1
    } else if (row.orders_count >= 4 && recency <= 15) {
      loyalty.loyal += 1
    } else if (row.orders_count <= 1) {
      loyalty.new_customer += 1
    } else {
      loyalty.near_loyal += 1
    }

    if (row.orders_count >= 4 && row.total_spent >= highSpent) {
      values.best += 1
    } else if (row.total_spent >= highSpent) {
      values.high_volume += 1
    } else if (row.orders_count >= 3) {
      values.frequent += 1
    } else {
      values.at_risk += 1
    }
  }

  const discountRows = [...aggregates]
    .sort((a, b) => toNumber(b.discount_total, 0) - toNumber(a.discount_total, 0))
    .slice(0, 8)
  const debtRows = [...aggregates]
    .sort((a, b) => toNumber(b.debt_total, 0) - toNumber(a.debt_total, 0))
    .slice(0, 8)

  return {
    labels: days.map(dateLabel),
    newSeries: days.map((day) => dailyMap[day]?.new_customers || 0),
    returningSeries: days.map((day) => dailyMap[day]?.returning_customers || 0),
    loyalty,
    values,
    totalCustomers: aggregates.length || customers.length || 0,
    discountRows,
    debtRows,
  }
}

export function buildMenuEngineering(topProducts = []) {
  const rows = (topProducts || []).map((row) => ({
    product: row.product_title || 'بدون نام',
    amount: toNumber(row.amount, 0),
    qty: toNumber(row.qty, 0),
    avg_price: row.qty ? toNumber(row.amount, 0) / toNumber(row.qty, 1) : 0,
  }))

  const medianQty = median(rows.map((row) => row.qty))
  const medianAvgPrice = median(rows.map((row) => row.avg_price))

  const matrix = {
    stars: 0,
    puzzles: 0,
    plowhorses: 0,
    dogs: 0,
  }

  for (const row of rows) {
    const highPopularity = row.qty >= medianQty
    const highProfitability = row.avg_price >= medianAvgPrice

    if (highPopularity && highProfitability) {
      matrix.stars += 1
    } else if (!highPopularity && highProfitability) {
      matrix.puzzles += 1
    } else if (highPopularity && !highProfitability) {
      matrix.plowhorses += 1
    } else {
      matrix.dogs += 1
    }
  }

  const bestSelling = [...rows].sort((a, b) => b.amount - a.amount).slice(0, 10)
  const lowSelling = [...rows].sort((a, b) => a.amount - b.amount).slice(0, 10)
  const popular = [...rows].sort((a, b) => b.qty - a.qty).slice(0, 10)
  const unpopular = [...rows].sort((a, b) => a.qty - b.qty).slice(0, 10)

  return {
    matrix,
    bestSelling,
    lowSelling,
    popular,
    unpopular,
  }
}

export function buildLostOrderDataset({ orderStatusRows = [], cancellationRows = [] } = {}) {
  const summary = {
    total: 0,
    lost_total: 0,
    cancelled_invoice: 0,
    voided: 0,
  }

  for (const row of orderStatusRows || []) {
    const status = String(row.status || '').toLowerCase()
    const count = toNumber(row.orders, 0)
    summary.total += count
    if (status === 'cancelled') {
      summary.cancelled_invoice += count
      summary.lost_total += count
    }
    if (status === 'void' || status === 'voided') {
      summary.voided += count
      summary.lost_total += count
    }
  }

  const byDate = {}
  for (const row of cancellationRows || []) {
    const date = normalizeDate(row.created_at)
    byDate[date] = (byDate[date] || 0) + 1
  }

  const labels = Object.keys(byDate).sort().map(dateLabel)
  const values = Object.keys(byDate)
    .sort()
    .map((date) => byDate[date])

  return {
    summary,
    labels,
    values,
  }
}
