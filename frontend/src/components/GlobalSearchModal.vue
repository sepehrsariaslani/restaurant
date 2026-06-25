<template>
  <Teleport to="body">
    <Transition name="search-modal">
      <div
        v-if="searchOpen"
        ref="overlayEl"
        class="search-overlay"
        dir="rtl"
        role="dialog"
        aria-modal="true"
        aria-label="جستجوی سراسری"
        @click.self="closeSearch"
        @keydown.esc="closeSearch"
      >
        <div class="search-box">
          <div class="search-input-row">
            <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            <input
              ref="inputEl"
              v-model="query"
              type="text"
              class="search-input"
              placeholder="جستجو در منو..."
              autocomplete="off"
              @keydown.esc="closeSearch"
              @keydown.enter="goFirst"
            />
            <button class="search-close-btn" type="button" @click="closeSearch" aria-label="بستن">×</button>
          </div>

          <div class="search-results" v-if="results.length">
            <a
              v-for="item in results"
              :key="item.slug"
              :href="`/item/${item.slug}`"
              class="result-row"
              @click="closeSearch"
            >
              <div class="result-img-wrap">
                <img
                  :src="item.image || fallback"
                  :alt="item.title"
                  class="result-img"
                  loading="lazy"
                  @error="$event.target.src = fallback"
                />
              </div>
              <div class="result-info">
                <strong class="result-name">{{ item.title }}</strong>
                <small class="result-cat">{{ item.category_title || item.category || 'منو' }}</small>
              </div>
              <span class="result-price">{{ formatMoney(item.base_price, 'TOMAN') }}</span>
              <span class="result-arrow">←</span>
            </a>
          </div>

          <div class="search-empty" v-else-if="searching">
            <div class="search-spinner"></div>
            <p>در حال جستجو...</p>
          </div>

          <div class="search-empty" v-else-if="query.length >= 2 && !searching">
            <span class="empty-icon">🍽️</span>
            <p>نتیجه‌ای برای «{{ query }}» یافت نشد.</p>
          </div>

          <div class="search-hint" v-else>
            <span class="hint-icon">🔍</span>
            <p>نام غذا، دسته‌بندی یا مواد اولیه را وارد کنید</p>
            <div class="hint-chips">
              <button type="button" class="hint-chip" v-for="chip in hintChips" :key="chip" @click="query = chip">{{ chip }}</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useSearchModal } from '@/composables/useSearchModal'
import { getMenuItems } from '@/utils/api'
import { formatMoney } from '@/utils/format'

const { searchOpen, closeSearch } = useSearchModal()

const query = ref('')
const results = ref([])
const searching = ref(false)
const inputEl = ref(null)

const fallback = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=200&auto=format&fit=crop&q=60'

const hintChips = ['برگر', 'پیتزا', 'سالاد', 'قهوه', 'دسر']

let debounceTimer = null

watch(searchOpen, async (val) => {
  if (val) {
    query.value = ''
    results.value = []
    await nextTick()
    inputEl.value?.focus()
    document.addEventListener('keydown', onKeyTrap)
  } else {
    document.removeEventListener('keydown', onKeyTrap)
  }
})

const overlayEl = ref(null)
function onKeyTrap(e) {
  if (e.key !== 'Tab' || !overlayEl.value) return
  const focusables = overlayEl.value.querySelectorAll('button, [href], input, [tabindex]:not([tabindex="-1"])')
  const arr = Array.from(focusables)
  if (!arr.length) return
  const first = arr[0]
  const last = arr[arr.length - 1]
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}

watch(query, (val) => {
  clearTimeout(debounceTimer)
  results.value = []
  if (String(val || '').trim().length < 2) {
    searching.value = false
    return
  }
  searching.value = true
  debounceTimer = setTimeout(() => doSearch(String(val).trim()), 320)
})

async function doSearch(term) {
  if (!term || term.length < 2) {
    searching.value = false
    return
  }
  try {
    const data = await getMenuItems({ search: term, page: 1, page_size: 8 })
    results.value = Array.isArray(data?.items) ? data.items : (Array.isArray(data) ? data : [])
  } catch (_) {
    results.value = []
  } finally {
    searching.value = false
  }
}

function goFirst() {
  if (results.value.length) {
    window.location.href = `/item/${results.value[0].slug}`
    closeSearch()
  }
}
</script>

<style scoped>
.search-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(28, 20, 17, 0.72);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 6rem 1rem 2rem;
}

.search-box {
  width: 100%;
  max-width: 640px;
  background: var(--theme-background, #fdf8f1);
  border-radius: 24px;
  box-shadow: 0 32px 80px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  animation: search-drop 0.22s cubic-bezier(0.22, 1, 0.36, 1);
}

@keyframes search-drop {
  from { transform: translateY(-24px) scale(0.97); opacity: 0; }
  to { transform: none; opacity: 1; }
}

.search-input-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.2rem;
  border-bottom: 1px solid var(--theme-border, #e0d8cf);
}

.search-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--text-muted, #846b58);
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 1.1rem;
  color: var(--text-primary, #3f2a1d);
  outline: none;
  font-family: inherit;
  direction: rtl;
  min-width: 0;
}

.search-input::placeholder {
  color: var(--text-muted, #a09080);
}

.search-close-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: none;
  background: var(--theme-surface-alt, #f0ece7);
  color: var(--text-muted, #846b58);
  font-size: 1.1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.search-results {
  max-height: 420px;
  overflow-y: auto;
}

.result-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 1.2rem;
  text-decoration: none;
  border-bottom: 1px solid var(--theme-border, #e0d8cf);
  transition: background 0.15s;
  color: inherit;
}

.result-row:last-child {
  border-bottom: none;
}

.result-row:hover {
  background: var(--theme-surface-alt, #f0ece7);
}

.result-img-wrap {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--theme-surface-alt, #f0ece7);
}

.result-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-name {
  display: block;
  font-size: 0.92rem;
  color: var(--text-primary, #3f2a1d);
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-cat {
  display: block;
  font-size: 0.75rem;
  color: var(--text-muted, #846b58);
  margin-top: 0.1rem;
}

.result-price {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--accent-gold, #c98d42);
  white-space: nowrap;
  flex-shrink: 0;
}

.result-arrow {
  font-size: 1rem;
  color: var(--text-muted, #846b58);
  flex-shrink: 0;
}

.search-empty,
.search-hint {
  padding: 2.5rem 1.5rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.empty-icon,
.hint-icon {
  font-size: 2.4rem;
}

.search-empty p,
.search-hint p {
  margin: 0;
  color: var(--text-muted, #846b58);
  font-size: 0.9rem;
}

.search-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--theme-border, #e0d8cf);
  border-top-color: var(--accent-green, #6f4a31);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-bottom: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.hint-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  justify-content: center;
  margin-top: 0.5rem;
}

.hint-chip {
  border: 1px solid var(--glass-border, #d5c3af);
  background: transparent;
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  font-size: 0.8rem;
  cursor: pointer;
  color: var(--text-primary, #3f2a1d);
  transition: background 0.15s, border-color 0.15s;
}

.hint-chip:hover {
  background: var(--accent-green20, rgba(111,74,49,0.1));
  border-color: var(--accent-green, #6f4a31);
}

.search-modal-enter-active,
.search-modal-leave-active {
  transition: opacity 0.2s;
}

.search-modal-enter-from,
.search-modal-leave-to {
  opacity: 0;
}
</style>
