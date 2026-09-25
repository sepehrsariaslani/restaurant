import test from 'node:test'
import assert from 'node:assert/strict'
import { buildMenuSections } from '../src/utils/menuSections.js'

const categories = [
  {
    slug: 'bar', title: 'بار',
    subcategories: [
      { slug: 'warm', title: 'بار گرم', sort_order: 2 },
      { slug: 'cold', title: 'بار سرد', sort_order: 1 },
    ],
  },
  { slug: 'drinks', title: 'نوشیدنی‌ها', subcategories: [] },
]

test('menu sections retain category order and configured subcategory order while showing every item once', () => {
  const items = [
    { slug: 'tea', category_slug: 'bar', subcategory_slug: 'warm', title: 'چای' },
    { slug: 'juice', category_slug: 'drinks', title: 'آبمیوه' },
    { slug: 'iced', category_slug: 'bar', subcategory_slug: 'cold', title: 'آیس لاته' },
    { slug: 'misc', category_slug: 'bar', title: 'ویژه' },
  ]
  const groups = buildMenuSections(categories, items)

  assert.deepEqual(groups.map((group) => group.slug), ['bar', 'drinks'])
  assert.deepEqual(groups[0].sections.map((section) => section.title), ['بار سرد', 'بار گرم', 'سایر موارد'])
  assert.deepEqual(groups.flatMap((group) => group.sections.flatMap((section) => section.items.map((item) => item.slug))), ['iced', 'tea', 'misc', 'juice'])
  assert.deepEqual(groups[0].subcategories.map((section) => section.slug), ['cold', 'warm'])
})

test('menu sections match native category and subcategory titles when slugs are absent', () => {
  const groups = buildMenuSections(categories, [
    { slug: 'tea', category_title: 'بار', subcategory_title: 'بار گرم', title: 'چای' },
    { slug: 'unused', category_title: 'ناموجود', title: 'محصول دیگر' },
  ])

  assert.deepEqual(groups.map((group) => group.slug), ['bar'])
  assert.deepEqual(groups[0].sections.map((section) => section.slug), ['warm'])
  assert.deepEqual(groups[0].sections[0].items.map((item) => item.slug), ['tea'])
})

test('menu sections sort products within each subcategory without changing section order', () => {
  const groups = buildMenuSections(categories, [
    { slug: 'expensive', category_slug: 'bar', subcategory_slug: 'cold', base_price: 200 },
    { slug: 'warm', category_slug: 'bar', subcategory_slug: 'warm', base_price: 150 },
    { slug: 'cheap', category_slug: 'bar', subcategory_slug: 'cold', base_price: 100 },
  ], 'price_asc')

  assert.deepEqual(groups[0].sections.map((section) => section.slug), ['cold', 'warm'])
  assert.deepEqual(groups[0].sections[0].items.map((item) => item.slug), ['cheap', 'expensive'])
})
