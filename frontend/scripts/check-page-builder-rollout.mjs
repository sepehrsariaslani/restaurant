import { existsSync, readFileSync } from 'node:fs'

function read(path) {
  return readFileSync(new URL(path, import.meta.url), 'utf8')
}

const failures = []

if (!existsSync(new URL('../src/components/management/ManagementPageBuilderWorkspace.vue', import.meta.url))) {
  failures.push('missing reusable ManagementPageBuilderWorkspace component')
}

const siteSettings = read('../src/pages/management/ManagementSiteSettingsPage.vue')
if (!siteSettings.includes("value: 'layout'") && !siteSettings.includes("value: 'page-builder'")) {
  failures.push('site settings is missing the layout/page-builder authoring stage')
}
if (!siteSettings.includes('ManagementPageBuilderWorkspace')) {
  failures.push('site settings does not mount the shared page builder workspace')
}

const pageLayout = read('../../restaurant/page_layout.py')
for (const page of ['home', 'about', 'faq', 'product_groups']) {
  if (!pageLayout.includes(`"${page}"`)) {
    failures.push(`page_layout backend is missing support for ${page}`)
  }
}

const resolver = read('../src/utils/pageLayout.js')
for (const marker of ['export function resolvePageLayout', 'export function hasStoredPageLayout']) {
  if (!resolver.includes(marker)) {
    failures.push(`page layout resolver is missing ${marker}`)
  }
}
if (!resolver.includes('const storedBlocks = asArray(stored?.blocks)')) {
  failures.push('page layout resolver does not safely guard missing stored blocks')
}

const registry = read('../src/utils/blockRegistry.js')
for (const marker of [
  '{ value: "fullscreen"',
  '{ value: "banner"',
  '{ value: "foodbar"',
]) {
  if (!registry.includes(marker)) {
    failures.push(`hero block registry is missing variant marker: ${marker}`)
  }
}

if (!siteSettings.includes('applyThemeSettings')) {
  failures.push('site settings is missing applyThemeSettings wiring for theme draft preview')
}

const app = read('../src/App.vue')
if (!app.includes("page === 'management-home-builder'")) {
  failures.push('App.vue no longer exposes the compatibility route for management-home-builder')
}
if (!app.includes('entry-mode="home-builder"')) {
  failures.push('App.vue does not route management-home-builder into site settings compatibility mode')
}

for (const file of [
  '../src/pages/AboutUsPage.vue',
  '../src/pages/FaqPage.vue',
  '../src/pages/ProductGroupsPage.vue',
]) {
  const source = read(file)
  if (!source.includes('PageBlocksRenderer')) {
    failures.push(`${file} is not wired to render stored page layouts`)
  }
}

if (failures.length) {
  console.error('page builder rollout checks failed:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('page builder rollout checks OK')
