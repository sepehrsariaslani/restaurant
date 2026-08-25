<template>
  <div class="search-page" dir="rtl">
    <header class="page-header">
      <button class="back-btn" type="button" @click="goBack" aria-label="بازگشت">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">جستجوی منو</h1>
      <a class="cart-link" href="/cart" aria-label="سبد خرید">🛒<i v-if="cartCount">{{ cartCount }}</i></a>
    </header>

    <section class="search-hero">
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
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { getMenuItems } from '@/utils/api'
import { formatMoney, parseQuery } from '@/utils/format'
import { cartState, upsertLine } from '@/stores/cartStore'

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
const cartCount = computed(() => cartState.lines.reduce((sum, line) => sum + Number(line.qty || 0), 0))
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

function goBack() {
  window.history.back()
}

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
.search-page { min-height: 100vh; background: #f7f0e8; color: #3f2a1d; padding-bottom: 7rem; }
.page-header { display: flex; align-items: center; justify-content: space-between; padding: 3.5rem 1rem 1rem; background: #fff; border-bottom: 1px solid #ede3d8; }
.back-btn, .cart-link { width: 40px; height: 40px; border-radius: 50%; background: #f7f0e8; border: none; color: #3f2a1d; display: flex; align-items: center; justify-content: center; text-decoration: none; position: relative; cursor: pointer; }
.cart-link i { position: absolute; top: 2px; left: 2px; background: #e74c3c; color: #fff; border-radius: 999px; font-size: .62rem; min-width: 16px; height: 16px; display: grid; place-items: center; font-style: normal; }
.page-title { margin: 0; font-size: 1.1rem; font-weight: 800; }
.search-hero { margin: 1rem; background: linear-gradient(135deg, #3f2a1d, #6f4a31); border-radius: 26px; padding: 1rem; box-shadow: 0 12px 26px rgba(63,42,29,.18); }
.search-input-wrap { display: flex; align-items: center; gap: .7rem; background: rgba(255,255,255,.14); border: 1px solid rgba(255,255,255,.24); border-radius: 18px; padding: .85rem 1rem; color: rgba(255,255,255,.76); }
.search-input { flex: 1; min-width: 0; background: transparent; border: 0; outline: 0; color: #fff; font-family: inherit; font-size: .98rem; }
.search-input::placeholder { color: rgba(255,255,255,.58); }
.clear-btn { width: 28px; height: 28px; border-radius: 50%; border: 0; background: rgba(255,255,255,.2); color: #fff; cursor: pointer; }
.chips-row { display: flex; gap: .5rem; overflow-x: auto; padding-top: .85rem; scrollbar-width: none; }
.chips-row::-webkit-scrollbar { display: none; }
.chips-row button { border: 1px solid rgba(255,255,255,.22); background: rgba(255,255,255,.12); color: #fff; border-radius: 999px; padding: .45rem .8rem; font-family: inherit; white-space: nowrap; }
.state { text-align: center; margin: 1rem; }
.muted { color: #846b58; }
.error { color: #b84f4f; }
.results-list { display: grid; gap: .85rem; margin: 0 1rem; }
.result-card { background: #fff; border-radius: 22px; overflow: hidden; display: grid; grid-template-columns: 112px 1fr; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.image-link { background: #f1e7db; min-height: 132px; }
.image-link img { width: 100%; height: 100%; object-fit: cover; display: block; }
.result-body { padding: .85rem; min-width: 0; }
.result-top { display: flex; justify-content: space-between; gap: .6rem; color: #846b58; font-size: .72rem; }
.result-top strong { color: #6f4a31; white-space: nowrap; }
.result-title { display: block; margin: .35rem 0; color: #3f2a1d; font-weight: 900; text-decoration: none; }
.result-body p { color: #846b58; font-size: .78rem; line-height: 1.7; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.result-actions { display: flex; gap: .5rem; margin-top: .75rem; }
.detail-btn, .add-btn, .primary-btn { border-radius: 14px; padding: .65rem .8rem; text-decoration: none; font-family: inherit; font-weight: 800; font-size: .78rem; display: inline-flex; align-items: center; justify-content: center; }
.detail-btn { background: #f7f0e8; color: #6f4a31; }
.add-btn, .primary-btn { border: none; background: #6f4a31; color: #fff; cursor: pointer; }
.empty-card, .hint-card { margin: 1rem; background: #fff; border-radius: 24px; padding: 2rem 1.2rem; text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,.06); }
.empty-card div, .hint-card div { font-size: 2.4rem; }
.empty-card p, .hint-card p { color: #846b58; line-height: 1.8; }
.toast { position: fixed; left: 1rem; right: 1rem; bottom: 5.8rem; background: #2e7d32; color: #fff; border-radius: 16px; padding: .85rem 1rem; text-align: center; font-weight: 800; z-index: 50; box-shadow: 0 12px 28px rgba(46,125,50,.28); }
.toast-enter-active, .toast-leave-active { transition: .2s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(16px); }
.bottom-spacer { height: 2rem; }
@media (min-width: 720px) { .search-page { max-width: 780px; margin: 0 auto; } }
</style>
