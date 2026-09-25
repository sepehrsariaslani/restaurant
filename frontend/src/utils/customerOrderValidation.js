import { normalizeMobile } from './format.js'

export function coordinateNumber(value, min, max) {
  if (value == null || String(value).trim() === '') return null
  const number = Number(String(value).replace(/[۰-۹]/g, (d) => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d))).replace(/[٠-٩]/g, (d) => String('٠١٢٣٤٥٦٧٨٩'.indexOf(d))))
  return Number.isFinite(number) && number >= min && number <= max ? number : null
}

export function hasDeliveryCoordinates(address = {}) {
  return coordinateNumber(address.lat, -90, 90) !== null && coordinateNumber(address.lng, -180, 180) !== null
}

export function isValidCustomerMobile(value) {
  return /^09\d{9}$/.test(normalizeMobile(value))
}

export function vehicleComplete(vehicle = {}) {
  return ['type', 'color', 'plate'].every((key) => String(vehicle[key] || '').trim())
}

export function orderContextIssue(context = {}) {
  if (!context.order_type) return 'روش دریافت را انتخاب کنید.'
  if (!context.branch) return 'شعبه را انتخاب کنید.'
  if (context.order_type === 'delivery') {
    if (!String(context.address?.address_line || '').trim()) return 'نشانی تحویل را وارد کنید.'
    if (!hasDeliveryCoordinates(context.address)) return 'محل تحویل را روی نقشه انتخاب کنید.'
    if (context.out_of_range) return 'این نشانی خارج از محدوده ارسال شعبه است.'
  }
  if (context.order_type === 'pickup') {
    if (context.pickup_method === 'car' && !vehicleComplete(context.pickup_vehicle)) return 'مدل، رنگ و پلاک خودرو را کامل کنید.'
    if (context.pickup_time_type === 'scheduled' && !context.pickup_time) return 'ساعت تحویل را انتخاب کنید.'
  }
  if (context.order_type === 'dine_in' && !context.table) return 'میز خود را انتخاب کنید.'
  return ''
}

export function deliveryOutsideRadius(address, branch) {
  if (!hasDeliveryCoordinates(address) || !hasDeliveryCoordinates(branch) || !(Number(branch.delivery_radius_km) > 0)) return false
  const rad = (value) => value * Math.PI / 180
  const sourceLat = coordinateNumber(branch.lat, -90, 90)
  const targetLat = coordinateNumber(address.lat, -90, 90)
  const lat = rad(targetLat - sourceLat)
  const lng = rad(coordinateNumber(address.lng, -180, 180) - coordinateNumber(branch.lng, -180, 180))
  const a = Math.min(1, Math.sin(lat / 2) ** 2 + Math.cos(rad(sourceLat)) * Math.cos(rad(targetLat)) * Math.sin(lng / 2) ** 2)
  return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)) > Number(branch.delivery_radius_km)
}

export function reservationTimeIsFuture(date, time, now = new Date()) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !/^\d{2}:\d{2}$/.test(time)) return false
  return new Date(`${date}T${time}:00`).getTime() > now.getTime()
}
