import test from 'node:test'
import assert from 'node:assert/strict'
import { coordinateNumber, hasDeliveryCoordinates, isValidCustomerMobile, vehicleComplete, orderContextIssue, deliveryOutsideRadius, reservationTimeIsFuture } from '../src/utils/customerOrderValidation.js'

test('delivery requires an explicitly chosen finite in-range point, including Persian coordinates', () => {
  for (const value of ['', ' ', null, undefined, 'NaN', 'Infinity']) assert.equal(coordinateNumber(value, -90, 90), null)
  assert.equal(hasDeliveryCoordinates({ lat: '', lng: '' }), false)
  assert.equal(hasDeliveryCoordinates({ lat: 91, lng: 51 }), false)
  assert.equal(hasDeliveryCoordinates({ lat: 35, lng: 181 }), false)
  assert.equal(hasDeliveryCoordinates({ lat: '۳۵.۷', lng: '٥١.٣' }), true)
  assert.equal(hasDeliveryCoordinates({ lat: 0, lng: 0 }), true)
})

test('phone and car validation reject incomplete inputs', () => {
  assert.equal(isValidCustomerMobile('۰۹۱۲ ۳۴۵ ۶۷۸۹'), true)
  for (const value of ['', '12345678901', '0912345']) assert.equal(isValidCustomerMobile(value), false)
  assert.equal(vehicleComplete({ type: 'پژو', color: ' ', plate: '۱۲ ب ۳۴۵' }), false)
  assert.equal(vehicleComplete({ type: 'پژو', color: 'سفید', plate: '۱۲ ب ۳۴۵' }), true)
})

test('each fulfillment method requires its own destination before checkout', () => {
  assert.ok(orderContextIssue({}))
  assert.ok(orderContextIssue({ order_type: 'pickup' }))
  assert.equal(orderContextIssue({ order_type: 'pickup', branch: 'company', pickup_method: 'walk' }), '')
  assert.ok(orderContextIssue({ order_type: 'pickup', branch: 'company', pickup_method: 'car' }))
  assert.equal(orderContextIssue({ order_type: 'pickup', branch: 'company', pickup_method: 'car', pickup_vehicle: { type: 'a', color: 'b', plate: 'c' } }), '')
  assert.ok(orderContextIssue({ order_type: 'dine_in', branch: 'company' }))
  assert.equal(orderContextIssue({ order_type: 'dine_in', branch: 'company', table: 'T1' }), '')
  assert.ok(orderContextIssue({ order_type: 'delivery', branch: 'company', address: { address_line: 'خانه' } }))
  const delivery = { order_type: 'delivery', branch: 'company', address: { address_line: 'خانه', lat: 35, lng: 51 } }
  assert.equal(orderContextIssue(delivery), '')
  assert.ok(orderContextIssue({ ...delivery, out_of_range: true }))
})

test('radius calculation handles localized digits without accepting out-of-zone addresses', () => {
  const branch = { lat: 35.7, lng: 51.3, delivery_radius_km: 2 }
  assert.equal(deliveryOutsideRadius({ lat: '۳۵.۷۰۱', lng: '۵۱.۳۰۱' }, branch), false)
  assert.equal(deliveryOutsideRadius({ lat: '۳۵.۸', lng: '۵۱.۳' }, branch), true)
  assert.equal(deliveryOutsideRadius({ lat: 35.8, lng: 51.3 }, { ...branch, delivery_radius_km: 0 }), false)
})

test('reservations reject past, missing, and invalid times', () => {
  const now = new Date('2026-09-25T13:00:00')
  assert.equal(reservationTimeIsFuture('2026-09-25', '13:00', now), false)
  assert.equal(reservationTimeIsFuture('2026-09-25', '12:30', now), false)
  assert.equal(reservationTimeIsFuture('2026-09-25', '13:30', now), true)
  assert.equal(reservationTimeIsFuture('2026-09-26', '12:00', now), true)
  assert.equal(reservationTimeIsFuture('', '', now), false)
  assert.equal(reservationTimeIsFuture('2026-09-25', '25:00', now), false)
})
