function toSearchable(value) {
  return String(value || '').trim().toLowerCase()
}

function buildSessionMap(sessions = []) {
  const map = new Map()
  for (const row of sessions || []) {
    const table = String(row?.table || '').trim()
    if (!table || map.has(table)) continue
    map.set(table, row)
  }
  return map
}

function buildReservationMap(reservations = []) {
  const rows = sortReservations(reservations)
  const map = new Map()
  for (const row of rows) {
    const table = String(row?.table || '').trim()
    if (!table || map.has(table)) continue
    map.set(table, row)
  }
  return map
}

function buildReservationLabel(tableName, tableLabelMap = {}) {
  return String(tableLabelMap?.[tableName] || tableName || '').trim()
}

export function buildTableLabelMap(tables = []) {
  return (tables || []).reduce((acc, row) => {
    const key = String(row?.name || '').trim()
    if (!key) return acc
    acc[key] = String(row?.table_number || row?.name || '').trim() || key
    return acc
  }, {})
}

export function buildTablesSummary({ tables = [], reservations = [], sessions = [] } = {}) {
  const normalizedTables = tables || []
  return {
    totalTables: normalizedTables.length,
    emptyTables: normalizedTables.filter((row) => String(row?.status || '').toLowerCase() === 'empty').length,
    waitingTables: normalizedTables.filter((row) => String(row?.status || '').toLowerCase() === 'waiting').length,
    occupiedTables: normalizedTables.filter((row) => String(row?.status || '').toLowerCase() === 'occupied').length,
    reservations: (reservations || []).length,
    activeSessions: (sessions || []).filter((row) => String(row?.status || '').toLowerCase() === 'active').length,
  }
}

export function sortReservations(rows = []) {
  return [...(rows || [])].sort((a, b) => {
    const aKey = `${String(a?.reservation_date || '')} ${String(a?.reservation_time || '')}`.trim()
    const bKey = `${String(b?.reservation_date || '')} ${String(b?.reservation_time || '')}`.trim()
    return aKey.localeCompare(bKey)
  })
}

export function filterTablesBySearch(tables = [], sessions = [], reservations = [], search = '') {
  const needle = toSearchable(search)
  if (!needle) return tables || []

  const sessionMap = buildSessionMap(sessions)
  const reservationMap = buildReservationMap(reservations)

  return (tables || []).filter((table) => {
    const session = sessionMap.get(String(table?.name || '').trim())
    const reservation = reservationMap.get(String(table?.name || '').trim())
    const haystack = [
      table?.table_number,
      table?.name,
      table?.location,
      table?.status,
      table?.notes,
      session?.customer_name,
      session?.customer_mobile,
      session?.note,
      reservation?.customer_name,
      reservation?.mobile,
      reservation?.branch,
      reservation?.note,
    ]
      .map(toSearchable)
      .join(' ')
    return haystack.includes(needle)
  })
}

export function filterReservationsBySearch(reservations = [], tables = [], search = '') {
  const needle = toSearchable(search)
  if (!needle) return sortReservations(reservations)

  const tableLabelMap = buildTableLabelMap(tables)
  const tableMap = new Map((tables || []).map((row) => [String(row?.name || "").trim(), row]))
  return sortReservations(reservations).filter((row) => {
    const table = tableMap.get(String(row?.table || "").trim())
    const haystack = [
      row?.customer_name,
      row?.mobile,
      row?.branch,
      row?.status,
      row?.note,
      row?.table,
      buildReservationLabel(row?.table, tableLabelMap),
      table?.location,
      table?.table_number,
    ]
      .map(toSearchable)
      .join(' ')
    return haystack.includes(needle)
  })
}

export function filterSessionsBySearch(sessions = [], tables = [], reservations = [], search = '') {
  const needle = toSearchable(search)
  if (!needle) return sessions || []

  const tableLabelMap = buildTableLabelMap(tables)
  const reservationMap = buildReservationMap(reservations)
  return (sessions || []).filter((row) => {
    const reservation = reservationMap.get(String(row?.table || '').trim())
    const haystack = [
      row?.name,
      row?.table,
      buildReservationLabel(row?.table, tableLabelMap),
      row?.status,
      row?.note,
      row?.customer_name,
      row?.customer_mobile,
      reservation?.customer_name,
      reservation?.mobile,
    ]
      .map(toSearchable)
      .join(' ')
    return haystack.includes(needle)
  })
}

export function buildFloorTableCards({ tables = [], sessions = [], reservations = [] } = {}) {
  const sessionMap = buildSessionMap(sessions)
  const reservationMap = buildReservationMap(reservations)

  return (tables || []).map((table) => {
    const tableName = String(table?.name || '').trim()
    const session = sessionMap.get(tableName) || null
    const reservation = reservationMap.get(tableName) || null
    return {
      ...table,
      session,
      reservation,
      statusTone: String(table?.status || 'empty').toLowerCase() || 'empty',
      customerName: session?.customer_name || reservation?.customer_name || '',
      customerMobile: session?.customer_mobile || reservation?.mobile || '',
      guestCount: Number(session?.guest_count || reservation?.guest_count || 0) || 0,
      sessionTotal: Number(session?.total_confirmed_amount || 0) || 0,
      openedAt: String(session?.opened_at || '').trim(),
    }
  })
}

export function buildSelectedTableDetail({ table = null, session = null, reservation = null } = {}) {
  return {
    table: table || null,
    session: session || null,
    reservation: reservation || null,
  }
}
