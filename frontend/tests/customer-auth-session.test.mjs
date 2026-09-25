import test from 'node:test'
import assert from 'node:assert/strict'
import { customerAccountHref, hasCustomerSession } from '../src/utils/customerAuth.js'

function storageWith(value) {
  return {
    getItem(key) {
      return key === 'restaurant-customer-auth-v1' ? JSON.stringify(value) : null
    },
  }
}

test('a saved phone alone is not treated as an authenticated customer session', () => {
  const storage = storageWith({ mobile: '09123456789' })

  assert.equal(hasCustomerSession(storage), false)
  assert.equal(customerAccountHref('/customer/orders', storage), '/customer/login?redirect=%2Fcustomer%2Forders')
})

test('a verified customer token unlocks account routes', () => {
  const storage = storageWith({ mobile: '09123456789', customer_token: 'verified-session' })

  assert.equal(hasCustomerSession(storage), true)
  assert.equal(customerAccountHref('/customer/orders', storage), '/customer/orders')
})
