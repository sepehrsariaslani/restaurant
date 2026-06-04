<template>
  <section class="products-panel">
    <header class="toolbar">
      <div class="search-box">
        <span class="icon">⌕</span>
        <input
          class="input dark-input"
          :value="searchTerm"
          @input="$emit('update:searchTerm', $event.target.value)"
          placeholder="نام یا کد محصول"
        />
        <button v-if="searchTerm" type="button" class="clear-search-btn" @click="$emit('update:searchTerm', '')">×</button>
      </div>

      <div class="view-toggle">
        <button type="button" :class="{ active: productView === 'grid' }" @click="$emit('update:productView', 'grid')">
          شبکه ای
        </button>
        <button type="button" :class="{ active: productView === 'list' }" @click="$emit('update:productView', 'list')">
          لیستی
        </button>
      </div>
    </header>

    <div class="scan-row">
      <input
        class="input dark-input"
        :value="scannerInput"
        @input="$emit('update:scannerInput', $event.target.value)"
        @keyup.enter="$emit('scan-scale')"
        placeholder="بارکد وزنی ترازو"
      />
      <button type="button" class="scan-btn" @click="$emit('scan-scale')">تحلیل بارکد</button>
    </div>
    <p class="scan-feedback" v-if="scannerFeedback">{{ scannerFeedback }}</p>

    <p class="hint" v-if="loading">در حال دریافت محصولات...</p>
    <p class="error" v-else-if="error">{{ error }}</p>

    <div class="products-grid" :class="`mode-${productView}`" v-else>
      <article class="product-card" v-for="item in products" :key="item.slug || item.name">
        <button type="button" class="image-btn" @click="$emit('increment-product', item)">
          <img class="product-image" :src="item.image || fallbackImage" :alt="item.title || item.name" />
        </button>

        <div class="product-body">
          <div>
            <span class="stock-chip">موجود</span>
            <h4>{{ item.title || item.name }}</h4>
          </div>
          <strong>{{ formatMoney(item.base_price || item.standard_rate || 0, currency) }}</strong>
        </div>

        <div class="product-actions">
          <div class="counter">
            <button type="button" @click="$emit('decrement-product', item)">-</button>
            <span>{{ displayQty(item.slug) }}</span>
            <button type="button" @click="$emit('increment-product', item)">+</button>
          </div>
          <button type="button" class="bom-btn" @click="$emit('open-bom', item)">BOM</button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { formatMoney } from '@/utils/format'

const props = defineProps({
  products: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
  searchTerm: {
    type: String,
    default: '',
  },
  scannerInput: {
    type: String,
    default: '',
  },
  scannerFeedback: {
    type: String,
    default: '',
  },
  productView: {
    type: String,
    default: 'grid',
  },
  quantityMap: {
    type: Object,
    default: () => ({}),
  },
  fallbackImage: {
    type: String,
    default: '',
  },
  currency: {
    type: String,
    default: 'IRR',
  },
})

defineEmits([
  'update:searchTerm',
  'update:productView',
  'increment-product',
  'decrement-product',
  'open-bom',
  'update:scannerInput',
  'scan-scale',
])

function displayQty(slug) {
  const raw = Number(props.quantityMap?.[slug] || 0)
  return raw.toFixed(3).replace(/\.000$/, '')
}
</script>

<style scoped>
.products-panel {
  border-radius: 18px;
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  padding: 0.75rem;
  color: var(--pos-text);
  min-height: 620px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  margin-bottom: 0.55rem;
}

.search-box {
  display: grid;
  grid-template-columns: 24px 1fr auto;
  align-items: center;
  border-radius: 12px;
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  padding: 0 0.45rem;
  flex: 1;
}

.search-box .input {
  border: 0;
  background: transparent;
  padding-right: 0;
}

.clear-search-btn {
  border: 0;
  background: transparent;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.66);
  cursor: pointer;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  font-size: 1rem;
  line-height: 1;
}

.clear-search-btn:hover {
  background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.1);
  color: var(--pos-primary);
}

.icon {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.55);
}

.view-toggle {
  display: inline-flex;
  border: 1px solid var(--pos-border);
  border-radius: 11px;
  overflow: hidden;
}

.view-toggle button {
  border: 0;
  background: var(--pos-white);
  color: var(--pos-text);
  padding: 0.4rem 0.65rem;
  cursor: pointer;
}

.view-toggle button.active {
  background: var(--pos-primary);
  color: var(--pos-white);
}

.scan-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.45rem;
  margin-bottom: 0.55rem;
}

.scan-btn {
  border: 1px solid var(--pos-primary);
  background: var(--pos-primary);
  border-radius: 10px;
  color: var(--pos-white);
  padding: 0.4rem 0.8rem;
  cursor: pointer;
}

.scan-feedback {
  margin: 0 0 0.55rem;
  color: var(--pos-primary);
  font-size: 0.77rem;
}

.hint {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
}

.error {
  color: var(--pos-accent);
}

.products-grid {
  display: grid;
  gap: 0.55rem;
  max-height: 66vh;
  overflow: auto;
  padding-left: 0.1rem;
}

.products-grid.mode-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.products-grid.mode-list {
  grid-template-columns: 1fr;
}

.product-card {
  border: 1px solid var(--pos-border);
  border-radius: 14px;
  overflow: hidden;
  background: var(--pos-white);
  display: grid;
  align-content: start;
}

.image-btn {
  border: 0;
  background: rgb(var(--pos-primary-rgb, 1 90 114) / 0.06);
  padding: 0;
  cursor: pointer;
  width: 100%;
  display: block;
}

.product-image {
  width: 100%;
  height: 132px;
  object-fit: contain;
  object-position: center;
}

.product-body {
  padding: 0.45rem 0.52rem 0.2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.stock-chip {
  display: inline-flex;
  border-radius: 999px;
  background: var(--pos-soft);
  color: var(--pos-primary);
  border: 1px solid var(--pos-border);
  padding: 0.14rem 0.45rem;
  font-size: 0.68rem;
}

.product-body h4 {
  margin: 0.28rem 0 0;
  font-size: 0.81rem;
}

.product-body strong {
  font-size: 0.76rem;
  color: var(--pos-accent);
}

.product-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.45rem 0.52rem 0.55rem;
}

.counter {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
}

.counter button {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-primary);
  cursor: pointer;
}

.counter span {
  min-width: 44px;
  text-align: center;
  font-size: 0.8rem;
}

.bom-btn {
  border: 1px solid var(--pos-accent);
  background: var(--pos-accent);
  color: var(--pos-white);
  border-radius: 9px;
  padding: 0.34rem 0.65rem;
  cursor: pointer;
}

.dark-input {
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-text);
}

.dark-input::placeholder {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.55);
}

@media (max-width: 1100px) {
  .products-grid.mode-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 680px) {
  .products-grid.mode-grid {
    grid-template-columns: 1fr;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
