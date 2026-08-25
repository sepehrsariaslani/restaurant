import { readFileSync } from 'node:fs'

function read(path) {
  return readFileSync(new URL(path, import.meta.url), 'utf8')
}

const rail = read('../src/components/CategoryImageRail.vue')
const card = read('../src/components/MenuProductCard.vue')
const menuPage = read('../src/pages/MenuPage.vue')
const itemDetail = read('../src/pages/ItemDetailPage.vue')
const app = read('../src/App.vue')

const failures = []

if (rail.includes('v-if="category.image"') || rail.includes(":class=\"{ 'has-image': category.image }\"")) {
  failures.push('category rail still prefers category.image in /menu instead of menu icon only')
}

if (!rail.includes('getMenuIconComponent(category.menu_icon')) {
  failures.push('category rail is missing stored menu icon lookup')
}

for (const marker of ['item.category_title', 'item.subcategory_title', 'calorie-chip', 'calorie-badge', 'Flame']) {
  if (card.includes(marker)) {
    failures.push(`menu product card still contains removed visual marker: ${marker}`)
  }
}

for (const marker of ['nutrition_carb_g', 'nutrition_sugar_g', 'C ${Math.round(carb)}g', 'S ${Math.round(sugar)}g']) {
  if (card.includes(marker)) {
    failures.push(`menu product card still includes extra nutrition field: ${marker}`)
  }
}

if (!card.includes('کیلوکالری') || !card.includes('گرم پروتئین')) {
  failures.push('menu product card is missing Persian nutrition labels for kcal/protein')
}

if (!card.includes('visibleTags')) {
  failures.push('menu product card is missing the single-tag presentation helper')
}

if (!menuPage.includes('next-category-card')) {
  failures.push('menu page is missing the next-category CTA card')
}

if (!menuPage.includes('goToNextCategory') || !menuPage.includes('nextCategoryMeta')) {
  failures.push('menu page is missing next-category navigation logic')
}

for (const marker of ['next-category-card--image', 'next-category-card__overlay', 'next-category-card__media-full']) {
  if (!menuPage.includes(marker)) {
    failures.push(`menu page is missing next-category visual marker: ${marker}`)
  }
}

for (const marker of ['function getMenuStickyOffset', 'function scrollElementIntoMenuView']) {
  if (!menuPage.includes(marker)) {
    failures.push(`menu page is missing offset-aware scroll helper: ${marker}`)
  }
}

for (const marker of ['async function loadCategoryCatalog', 'await loadCategoryCatalog()', 'allLoaded.value = true']) {
  if (!menuPage.includes(marker)) {
    failures.push(`menu page is missing grouped-menu preload marker: ${marker}`)
  }
}

if (menuPage.includes('scrollIntoView?.({ behavior: \'smooth\', block: \'start\' })')) {
  failures.push('menu page still relies on raw scrollIntoView for sticky-offset navigation')
}

for (const marker of ['function resolveItemImage', 'nutritionCards', 'nutri-chip__icon']) {
  if (!itemDetail.includes(marker)) {
    failures.push(`item detail is missing marker: ${marker}`)
  }
}

for (const marker of ['.gallery-img { object-fit: contain;', 'height: min(390px, 82vw);', 'max-width: min(100%, 27rem);']) {
  if (!itemDetail.includes(marker)) {
    failures.push(`item detail mobile hero is missing improved image marker: ${marker}`)
  }
}

for (const imageMarker of ['source?.item_image', 'source?.website_image', 'source?.extra_images?.[0]']) {
  if (!itemDetail.includes(imageMarker)) {
    failures.push(`item detail image resolver is missing fallback source: ${imageMarker}`)
  }
}

if (!app.includes("page !== 'item'")) {
  failures.push('app still mounts mobile bottom nav on item detail page')
}

if (failures.length) {
  console.error('menu minimalization checks failed:')
  for (const failure of failures) console.error(`- ${failure}`)
  process.exit(1)
}

console.log('menu minimalization checks OK')
