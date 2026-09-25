<template>
  <div class="search-page" dir="rtl">
    <section class="search-hero">
      <div class="search-heading">
        <p>جستجو در منوی ویدرخت</p>
        <h1>چی میل دارید؟</h1>
        <span>نام غذا، دسته‌بندی یا یکی از مواد اولیه را بنویسید.</span>
      </div>
      <div class="search-input-wrap">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <input
          ref="searchInput"
          v-model.trim="query"
          class="search-input"
          placeholder="نام غذا، دسته‌بندی یا مواد اولیه..."
          autocomplete="off"
          @keydown.enter="searchNow"
        />
        <button v-if="query" type="button" class="clear-btn" @click="clearSearch">×</button>
      </div>
      <div class="chips-row">
        <button v-for="chip in hintChips" :key="chip" type="button" @click="selectChip(chip)">{{ chip }}</button>
      </div>
    </section>

    <p v-if="loading" class="state muted">در حال جستجو...</p>
    <p v-else-if="error" class="state error">{{ error }}</p>

    <section v-else-if="results.length" class="results-list">
      <article v-for="item in results" :key="item.slug || item.name" class="result-card">
        <a :href="`/item/${item.slug}`" class="image-link">
          <img :src="item.image || fallbackImage" :alt="item.title" loading="lazy" />
        </a>
        <div class="result-body">
          <div class="result-top">
            <span>{{ item.category_title || item.category || 'منو' }}</span>
            <strong>{{ formatMoney(item.base_price, currency) }}</strong>
          </div>
          <a :href="`/item/${item.slug}`" class="result-title">{{ item.title }}</a>
          <p>{{ item.short_desc || 'توضیحی برای این آیتم ثبت نشده است.' }}</p>
          <div class="result-actions">
            <a :href="`/item/${item.slug}`" class="detail-btn">جزئیات</a>
            <button type="button" class="add-btn" @click="quickAdd(item)">افزودن سریع</button>
          </div>
        </div>
      </article>
    </section>

    <section v-else-if="searched" class="empty-card">
      <div>🔍</div>
      <h3>نتیجه‌ای پیدا نشد</h3>
      <p>عبارت دیگری را جستجو کنید یا از دسته‌بندی‌های منو استفاده کنید.</p>
      <a href="/menu" class="primary-btn">رفتن به منو</a>
    </section>

    <section v-else class="hint-card">
      <div>🍽️</div>
      <h3>چی میل دارید؟</h3>
      <p>حداقل دو حرف تایپ کنید تا جستجو در منوی آنلاین انجام شود.</p>
    </section>

    <Transition name="toast">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </Transition>

    <div class="bottom-spacer"></div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import { getMenuItems } from '@/utils/api'
import { formatMoney, parseQuery } from '@/utils/format'
import { upsertLine } from '@/stores/cartStore'

const routeQuery = parseQuery()
const query = ref(String(routeQuery.q || '').trim())
const results = ref([])
const loading = ref(false)
const error = ref('')
const searched = ref(false)
const currency = ref('TOMAN')
const toast = ref('')
const searchInput = ref(null)
const fallbackImage = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&auto=format&fit=crop&q=60'
const hintChips = ['برگر', 'پیتزا', 'سالاد', 'قهوه', 'دسر']
let timer = null

watch(query, (value) => {
  window.clearTimeout(timer)
  if (String(value || '').trim().length < 2) {
    results.value = []
    searched.value = false
    loading.value = false
    return
  }
  loading.value = true
  timer = window.setTimeout(() => searchNow(), 320)
})

function clearSearch() {
  query.value = ''
  results.value = []
  searched.value = false
  nextTick(() => searchInput.value?.focus())
}

function selectChip(chip) {
  query.value = chip
  nextTick(searchNow)
}

async function searchNow() {
  const term = String(query.value || '').trim()
  if (term.length < 2) return
  loading.value = true
  error.value = ''
  searched.value = true
  try {
    const data = await getMenuItems({ search: term, page: 1, page_size: 30 })
    results.value = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []
    if (data?.currency) currency.value = data.currency
    const url = new URL(window.location.href)
    url.searchParams.set('q', term)
    window.history.replaceState({}, '', `${url.pathname}?${url.searchParams.toString()}`)
  } catch (err) {
    error.value = err?.message || 'جستجو ناموفق بود.'
    results.value = []
  } finally {
    loading.value = false
  }
}

function quickAdd(item = {}) {
  if (!item.slug) return
  if (Number(item.has_customization || 0) === 1 || Number(item.restaurant_is_customizable || 0) === 1) {
    window.location.href = `/item/${item.slug}`
    return
  }
  upsertLine({
    item_slug: item.slug,
    item_title: item.title,
    item_image: item.image || '',
    base_price: Number(item.base_price || 0),
    qty: 1,
    unit_price_preview: Number(item.base_price || 0),
    line_total_preview: Number(item.base_price || 0),
    customization: { ingredient_adjustments: [], selected_modifiers: [] },
    ingredient_catalog: [],
    modifier_groups_catalog: [],
  })
  toast.value = 'به سبد اضافه شد'
  window.setTimeout(() => { toast.value = '' }, 1800)
}

onMounted(() => {
  searchInput.value?.focus()
  if (query.value.length >= 2) searchNow()
})
</script>

<style scoped>
.search-page { width: min(100%, 1040px); min-height: 100vh; margin-inline: auto; box-sizing: border-box; color: var(--ds-color-text-primary); padding: 1rem 1rem 7rem; }
.search-hero { display: grid; gap: 1rem; margin-bottom: 1.25rem; border: 1px solid var(--ds-color-border); border-radius: 26px; padding: clamp(1.1rem, 4vw, 2rem); background: linear-gradient(135deg, var(--ds-color-action-primary-soft), var(--ds-color-action-accent-soft)), var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-sm); }
.search-heading p { margin: 0 0 .25rem; color: var(--ds-color-action-primary); font-size: .78rem; font-weight: 800; }
.search-heading h1 { margin: 0; color: var(--ds-color-text-primary); font-size: clamp(1.25rem, 4vw, 1.65rem); font-weight: 900; }
.search-heading span { display: block; margin-top: .35rem; color: var(--ds-color-text-secondary); font-size: .86rem; line-height: 1.7; }
.search-input-wrap { display: flex; min-height: 54px; align-items: center; gap: .7rem; border: 1px solid var(--ds-color-border); border-radius: 18px; background: var(--ds-color-surface-raised); padding: .55rem .85rem; color: var(--ds-color-action-primary); box-shadow: 0 6px 16px color-mix(in srgb, var(--ds-color-text-primary) 6%, transparent); }
.search-input-wrap:focus-within { border-color: var(--ds-color-focus-ring); box-shadow: 0 0 0 3px var(--ds-color-action-accent-soft); }
.search-input { flex: 1; min-width: 0; background: transparent; border: 0; outline: 0; color: var(--ds-color-text-primary); font-family: inherit; font-size: .98rem; }
.search-input::placeholder { color: var(--ds-color-text-muted); }
.clear-btn { width: 34px; height: 34px; border-radius: 50%; border: 0; background: var(--ds-color-surface-muted); color: var(--ds-color-action-primary); cursor: pointer; }
.chips-row { display: flex; gap: .5rem; overflow-x: auto; padding-top: .1rem; scrollbar-width: none; }
.chips-row::-webkit-scrollbar { display: none; }
.chips-row button { min-height: 38px; border: 1px solid var(--ds-color-border); background: var(--ds-color-surface-raised); color: var(--ds-color-text-secondary); border-radius: 999px; padding: .45rem .8rem; font-family: inherit; white-space: nowrap; cursor: pointer; }
.chips-row button:hover { background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); }
.state { text-align: center; margin: 1rem; }
.muted { color: var(--ds-color-text-muted); }
.error { color: var(--ds-color-status-danger); }
.results-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 420px), 1fr)); gap: .85rem; }
.result-card { min-width: 0; border: 1px solid var(--ds-color-border); background: var(--ds-color-surface-raised); border-radius: 22px; overflow: hidden; display: grid; grid-template-columns: 112px minmax(0, 1fr); box-shadow: var(--ds-shadow-sm); }
.image-link { background: var(--ds-color-surface-muted); min-height: 150px; }
.image-link img { width: 100%; height: 100%; object-fit: cover; display: block; }
.result-body { padding: .85rem; min-width: 0; }
.result-top { display: flex; justify-content: space-between; gap: .6rem; color: var(--ds-color-text-muted); font-size: .72rem; }
.result-top strong { color: var(--ds-color-action-primary); white-space: nowrap; }
.result-title { display: block; margin: .35rem 0; color: var(--ds-color-text-primary); font-weight: 900; text-decoration: none; }
.result-body p { color: var(--ds-color-text-secondary); font-size: .78rem; line-height: 1.7; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.result-actions { display: flex; gap: .5rem; margin-top: .75rem; }
.detail-btn, .add-btn, .primary-btn { min-height: 42px; border-radius: 14px; padding: .55rem .8rem; text-decoration: none; font-family: inherit; font-weight: 800; font-size: .78rem; display: inline-flex; align-items: center; justify-content: center; }
.detail-btn { background: var(--ds-color-surface-muted); color: var(--ds-color-action-primary); }
.add-btn, .primary-btn { flex: 1; border: none; background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground, var(--ds-color-text-inverse)); cursor: pointer; }
.empty-card, .hint-card { margin-top: 1rem; border: 1px solid var(--ds-color-border); background: var(--ds-color-surface-raised); border-radius: 24px; padding: 2rem 1.2rem; text-align: center; box-shadow: var(--ds-shadow-sm); }
.empty-card div, .hint-card div { font-size: 2.4rem; }
.empty-card p, .hint-card p { color: var(--ds-color-text-secondary); line-height: 1.8; }
.toast { position: fixed; left: 1rem; right: 1rem; bottom: 5.8rem; background: var(--ds-color-status-success); color: var(--ds-color-status-success-foreground, var(--ds-color-text-inverse)); border-radius: 16px; padding: .85rem 1rem; text-align: center; font-weight: 800; z-index: var(--ds-z-sticky); box-shadow: var(--ds-shadow-md); }
.toast-enter-active, .toast-leave-active { transition: .2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(16px); }
.bottom-spacer { height: 2rem; }
@media (max-width: 440px) {
  .search-page { padding-inline: .75rem; }
  .result-card { grid-template-columns: 94px minmax(0, 1fr); }
  .image-link { min-height: 142px; }
  .result-actions { gap: .35rem; }
  .detail-btn, .add-btn, .primary-btn { padding-inline: .55rem; font-size: .72rem; }
}
.search-page :is(button, a, input):focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
</style>
