import jalaali from 'jalaali-js'

export function gregorianToJalali(gy, gm, gd) {
  const j = jalaali.toJalaali(gy, gm, gd)
  return { year: j.jy, month: j.jm, day: j.jd }
}

export function jalaliToGregorian(jy, jm, jd) {
  const g = jalaali.toGregorian(jy, jm, jd)
  return { year: g.gy, month: g.gm, day: g.gd }
}

export function getJalaliDaysInMonth(jy, jm) {
  return jalaali.jalaaliMonthLength(jy, jm)
}

export function formatGregorianDate(date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export function formatJalaliDate(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-').map(Number)
  const j = jalaali.toJalaali(y, m, d)
  return `${j.jy}/${String(j.jm).padStart(2, '0')}/${String(j.jd).padStart(2, '0')}`
}

export function formatJalaliDisplay(dateStr) {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-').map(Number)
  if (!y || !m || !d) return ''
  const j = jalaali.toJalaali(y, m, d)
  const persianNums = (n) => String(n).replace(/\d/g, (x) => '۰۱۲۳۴۵۶۷۸۹'[x])
  return `${persianNums(j.jy)}/${persianNums(String(j.jm).padStart(2, '0'))}/${persianNums(String(j.jd).padStart(2, '0'))}`
}

export function formatJalaliNumericDate(dateStr, sep = '/') {
  if (!dateStr) return ''
  const [y, m, d] = dateStr.split('-').map(Number)
  if (!y || !m || !d) return ''
  const j = jalaali.toJalaali(y, m, d)
  const persianNums = (n) => String(n).replace(/\d/g, (x) => '۰۱۲۳۴۵۶۷۸۹'[x])
  return `${persianNums(j.jy)}${sep}${persianNums(String(j.jm).padStart(2, '0'))}${sep}${persianNums(String(j.jd).padStart(2, '0'))}`
}

export function toPersianDigits(n) {
  return String(n).replace(/\d/g, (x) => '۰۱۲۳۴۵۶۷۸۹'[x])
}
