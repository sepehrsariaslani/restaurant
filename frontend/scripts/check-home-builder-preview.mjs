import { readFileSync } from 'node:fs'

const builderPage = readFileSync(
  new URL('../src/pages/management/ManagementHomeBuilderPage.vue', import.meta.url),
  'utf8',
)
const landingPage = readFileSync(
  new URL('../src/pages/RestaurantLandingPage.vue', import.meta.url),
  'utf8',
)

const failures = []

if (!builderPage.includes('<RestaurantLandingPage :key="previewKey" :boot="previewBoot" preview-mode />')) {
  failures.push('builder preview does not render RestaurantLandingPage in preview mode')
}

if (builderPage.includes('<HomePageRenderer :key="previewKey" :boot="previewBoot" />')) {
  failures.push('builder preview still renders bare HomePageRenderer')
}

if (!landingPage.includes('previewMode:')) {
  failures.push('RestaurantLandingPage is missing previewMode prop')
}

if (!landingPage.includes('<PublicHeader\n      v-if="!previewMode"')) {
  failures.push('RestaurantLandingPage does not gate the full public header in preview mode')
}

if (!landingPage.includes('class="home-preview-chrome"')) {
  failures.push('RestaurantLandingPage is missing compact preview chrome')
}

if (landingPage.includes(':preview="previewMode"')) {
  failures.push('RestaurantLandingPage still passes previewMode into the full PublicHeader')
}

if (!landingPage.includes('v-if="!previewMode && toastMessage"')) {
  failures.push('preview mode still allows toast overlay')
}

if (!landingPage.includes('v-if="!previewMode && cartCount > 0"')) {
  failures.push('preview mode still allows sticky cart overlay')
}

if (!landingPage.includes('v-if="!previewMode && siteComponents.footer_variant === \'full\'"')) {
  failures.push('preview mode still allows full footer')
}

if (failures.length) {
  console.error('home builder preview checks failed:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('home builder preview checks OK')
