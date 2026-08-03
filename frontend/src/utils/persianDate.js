import { toJalaali } from 'jalaali-js'

const PERSIAN_DIGITS = '۰۱۲۳۴۵۶۷۸۹'

export function toPersianDigits(value) {
  return String(value ?? '').replace(/\d/g, (digit) => PERSIAN_DIGITS[Number(digit)])
}

export function formatPersianDate(value, fallback = '—') {
  const raw = String(value ?? '').trim()
  const match = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
  if (!match) return raw || fallback

  try {
    const { jy, jm, jd } = toJalaali(Number(match[1]), Number(match[2]), Number(match[3]))
    return toPersianDigits(`${jy}/${String(jm).padStart(2, '0')}/${String(jd).padStart(2, '0')}`)
  } catch (_) {
    return raw || fallback
  }
}
