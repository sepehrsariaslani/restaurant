import { readFileSync } from 'node:fs'

function read(path) {
  return readFileSync(new URL(path, import.meta.url), 'utf8')
}

const failures = []

const app = read('../src/App.vue')
if (!app.includes("page === 'management-settings'")) {
  failures.push('App.vue is missing the management-settings route')
}
if (!app.includes('entry-mode="theme-settings"')) {
  failures.push('management-settings is not routed into site settings theme mode')
}

const layout = read('../src/components/management/ManagementLayout.vue')
if (!layout.includes('/management/site-settings?stage=theme')) {
  failures.push('management layout does not point panel settings to the site settings theme stage')
}

const siteSettings = read('../src/pages/management/ManagementSiteSettingsPage.vue')
for (const marker of [
  "value: 'identity'",
  "value: 'theme'",
  "value: 'layout'",
  "value: 'content'",
  "value: 'review'",
  'ManagementThemeStudio',
  'activeStage',
]) {
  if (!siteSettings.includes(marker)) {
    failures.push(`site settings is missing authoring flow marker: ${marker}`)
  }
}
if (siteSettings.includes("value: 'components'")) {
  failures.push('legacy components stage still exists in site settings')
}

const themeStudio = read('../src/components/management/ManagementThemeStudio.vue')
for (const marker of ['themePresets', 'saveThemeSettingsToServer', 'hydrateThemeSettingsFromServer']) {
  if (!themeStudio.includes(marker)) {
    failures.push(`theme studio is missing ${marker}`)
  }
}

if (failures.length) {
  console.error('site authoring flow checks failed:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('site authoring flow checks OK')
