const knownAreas = new Map([
  ['main hall', 'سالن اصلی'],
  ['terrace', 'تراس'],
  ['vip', 'سالن ویژه'],
  ['family', 'سالن خانواده'],
])

export function customerTableAreaLabel(value) {
  const original = String(value || '').trim()
  return knownAreas.get(original.toLowerCase()) || original || 'سالن'
}
