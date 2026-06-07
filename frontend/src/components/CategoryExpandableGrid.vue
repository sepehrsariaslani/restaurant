<template>
  <div class="cat-expand" dir="rtl">
    <div class="cat-grid">
      <button
        v-for="cat in resolvedCategories"
        :key="cat.key"
        type="button"
        class="cat-card"
        :class="{ active: selectedSlug === cat.slug }"
        @click="toggleCategory(cat)"
      >
        <div class="cat-img-wrap">
          <img v-if="cat.image" :src="cat.image" :alt="cat.title" loading="lazy" />
          <div v-else class="cat-no-img">
            <span class="cat-emoji">🍽️</span>
          </div>
          <div class="cat-img-overlay"></div>
        </div>
        <div class="cat-label">
          <span class="cat-name">{{ cat.title }}</span>
          <span class="cat-count" v-if="cat.count">{{ cat.count }} آیتم</span>
        </div>
        <span class="cat-active-dot" v-if="selectedSlug === cat.slug"></span>
      </button>
    </div>

    <transition name="panel-slide">
      <div v-if="selectedCategory" class="cat-panel" ref="panelRef">
        <div class="cat-panel-header">
          <div class="cat-panel-title">
            <h3>{{ selectedCategory.title }}</h3>
            <span class="cat-panel-count" v-if="items.length">{{ items.length }} آیتم</span>
          </div>
          <div class="cat-panel-actions">
            <a :href="`/menu?category=${selectedCategory.slug}`" class="see-all-btn">
              مشاهده همه
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </a>
            <button type="button" class="close-panel-btn" @click="close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        <div v-if="loadingItems" class="cat-panel-loading">
          <div class="loader-ring"></div>
          <span>در حال بارگذاری...</span>
        </div>

        <div v-else-if="!items.length" class="cat-panel-empty">
          آیتمی در این دسته یافت نشد.
        </div>

        <div v-else class="cat-items-grid">
          <a
            v-for="item in items"
            :key="item.slug || item.name"
            :href="`/menu?category=${selectedCategory.slug}`"
            class="cat-item-card"
          >
            <div class="cat-item-img-wrap">
              <img v-if="item.image" :src="item.image" :alt="item.title || item.name" loading="lazy" />
              <div v-else class="cat-item-no-img">🍴</div>
            </div>
            <div class="cat-item-info">
              <span class="cat-item-name">{{ item.title || item.item_name || item.name }}</span>
              <span class="cat-item-price" v-if="item.price > 0">
                {{ formatPrice(item.price, currency) }}
              </span>
            </div>
          </a>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from 'vue'
import { getMenuItems } from '@/utils/api'

const props = defineProps({
  categories: {
    type: Array,
    default: () => [],
  },
  currency: {
    type: String,
    default: 'IRR',
  },
})

const emit = defineEmits(['quick-add'])

const selectedSlug = ref('')
const selectedCategory = ref(null)
const items = ref([])
const loadingItems = ref(false)

const resolvedCategories = computed(() =>
  (props.categories || []).map((cat, idx) => ({
    key: cat.slug || `cat-${idx}`,
    title: cat.title || 'دسته بندی',
    slug: cat.slug || '',
    image: cat.image || '',
    count: cat.items_count || null,
  })),
)

const panelRef = ref(null)

async function toggleCategory(cat) {
  if (selectedSlug.value === cat.slug) {
    close()
    return
  }

  selectedSlug.value = cat.slug
  selectedCategory.value = cat
  items.value = []
  loadingItems.value = true

  await nextTick()
  scrollToPanel()

  try {
    const result = await getMenuItems({ category_slug: cat.slug, page_size: 20 })
    items.value = Array.isArray(result?.items) ? result.items : Array.isArray(result) ? result : []
  } catch {
    items.value = []
  } finally {
    loadingItems.value = false
  }
}

function scrollToPanel() {
  nextTick(() => {
    const el = panelRef.value
    if (!el) return
    const y = el.getBoundingClientRect().top + window.scrollY - 96
    window.scrollTo({ top: y, behavior: 'smooth' })
  })
}

function close() {
  selectedSlug.value = ''
  selectedCategory.value = null
  items.value = []
}

function formatPrice(price, currency) {
  if (!price) return ''
  const num = Number(price)
  if (!num) return ''
  const formatted = num.toLocaleString('fa-IR')
  return currency === 'IRR' ? `${formatted} ریال` : `${formatted} ${currency}`
}
</script>

<style scoped>
.cat-expand {
  display: grid;
  gap: 1rem;
  direction: rtl;
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.7rem;
}

.cat-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  border: none;
  border-radius: 16px;
  background: none;
  cursor: pointer;
  padding: 0;
  text-align: right;
  transition: transform 0.2s, box-shadow 0.2s;
  font-family: inherit;
  overflow: hidden;
}

.cat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgb(0 0 0 / 0.12);
}

.cat-card.active .cat-img-wrap {
  outline: 2.5px solid var(--palette-deep-sapphire, #6F4A31);
  outline-offset: 2px;
}

.cat-img-wrap {
  position: relative;
  width: 100%;
  padding-bottom: 75%;
  border-radius: 14px;
  overflow: hidden;
}

.cat-img-wrap img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s;
}

.cat-card:hover .cat-img-wrap img {
  transform: scale(1.06);
}

.cat-no-img {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #f5f0eb, #e8e0d6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
}

.cat-img-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 40%, rgb(0 0 0 / 0.4) 100%);
  border-radius: 14px;
}

.cat-label {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0 0.2rem;
}

.cat-name {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ink-800, #3d2e26);
  line-height: 1.3;
}

.cat-count {
  font-size: 0.7rem;
  color: var(--ink-600, #9a8a80);
}

.cat-active-dot {
  position: absolute;
  bottom: 0.35rem;
  left: 50%;
  transform: translateX(-50%);
  width: 0.45rem;
  height: 0.45rem;
  border-radius: 50%;
  background: var(--palette-deep-sapphire, #6F4A31);
}

/* Expanded panel */
.cat-panel {
  background: #fff;
  border: 1.5px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.12);
  border-radius: 18px;
  padding: 1.1rem;
  display: grid;
  gap: 0.9rem;
  box-shadow: 0 8px 32px rgb(0 0 0 / 0.07);
}

.cat-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
}

.cat-panel-title {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.cat-panel-title h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 800;
  color: var(--ink-900, #1c1411);
}

.cat-panel-count {
  font-size: 0.75rem;
  color: var(--ink-600, #9a8a80);
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
}

.cat-panel-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.see-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.38rem 0.85rem;
  border-radius: 999px;
  background: var(--palette-deep-sapphire, #6F4A31);
  color: #fff;
  font-size: 0.76rem;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.15s;
}

.see-all-btn:hover {
  background: #5a3b25;
}

.close-panel-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  border: 1.5px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.18);
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-700, #7a6a60);
  transition: background 0.15s;
}

.close-panel-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
  color: var(--ink-900, #1c1411);
}

.cat-panel-loading {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 1.5rem 0;
  justify-content: center;
  color: var(--ink-600, #9a8a80);
  font-size: 0.85rem;
}

.loader-ring {
  width: 1.4rem;
  height: 1.4rem;
  border: 2px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.2);
  border-top-color: var(--palette-deep-sapphire, #6F4A31);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.cat-panel-empty {
  text-align: center;
  padding: 1.5rem;
  color: var(--ink-600, #9a8a80);
  font-size: 0.84rem;
}

.cat-items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.65rem;
}

.cat-item-card {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  border-radius: 12px;
  overflow: hidden;
  text-decoration: none;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb, 111 74 49) / 0.08);
  transition: transform 0.18s, box-shadow 0.18s;
  background: rgb(var(--palette-eggshell-rgb, 251 248 244) / 0.6);
}

.cat-item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 16px rgb(0 0 0 / 0.09);
}

.cat-item-img-wrap {
  width: 100%;
  aspect-ratio: 4/3;
  overflow: hidden;
  background: #f0ece7;
  position: relative;
}

.cat-item-img-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.cat-item-card:hover .cat-item-img-wrap img {
  transform: scale(1.05);
}

.cat-item-no-img {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  background: linear-gradient(135deg, #f5f0eb, #e8e0d6);
}

.cat-item-info {
  padding: 0.35rem 0.5rem 0.45rem;
  display: grid;
  gap: 0.12rem;
}

.cat-item-name {
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--ink-800, #3d2e26);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cat-item-price {
  font-size: 0.68rem;
  color: var(--palette-deep-sapphire, #6F4A31);
  font-weight: 600;
}

/* Transition */
.panel-slide-enter-active {
  animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.panel-slide-leave-active {
  animation: slideDown 0.2s cubic-bezier(0.4, 0, 0.2, 1) reverse;
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 520px) {
  .cat-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .cat-items-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
