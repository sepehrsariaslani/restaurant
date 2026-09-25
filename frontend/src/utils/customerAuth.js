const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'

export function hasCustomerSession(storage = typeof localStorage !== 'undefined' ? localStorage : null) {
  if (!storage) return false

  try {
    const auth = JSON.parse(storage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    return Boolean(String(auth?.mobile || '').trim())
  } catch {
    return false
  }
}

export function customerAccountHref(returnTo = '/customer/dashboard', storage = typeof localStorage !== 'undefined' ? localStorage : null) {
  const path = String(returnTo || '/customer/dashboard').trim()
  const safePath = path.startsWith('/') && !path.startsWith('//') && !path.includes('\\')
    ? path
    : '/customer/dashboard'

  return hasCustomerSession(storage)
    ? safePath
    : `/customer/login?redirect=${encodeURIComponent(safePath)}`
}
