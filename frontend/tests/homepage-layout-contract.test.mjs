import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const sourceRoot = new URL('../src/', import.meta.url)

async function source(path) {
  return readFile(new URL(path, sourceRoot), 'utf8')
}

test('homepage uses a compact section rhythm without changing other page spacing', async () => {
  const renderer = await source('components/blocks/PageBlocksRenderer.vue')

  assert.match(renderer, /'page-blocks--home': isHomePage/)
  assert.match(renderer, /\.page-blocks\s*\{[^}]*gap:\s*clamp\(1\.8rem, 4vw, 3\.2rem\);/s)
  assert.match(renderer, /\.page-blocks--home\s*\{[^}]*gap:\s*clamp\(1\.3rem, 2\.7vw, 2\.1rem\);/s)
})

test('homepage hero keeps its editable variant while taking less vertical space', async () => {
  const hero = await source('components/blocks/HeroBlock.vue')

  assert.match(hero, /const raw = String\(props\.variant \|\| 'fullscreen'\)/)
  assert.match(hero, /min-height:\s*clamp\(320px, 42vh, 440px\)/)
  assert.match(hero, /min-height:\s*clamp\(320px, 46svh, 420px\)/)
  assert.match(hero, /--ds-color-action-accent/)
})

test('public desktop navigation labels meet the updated reading size', async () => {
  const header = await source('components/AppHeader.vue')

  assert.match(header, /\.nav-link\s*\{[^}]*font-size:\s*0\.8rem;/s)
  assert.match(header, /--ds-color-action-primary/)
})

test('customer login uses the saved hero image and a restaurant-branded fallback', async () => {
  const login = await source('pages/CustomerLoginPage.vue')

  assert.match(login, /:src="heroImage"/)
  assert.match(login, /props\.boot\?\.branding\?\.hero_image/)
  assert.match(login, /veederakht-home-hero\.webp/)
  assert.doesNotMatch(login, /NooshYar%20Image\.png/)
})
