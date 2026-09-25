import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { findCustomerCompanyBranch, isCustomerCompany, isCustomerDeliveryCompany, isCustomerPickupCompany } from '../src/utils/orderBranches.js'

const root = new URL('../src/', import.meta.url)

async function source(path) {
  return readFile(new URL(path, root), 'utf8')
}

test('cart line keeps the product image as a large, stable visual anchor', async () => {
  const page = await source('components/CartLineEditor.vue')

  assert.match(page, /class="product-visual"/)
  assert.match(page, /width:\s*clamp\(112px, 20vw, 144px\)/)
  assert.match(page, /aspect-ratio:\s*1/)
  assert.match(page, /object-fit:\s*contain/)
})

test('customer language uses branches while preserving native company identity', async () => {
  const [delivery, orderType] = await Promise.all([source('pages/OrderDeliveryPage.vue'), source('pages/OrderTypePage.vue')])
  assert.match(delivery, /انتخاب شعبه/)
  assert.match(delivery, /branch:\s*selectedCompany\.value\?\.(id|name)/)
  for (const label of ['درب منزل', 'درب ماشین', 'تحویل حضوری', 'سر میز']) assert.ok(orderType.includes(label))
})

test('checkout summarizes the selected order context in editable confirmation cards', async () => {
  const page = await source('pages/CheckoutPage.vue')

  assert.match(page, /class="[^"]*checkout-confirmation-card[^"]*"/)
  assert.match(page, /ویرایش نوع سفارش/)
  assert.match(page, /class="checkout-product-summary"/)
  assert.match(page, /if \(!context\.value\.branch\) return 'برای ارسال، انتخاب شعبه الزامی است\.'/)
  assert.match(page, /orderReviewStep = computed\(\(\) => context\.value\.order_type === 'pickup' \? '۵' : '۴'\)/)
  assert.match(page, /\{\{ orderReviewStep \}\}\. مرور سفارش/)
})

test('cart switches to one column before image-first cards become cramped', async () => {
  const page = await source('pages/CartPage.vue')

  assert.match(page, /@media \(max-width: 760px\)/)
  assert.match(page, /margin-bottom:\s*calc\(7\.5rem \+ env\(safe-area-inset-bottom\)\)/)
  assert.match(page, /\.summary-panel\s*\{\s*position:\s*static;/)
})

test('cart actions remain touch friendly, named, and tied to dynamic theme tokens', async () => {
  const [cart, line] = await Promise.all([
    source('pages/CartPage.vue'),
    source('components/CartLineEditor.vue'),
  ])

  assert.match(line, /:aria-label="`حذف \$\{line\.item_title\} از سبد`"/)
  assert.match(line, /role="group" :aria-label="`تعداد \$\{line\.item_title\}`"/)
  assert.match(line, /\.remove-btn\s*\{[^}]*width:\s*44px;[^}]*height:\s*44px;/s)
  assert.match(line, /\.qty-btn\s*\{[^}]*width:\s*44px;[^}]*height:\s*44px;/s)
  assert.match(line, /\.mini-btn\s*\{[^}]*min-height:\s*44px;/s)
  assert.match(line, /--ds-color-action-primary/)
  assert.match(cart, /--ds-color-action-primary/)
})

test('pickup selection avoids a stretched single-branch card and wrapped progress steps', async () => {
  const page = await source('pages/OrderPickupPage.vue')

  assert.match(page, /\.pickup-branch-grid \.order-flow-branch-card,\s*\.order-flow-layout > \.order-flow-list > \.order-flow-branch-card\s*\{[^}]*width:\s*min\(100%,\s*32rem\);[^}]*justify-self:\s*center;/s)
  assert.match(page, /\.order-flow-steps\s*\{[^}]*flex-wrap:\s*nowrap;[^}]*overflow-x:\s*auto;/s)
  assert.match(page, /\.order-flow-step\s*\{[^}]*flex:\s*0 0 auto;[^}]*white-space:\s*nowrap;/s)
})

test('delivery keeps map first and exposes manual recovery on failure', async () => {
  const page = await source('pages/OrderDeliveryPage.vue')
  assert.match(page, /<AddressPickerMap v-model="addressLocation" :config="deliveryMapConfig" @status="mapStatus = \$event"/)
  assert.match(page, /:open="mapStatus === 'error'"/)
  assert.match(page, /عرض جغرافیایی/)
  assert.match(page, /طول جغرافیایی/)
})

test('Frappe serves checkout through the restaurant SPA route', async () => {
  const hooks = await readFile(new URL('../../restaurant/hooks.py', import.meta.url), 'utf8')

  assert.match(hooks, /\{"from_route": "\/checkout", "to_route": "restaurant\/index"\}/)
})

test('customer login uses the saved brand and semantic theme colors', async () => {
  const page = await source('pages/CustomerLoginPage.vue')

  assert.match(page, /props\.boot\?\.branding\?\.name/)
  assert.match(page, /--ds-color-bg-page/)
  assert.match(page, /--ds-color-surface-raised/)
  assert.match(page, /--ds-color-status-danger/)
})

test('the secondary home page follows the saved theme and has a local hero fallback', async () => {
  const [landing, hero] = await Promise.all([
    source('pages/RestaurantLandingPage.vue'),
    source('components/blocks/HeroBlock.vue'),
  ])

  assert.doesNotMatch(landing, /--healthy-brand-green|#f6f6ed/)
  assert.match(landing, /background: var\(--ds-color-bg-page\)/)
  assert.match(hero, /\/assets\/restaurant\/frontend\/veederakht-home-hero\.webp/)
})

test('customer landing blocks render Persian cart, category, and popular labels as text', async () => {
  const [landing, bottomNav, categories, popular] = await Promise.all([
    source('pages/RestaurantLandingPage.vue'),
    source('components/MobileBottomNav.vue'),
    source('components/blocks/CategoriesBlock.vue'),
    source('components/blocks/PopularBlock.vue'),
  ])

  assert.match(landing, /<CartActionFeedback :message="toastMessage" \/>/)
  assert.doesNotMatch(landing, /home-sticky-cart/)
  assert.match(bottomNav, /<small>سبد<\/small>/)
  assert.match(bottomNav, /سبد سفارش/)
  assert.match(categories, /\{\{ formatCount\(cat\.count\) \}\} آیتم/)
  assert.match(popular, /محبوب شماره ۱/)
  assert.match(popular, />افزودن<\/button>/)
})

test('menu and product detail replace failed optional images with their designed fallbacks', async () => {
  const menu = await source('pages/MenuPage.vue')
  const item = await source('pages/ItemDetailPage.vue')
  const ingredients = await source('components/IngredientQuantityEditor.vue')

  assert.match(menu, /nextCategoryImageFailed = true/)
  assert.match(menu, /nextCategoryMeta\.image && !nextCategoryImageFailed/)
  assert.match(item, /@error="onRelatedImageError"/)
  assert.match(item, /\/assets\/restaurant\/frontend\/veederakht-home-hero\.webp/)
  assert.match(ingredients, /@error="markIngredientImageBroken\(ingredient\)"/)
  assert.match(ingredients, /v-if="ingredient\.image && !isIngredientImageBroken\(ingredient\)"/)
  assert.match(ingredients, /class="card-img-placeholder"/)
})

test('customer menu starts loading immediately and exposes accessible responsive controls', async () => {
  const [menu, categoryRail, bottomNav, orderContext, productCard, detail] = await Promise.all([
    source('pages/MenuPage.vue'),
    source('components/CategoryImageRail.vue'),
    source('components/MobileBottomNav.vue'),
    source('components/OrderContextStrip.vue'),
    source('components/MenuProductCard.vue'),
    source('pages/ItemDetailPage.vue'),
  ])

  assert.match(menu, /const loading = ref\(true\)/)
  assert.doesNotMatch(menu, /await getManagementSessionProfile\(\)/)
  assert.match(menu, /aria-controls="menu-sort-options"/)
  assert.match(menu, /:aria-pressed="sortMode === option\.value"/)
  assert.match(menu, /:aria-pressed="selectedTag === tag"/)
  assert.match(menu, /min-height:\s*44px/)
  assert.match(menu, /<CartActionFeedback :message="cartFeedback" \/>/)
  assert.doesNotMatch(menu, /sticky-cart/)
  assert.match(menu, /padding-bottom:\s*max\(7rem,\s*calc\(7rem \+ env\(safe-area-inset-bottom\)\)\)/)
  assert.match(categoryRail, /role="group" aria-label="دسته‌بندی‌های منو"/)
  assert.match(categoryRail, /:aria-pressed="selectedCategory === category\.slug"/)
  assert.match(categoryRail, /min-height:\s*44px/)
  assert.match(bottomNav, /bottom:\s*calc\(0\.62rem \+ env\(safe-area-inset-bottom\)\)/)
  assert.match(bottomNav, /aria-controls="mobile-more-sheet"/)
  assert.match(bottomNav, /--ds-color-action-primary/)
  assert.match(orderContext, /min-height:\s*44px/)
  assert.match(orderContext, /--ds-color-surface-raised/)
  assert.match(productCard, /const isUnavailable = computed\(\(\) => isComingSoon\.value \|\| isStockOut\.value \|\| isOutOfStock\.value \|\| isTemporarilyUnavailable\.value\)/)
  assert.match(productCard, /if \(isUnavailable\.value\) return/)
  assert.match(productCard, /out_of_stock_until/)
  assert.match(detail, /const isUnavailable = computed\(\(\) => isOutOfStock\.value \|\| isStockOut\.value \|\| isComingSoon\.value\)/)
  assert.match(detail, /:disabled="isUnavailable"/)
  assert.doesNotMatch(detail, /unavailableReason \|\| isBuilderEnabled \?/)
  assert.match(detail, /class="gallery-dot"[\s\S]*:aria-pressed="galleryIndex === idx"/)
  assert.match(detail, /const loading = ref\(true\)/)
})

test('delivery choices include configured company branches and exclude table locations', () => {
  const veederakht = {
    id: 'وی‌درخت',
    company: 'وی‌درخت',
    is_active: 1,
    delivery_available: true,
    isOpen: true,
  }

  assert.equal(isCustomerDeliveryCompany(veederakht), true)
  assert.equal(isCustomerDeliveryCompany({ ...veederakht, delivery_available: false }), false)
  assert.equal(isCustomerDeliveryCompany({ ...veederakht, is_active: 0 }), false)
  assert.equal(isCustomerDeliveryCompany({ id: 'DEFAULT', company: 'وی‌درخت', delivery_available: true }), false)
  assert.equal(isCustomerDeliveryCompany({ id: 'Main Hall', delivery_available: true }), false)
})

test('pickup and dine-in choices exclude production defaults and table locations', async () => {
  const company = {
    id: 'وی‌درخت',
    company: 'وی‌درخت',
    is_active: 1,
    isOpen: true,
    pickup_available: true,
    delivery_available: true,
  }
  const [pickup, dineIn] = await Promise.all([
    source('pages/OrderPickupPage.vue'),
    source('pages/OrderDineInPage.vue'),
  ])

  assert.equal(isCustomerCompany(company), true)
  assert.equal(isCustomerPickupCompany(company), true)
  assert.equal(findCustomerCompanyBranch([company], 'وی درخت'), company)
  assert.equal(isCustomerPickupCompany({ ...company, pickup_available: false }), false)
  assert.equal(isCustomerPickupCompany({ ...company, isOpen: false }), false)
  assert.equal(isCustomerCompany({ id: 'DEFAULT', company: 'وی‌درخت', is_active: 1, isOpen: true }), false)
  assert.equal(isCustomerCompany({ id: 'Main Hall', is_active: 1, isOpen: true }), false)
  assert.match(pickup, /\.filter\(isCustomerPickupCompany\)/)
  assert.match(dineIn, /\.filter\(isCustomerCompany\)/)
})

test('public app pages cache-bust the built frontend instead of pinning an old version', async () => {
  const home = await readFile(new URL('../../restaurant/www/restaurant/index.html', import.meta.url), 'utf8')
  const order = await readFile(new URL('../../restaurant/www/order/type.html', import.meta.url), 'utf8')
  const orders = await readFile(new URL('../../restaurant/www/customer/orders.html', import.meta.url), 'utf8')
  const frontendVersion = await readFile(new URL('../../restaurant/www/_frontend.py', import.meta.url), 'utf8')

  for (const page of [home, order, orders]) {
    assert.match(page, /\?v=\{\{ frontend_version \}\}/)
    assert.doesNotMatch(page, /20260705c|20260924-homev2-r2/)
  }
  assert.match(frontendVersion, /get_frontend_version/)
  assert.match(frontendVersion, /getmtime/)
})

test('customer, product, and order page wrappers provide the shared frontend version', async () => {
  const pages = await Promise.all([
    readFile(new URL('../../restaurant/www/restaurant/index.py', import.meta.url), 'utf8'),
    readFile(new URL('../../restaurant/www/restaurant/item.py', import.meta.url), 'utf8'),
    readFile(new URL('../../restaurant/www/order/_context.py', import.meta.url), 'utf8'),
    readFile(new URL('../../restaurant/www/customer/orders.py', import.meta.url), 'utf8'),
  ])

  for (const page of pages) assert.match(page, /context\.frontend_version\s*=\s*get_frontend_version\(context\)/)
})
