import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const read = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')
const app = read('../src/App.vue')
const api = read('../src/utils/api.js')
const nav = read('../src/components/management/ManagementLayout.vue')
const landing = read('../src/pages/RestaurantLandingPage.vue')
const footer = read('../src/components/SiteFooter.vue') + read('../src/components/SiteFooterMinimal.vue')
const hooks = read('../../restaurant/hooks.py')
const backend = read('../../restaurant/api_blog.py')
const editor = read('../src/pages/management/content/ManagementBlogPage.vue')
const childDoctype = read('../../restaurant/doctype/restaurant_blog_product/restaurant_blog_product.json')

test('blog routes, home, and both site footers are connected', () => {
  assert.match(app, /pathname === '\/blog'/)
  assert.match(app, /pathname\.startsWith\('\/blog\/'\)/)
  assert.match(app, /management-blog/)
  assert.match(hooks, /"from_route": "\/blog"/)
  assert.match(hooks, /"from_route": "\/blog\/<path:route>"/)
  assert.match(hooks, /"from_route": "\/management\/blog"/)
  assert.match(landing, /<BlogHighlights/)
  assert.match(footer, /href="\/blog"/)
  assert.match(nav, /url: "\/management\/blog"/)
})

test('blog posts link native Items and management endpoints enforce access', () => {
  assert.match(api, /getPublicBlogPost/)
  assert.match(api, /searchManagementBlogProducts/)
  assert.match(childDoctype, /"options": "Item"/)
  assert.match(backend, /_ensure_management_access\(\)/)
  assert.match(backend, /sanitize_html\(doc\.body_html/)
  assert.match(editor, /related_products/)
  assert.match(editor, /is_published/)
})
