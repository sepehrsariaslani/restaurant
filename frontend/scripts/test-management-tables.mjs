import assert from 'node:assert/strict'
import {
  buildTableLabelMap,
  buildTablesSummary,
  filterTablesBySearch,
  filterReservationsBySearch,
  filterSessionsBySearch,
  sortReservations,
  buildFloorTableCards,
  buildSelectedTableDetail,
} from '../src/utils/managementTables.js'

const tables = [
  { name: 'TBL-1', table_number: 'T01', location: 'سالن اصلی', status: 'occupied', is_active: 1, notes: '' },
  { name: 'TBL-2', table_number: 'T02', location: 'تراس', status: 'empty', is_active: 1, notes: '' },
]

const reservations = [
  { name: 'RES-2', customer_name: 'زهرا', mobile: '0912', branch: 'A', table: 'TBL-2', reservation_date: '2026-07-17', reservation_time: '20:00', guest_count: 2, status: 'pending', note: '' },
  { name: 'RES-1', customer_name: 'علی', mobile: '0935', branch: 'A', table: 'TBL-1', reservation_date: '2026-07-16', reservation_time: '18:00', guest_count: 4, status: 'confirmed', note: '' },
]

const sessions = [
  { name: 'SES-1', table: 'TBL-1', status: 'active', note: 'VIP', total_confirmed_amount: 3500000, opened_at: '2026-07-16 12:00:00', closed_at: '', customer_name: 'علی', customer_mobile: '0935', guest_count: 4 },
]

assert.deepEqual(buildTableLabelMap(tables), { 'TBL-1': 'T01', 'TBL-2': 'T02' })

assert.deepEqual(buildTablesSummary({ tables, reservations, sessions }), {
  totalTables: 2,
  emptyTables: 1,
  waitingTables: 0,
  occupiedTables: 1,
  reservations: 2,
  activeSessions: 1,
})

assert.equal(filterTablesBySearch(tables, sessions, reservations, 'علی').length, 1)
assert.equal(filterReservationsBySearch(reservations, tables, 'تراس').length, 1)
assert.equal(filterSessionsBySearch(sessions, tables, reservations, 'vip').length, 1)

assert.deepEqual(
  sortReservations(reservations).map((row) => row.name),
  ['RES-1', 'RES-2'],
)

const cards = buildFloorTableCards({ tables, sessions, reservations })
assert.equal(cards[0].name, 'TBL-1')
assert.equal(cards[0].session?.name, 'SES-1')
assert.equal(cards[0].reservation?.name, 'RES-1')
assert.equal(cards[0].statusTone, 'occupied')
assert.equal(cards[1].statusTone, 'empty')
assert.equal(cards[0].customerName, 'علی')
assert.equal(cards[0].guestCount, 4)

const detail = buildSelectedTableDetail({
  table: tables[0],
  session: sessions[0],
  reservation: reservations[1],
})
assert.equal(detail.table.table_number, 'T01')
assert.equal(detail.session.customer_name, 'علی')
assert.equal(detail.reservation.customer_name, 'علی')

console.log('management tables utility tests: PASS')
