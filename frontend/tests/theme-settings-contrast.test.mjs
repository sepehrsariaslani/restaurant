import test from 'node:test'
import assert from 'node:assert/strict'
import { ensureThemeBorderContrast } from '../src/utils/themeContrast.js'

function luminance(hex) {
  const value = hex.replace('#', '')
  const channels = [0, 2, 4].map((offset) => Number(`0x${value.slice(offset, offset + 2)}`) / 255)
  const linear = channels.map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4)
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]
}

function contrastRatio(first, second) {
  const firstLuminance = luminance(first)
  const secondLuminance = luminance(second)
  return (Math.max(firstLuminance, secondLuminance) + 0.05) / (Math.min(firstLuminance, secondLuminance) + 0.05)
}

test('a border that matches the page surface is adjusted to a visible brand tint', () => {
  const border = ensureThemeBorderContrast('#FAFAFA', '#FAFAFA', '#2F5F47')

  assert.notEqual(border, '#FAFAFA')
  assert.ok(contrastRatio(border, '#FAFAFA') >= 3)
})

test('an already legible custom border keeps its selected color', () => {
  assert.equal(ensureThemeBorderContrast('#2F5F47', '#F4F7F3', '#2F5F47'), '#2F5F47')
})

test('a low contrast border also adapts for dark surfaces', () => {
  const border = ensureThemeBorderContrast('#38322E', '#2E2A27', '#C07050')

  assert.notEqual(border, '#38322E')
  assert.ok(contrastRatio(border, '#2E2A27') >= 3)
})
