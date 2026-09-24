export function isCustomerCompany(row = {}) {
  const branchId = String(row.id || row.name || '').trim()
  const company = String(row.company || '').trim()

  return Boolean(
    branchId &&
      company === branchId &&
      Number(row.is_active) !== 0 &&
      row.isOpen !== false,
  )
}

function normalizeBranchLabel(value) {
  return String(value || '')
    .normalize('NFKC')
    .replace(/[\s\u200c-\u200f\uFEFF]/g, '')
    .toLocaleLowerCase('fa')
}

export function findCustomerCompanyBranch(rows = [], value = '') {
  const expected = normalizeBranchLabel(value)
  if (!expected) return null

  return rows.find((row) => [row?.id, row?.name, row?.title].some((label) => normalizeBranchLabel(label) === expected)) || null
}

export function isCustomerPickupCompany(row = {}) {
  return isCustomerCompany(row) && row.pickup_available === true
}

export function isCustomerDeliveryCompany(row = {}) {
  return isCustomerCompany(row) && row.delivery_available === true
}

export function resolveDeliveryCompanySelection(rows = [], selectedId = '') {
  const available = rows.filter(isCustomerDeliveryCompany)
  const selected = String(selectedId || '').trim()
  if (available.some((row) => String(row.id || row.name || '').trim() === selected)) return selected
  return available.length === 1 ? String(available[0].id || available[0].name || '').trim() : ''
}
