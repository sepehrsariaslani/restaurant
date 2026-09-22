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
      { icon: 'leaf', image: '', title: 'سالم', description: 'تازه' },
      { icon: 'sparkles', image: '', title: 'سریع', description: '' },
    ],
  )
})

test('preserves feature images, empty icons, and authoring whitespace', () => {
  assert.deepEqual(
    normalizeFeatureItems(
      [{ icon: '', image: '/files/fresh.jpg', title: ' عنوان ', description: 'توضیح ' }],
      { preserveWhitespace: true },
    ),
    [{ icon: '', image: '/files/fresh.jpg', title: ' عنوان ', description: 'توضیح ' }],
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
  assert.match(heroSource, /\.hero-cover--fullscreen\s*\{[\s\S]*?min-height:\s*100svh/)
})

test('uses the canonical management image dropzone for authoring images', () => {
  const blockFormSource = fs.readFileSync(path.join(sourceRoot, 'src/components/management/builder/BlockPropsForm.vue'), 'utf8')
  const settingsSource = fs.readFileSync(path.join(sourceRoot, 'src/pages/management/ManagementSiteSettingsPage.vue'), 'utf8')
  assert.match(blockFormSource, /ManagementImageDropzone/)
  assert.match(settingsSource, /ManagementImageDropzone/)
  assert.doesNotMatch(settingsSource, /new FileReader\(\)/)
  assert.doesNotMatch(settingsSource, /v-model\.trim="webSettings\.hero_image"/)
})

test('renders feature editing through the shared icon selector and normalizer', () => {
  const blockFormSource = fs.readFileSync(path.join(sourceRoot, 'src/components/management/builder/BlockPropsForm.vue'), 'utf8')
  const featureBlockSource = fs.readFileSync(path.join(sourceRoot, 'src/components/blocks/FeaturesBlock.vue'), 'utf8')
  const registrySource = fs.readFileSync(path.join(sourceRoot, 'src/utils/blockRegistry.js'), 'utf8')
  assert.match(blockFormSource, /SearchableDropdown/)
  assert.doesNotMatch(blockFormSource, /placeholder="\\u[0-9a-fA-F]{4}/)
  assert.match(featureBlockSource, /normalizeFeatureItems/)
  assert.match(registrySource, /title: "\\u0633\\u0627\\u0644\\u0645"/)
  assert.match(registrySource, /title: "\\u0633\\u0628\\u06a9"/)
  assert.match(registrySource, /title: "\\u0633\\u0631\\u06cc\\u0639"/)
  assert.match(blockFormSource, /ManagementImageDropzone[\s\S]*updateFeature\(field, idx, 'image'/)
  assert.match(blockFormSource, /value: '', label: 'بدون آیکن'/)
  assert.match(featureBlockSource, /v-if="f\.icon"/)
  assert.match(featureBlockSource, /background-image/)
  assert.match(registrySource, /function optionalStr[\s\S]*value === undefined/)
})

test('opens category products in the same page through the interactive grid', () => {
  const categoriesSource = fs.readFileSync(path.join(sourceRoot, 'src/components/blocks/CategoriesBlock.vue'), 'utf8')
  const gridSource = fs.readFileSync(path.join(sourceRoot, 'src/components/CategoryExpandableGrid.vue'), 'utf8')
  assert.match(categoriesSource, /CategoryExpandableGrid/)
  assert.match(categoriesSource, /@quick-add/)
  assert.match(gridSource, /getMenuItems/)
  assert.match(gridSource, /category_slug:\s*cat\.slug/)
  assert.match(gridSource, /v-if="selectedCategory"/)
})

test('keeps the Builder preview usable at a phone viewport', () => {
  const workspaceSource = fs.readFileSync(path.join(sourceRoot, 'src/components/management/ManagementPageBuilderWorkspace.vue'), 'utf8')
  const settingsSource = fs.readFileSync(path.join(sourceRoot, 'src/pages/management/ManagementSiteSettingsPage.vue'), 'utf8')
  assert.match(workspaceSource, /device === 'mobile'/)
  assert.match(workspaceSource, /width: min\(390px/)
  assert.match(workspaceSource, /\.cat-expand \.cat-card[\s\S]*pointer-events: auto/)
  assert.match(settingsSource, /previewDeviceOptions/)
  assert.match(settingsSource, /preview-viewport--mobile/)
})

test('uses the real public components for every live management preview page', () => {
  const previewSource = fs.readFileSync(path.join(sourceRoot, 'src/components/management/ManagementLivePagePreview.vue'), 'utf8')
  const settingsSource = fs.readFileSync(path.join(sourceRoot, 'src/pages/management/ManagementSiteSettingsPage.vue'), 'utf8')
  assert.match(previewSource, /PublicHeader/)
  assert.match(previewSource, /HomePageRenderer/)
  assert.match(previewSource, /AboutUsPage/)
  assert.match(previewSource, /FaqPage/)
  assert.match(previewSource, /ProductGroupsPage/)
  assert.match(previewSource, /MenuItemCard/)
  assert.match(previewSource, /SiteFooter/)
  assert.match(settingsSource, /ManagementLivePagePreview/)
  assert.match(settingsSource, /livePreviewPage/)
  assert.match(settingsSource, /components: \['aboutShell', 'aboutSections'\]/)
  assert.match(settingsSource, /components: \['faqShell', 'faqItems'\]/)
})

test('keeps about section images visible and saves authoring changes directly', () => {
  const aboutSource = fs.readFileSync(path.join(sourceRoot, 'src/pages/AboutUsPage.vue'), 'utf8')
  const settingsSource = fs.readFileSync(path.join(sourceRoot, 'src/pages/management/ManagementSiteSettingsPage.vue'), 'utf8')
  assert.match(aboutSource, /heroResolved\.image/)
  assert.match(aboutSource, /mission\.image/)
  assert.match(aboutSource, /vision\.image/)
  assert.match(aboutSource, /item\.image/)
  assert.match(aboutSource, /history\.image/)
  assert.match(aboutSource, /event\.image/)
  assert.match(settingsSource, /async function saveSiteSettingsDirect[\s\S]*setManagementSiteSettings\(payload\)/)
  assert.match(settingsSource, /async function saveThemeDraft[\s\S]*saveThemeSettingsToServer/)
  assert.match(settingsSource, /async function savePageLayoutDirect[\s\S]*setManagementPageLayout\(\{ page: pageKey, blocks \}\)/)
  assert.match(settingsSource, /focusAboutEditor[\s\S]*scrollIntoView/)
})
