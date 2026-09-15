const ROOT_ITEM_GROUP = 'All Item Groups'
const ROOT_ITEM_GROUP_LABEL = 'همه گروه‌ها'

function normalizeRows(rows = []) {
  return (Array.isArray(rows) ? rows : [])
    .map((row) => {
      const value = String(row?.value || row?.name || '').trim()
      if (!value) return null
      return {
        ...row,
        value,
        label: String(row?.label || row?.item_group_name || row?.title || value).trim(),
        parentValue: String(row?.parentValue || row?.parent_item_group || '').trim(),
        parentLabel: String(row?.parentLabel || row?.parent_label || '').trim(),
        path: String(row?.path || row?.item_group_path || '').trim(),
        isGroup: Number(row?.is_group || 0) === 1,
      }
    })
    .filter(Boolean)
}

function getLabel(row, fallback = '') {
  return String(row?.label || row?.item_group_name || row?.title || row?.name || fallback).trim()
}

function resolvePath(row, byValue) {
  if (row.path) return row.path
  const labels = [getLabel(row, row.value)]
  const seen = new Set([row.value])
  let parentValue = row.parentValue

  while (parentValue && parentValue !== ROOT_ITEM_GROUP && !seen.has(parentValue)) {
    seen.add(parentValue)
    const parent = byValue.get(parentValue)
    if (!parent) break
    labels.unshift(getLabel(parent, parentValue))
    parentValue = parent.parentValue
  }

  return labels.join(' / ')
}

export function buildItemGroupOptions(rows = []) {
  const normalized = normalizeRows(rows)
  const byValue = new Map(normalized.map((row) => [row.value, row]))

  return normalized
    .filter((row) => !row.isGroup)
    .map((row) => {
      const parentValue = row.parentValue || ROOT_ITEM_GROUP
      const parent = byValue.get(parentValue)
      const parentLabel = parent ? getLabel(parent, parentValue) : row.parentLabel || ROOT_ITEM_GROUP_LABEL
      return {
        value: row.value,
        label: resolvePath(row, byValue),
        parentValue,
        parentLabel,
      }
    })
    .sort((left, right) => {
      const leftLabel = String(left.label || '').split(' / ').pop()
      const rightLabel = String(right.label || '').split(' / ').pop()
      if (leftLabel === rightLabel) return 0
      return leftLabel < rightLabel ? -1 : 1
    })
}

export function getChildItemGroupOptions(rows = [], parentValue = '') {
  const normalizedParent = String(parentValue || '').trim()
  if (!normalizedParent) return buildItemGroupOptions(rows)
  return buildItemGroupOptions(rows).filter((row) => row.parentValue === normalizedParent)
}

export function resolveItemGroupSelection(rows = [], value = '') {
  const selectedValue = String(value || '').trim()
  const option = buildItemGroupOptions(rows).find((row) => row.value === selectedValue)
  if (!option) {
    return { itemGroup: selectedValue, parentItemGroup: '', path: '' }
  }
  return {
    itemGroup: option.value,
    parentItemGroup: option.parentValue,
    path: option.label,
  }
}

export { ROOT_ITEM_GROUP, ROOT_ITEM_GROUP_LABEL }
