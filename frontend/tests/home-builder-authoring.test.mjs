import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import {
  decodeEscapedUnicode,
  mergeBuilderBoot,
  normalizeBuilderCategories,
  normalizeFeatureItems,
} from '../src/utils/homeBuilder.js'

const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

test('decodes legacy escaped Persian labels before rendering', () => {
  assert.equal(decodeEscapedUnicode('\\u0633\\u0627\\u0644\\u0645'), 'سالم')
  assert.equal(decodeEscapedUnicode('تازه'), 'تازه')
})

test('normalizes feature rows without losing valid icon keys', () => {
  assert.deepEqual(
    normalizeFeatureItems([
      { icon: 'leaf', title: '\\u0633\\u0627\\u0644\\u0645', description: '\\u062a\\u0627\\u0632\\u0647' },
      { icon: 'unknown-icon', title: 'سریع', description: '' },
    ]),
    [
      { icon: 'leaf', title: 'سالم', description: 'تازه' },
      { icon: 'sparkles', title: 'سریع', description: '' },
    ],
  )
})

test('normalizes real menu categories for the Builder preview', () => {
  assert.deepEqual(
    normalizeBuilderCategories([
      { name: 'Main Food', item_group_name: 'غذای اصلی', restaurant_slug: 'main-food', restaurant_sort_order: 2 },
      { slug: 'drinks', title: 'نوشیدنی', image: '/files/drinks.jpg', item_count: 4 },
    ]),
    [
      { name: 'Main Food', title: 'غذای اصلی', slug: 'main-food', image: '', item_count: 0, sort_order: 2, subcategories: [] },
      { name: '', title: 'نوشیدنی', slug: 'drinks', image: '/files/drinks.jpg', item_count: 4, sort_order: 0, subcategories: [] },
    ],
  )
})

test('merges menu boot data while preserving management draft content', () => {
  const merged = mergeBuilderBoot({
    baseBoot: { user: { name: 'manager' }, categories: [{ title: 'قدیمی' }], currency: 'IRR' },
    settings: { brand_name: 'رستوران من', hero_section_title: 'هیروی من' },
    heroSlides: [{ title: 'اسلاید' }],
    aboutSections: [{ title: 'داستان' }],
    faqItems: [{ question: 'سوال' }],
    menuBoot: {
      categories: [{ slug: 'fresh', title: 'تازه‌ها' }],
      featured_items: [{ slug: 'salad', title: 'سالاد' }],
      currency: 'TOMAN',
    },
  })

  assert.equal(merged.user.name, 'manager')
  assert.equal(merged.branding.name, 'رستوران من')
  assert.equal(merged.branding.hero_section_title, 'هیروی من')
  assert.deepEqual(merged.categories.map((row) => row.slug), ['fresh'])
  assert.deepEqual(merged.featured_items.map((row) => row.slug), ['salad'])
  assert.equal(merged.currency, 'TOMAN')
  assert.deepEqual(merged.hero_slides, [{ title: 'اسلاید' }])
  assert.deepEqual(merged.about_us_sections, [{ title: 'داستان' }])
  assert.deepEqual(merged.faq_items, [{ question: 'سوال' }])
})

test('declares the full-screen hero as a viewport-width block', () => {
  const heroSource = fs.readFileSync(path.join(sourceRoot, 'src/components/blocks/HeroBlock.vue'), 'utf8')
  assert.match(heroSource, /\.hero\.hero--fullscreen\s*\{[\s\S]*?width:\s*100%/)
  assert.match(heroSource, /\.hero-cover--fullscreen\s*\{[\s\S]*?min-height:\s*min\(100svh/)
})
