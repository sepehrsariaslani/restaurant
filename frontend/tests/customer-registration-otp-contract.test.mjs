import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const page = fs.readFileSync(path.join(here, '../src/pages/CustomerLoginPage.vue'), 'utf8')
const api = fs.readFileSync(path.join(here, '../src/utils/api.js'), 'utf8')

test('customer registration is mobile-OTP based and does not require an email link', () => {
  assert.doesNotMatch(page, /customerRegisterWithEmail/)
  assert.doesNotMatch(page, /customerVerifyEmailRegistration/)
  assert.match(page, /sendOtpAPI\(\{ mobile: registrationMobile\.value \}\)/)
  assert.match(page, /register_profile/)
  assert.match(page, /mobile_verification_token/)
  assert.match(page, /!registerEmail\.value\.trim\(\) \|\| registerEmail\.value\.trim\(\)\.includes\('@'\)/)
})

test('customer API exposes the verified-mobile registration and password-change payloads', () => {
  assert.match(api, /mobile_verification_token/)
  assert.match(api, /changeCustomerPassword/)
})
