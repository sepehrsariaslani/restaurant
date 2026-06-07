const REVIEWS_KEY = 'restaurant_item_reviews_v2'

function loadAll() {
  try {
    const raw = localStorage.getItem(REVIEWS_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (_) {
    return {}
  }
}

function saveAll(data) {
  try {
    localStorage.setItem(REVIEWS_KEY, JSON.stringify(data))
  } catch (_) {}
}

export function getItemReviews(slug = '') {
  const key = String(slug || '').trim()
  if (!key) return []
  const all = loadAll()
  return Array.isArray(all[key]) ? all[key] : []
}

export function addItemReview(slug = '', { author = '', rating = 5, comment = '' } = {}) {
  const key = String(slug || '').trim()
  if (!key) return null
  const all = loadAll()
  const reviews = Array.isArray(all[key]) ? all[key] : []
  const review = {
    id: `r_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    author: String(author || 'مهمان').trim() || 'مهمان',
    rating: Math.min(5, Math.max(1, Math.round(Number(rating) || 5))),
    comment: String(comment || '').trim(),
    date: new Date().toISOString(),
  }
  all[key] = [review, ...reviews].slice(0, 100)
  saveAll(all)
  return review
}

export function getAverageRating(slug = '') {
  const reviews = getItemReviews(slug)
  if (!reviews.length) return 0
  const sum = reviews.reduce((s, r) => s + Number(r.rating || 0), 0)
  return Math.round((sum / reviews.length) * 10) / 10
}

export function getReviewCount(slug = '') {
  return getItemReviews(slug).length
}
