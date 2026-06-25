<template>
  <teleport to="body">
    <div class="bom-modal-overlay" v-if="open" @click.self="close">
      <div class="bom-modal-panel" role="dialog" aria-modal="true" :aria-label="`فرمول ساخت ${itemTitle}`">
        <!-- ── Header with product image ── -->
        <header class="bom-modal-head">
          <button class="bom-close-btn" type="button" @click="close" aria-label="بستن">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
          <div class="bom-head-info">
            <h2 class="bom-modal-title">فرمول ساخت &mdash; {{ itemTitle }}</h2>
            <span v-if="isStaffOnly" class="staff-badge">فقط پرسنل</span>
          </div>
          <img v-if="productImage" :src="productImage" :alt="itemTitle" class="bom-head-img" />
        </header>

        <!-- ── Body ── -->
        <div class="bom-modal-body">
          <!-- Loading -->
          <div class="bom-loading" v-if="loading">
            <div class="bom-spinner"></div>
            <p>در حال بارگذاری اطلاعات فرمول...</p>
          </div>

          <!-- Error -->
          <div class="bom-error" v-else-if="error">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <p>{{ error }}</p>
            <button class="bom-retry-btn" type="button" @click="loadBom" :disabled="loading">تلاش مجدد</button>
          </div>

          <!-- No BOM -->
          <div class="bom-empty" v-else-if="!hasBom">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
            </svg>
            <p>فرمول ساخت برای این محصول ثبت نشده است.</p>
          </div>

          <!-- BOM content -->
          <div class="bom-content" v-else>
            <!-- Nutrition / weight summary -->
            <div class="bom-section" v-if="hasNutrition">
              <h3 class="bom-section-title">ارزش غذایی</h3>
              <div class="bom-nutrition-grid">
                <div class="nutri-chip" v-if="product?.nutrition?.kcal">
                  <small>کالری</small>
                  <strong>{{ product.nutrition.kcal }} kcal</strong>
                </div>
                <div class="nutri-chip" v-if="product?.nutrition?.protein_g">
                  <small>پروتئین</small>
                  <strong>{{ product.nutrition.protein_g }}g</strong>
                </div>
                <div class="nutri-chip" v-if="product?.nutrition?.carb_g">
                  <small>کربوهیدرات</small>
                  <strong>{{ product.nutrition.carb_g }}g</strong>
                </div>
                <div class="nutri-chip" v-if="product?.nutrition?.fat_g">
                  <small>چربی</small>
                  <strong>{{ product.nutrition.fat_g }}g</strong>
                </div>
              </div>
            </div>

            <!-- Preparation steps from BOM operations -->
            <div class="bom-section" v-if="operations.length">
              <h3 class="bom-section-title">مراحل آماده‌سازی</h3>
              <ol class="bom-steps">
                <li v-for="(op, idx) in operations" :key="idx" class="bom-step">
                  <span class="step-num">{{ idx + 1 }}</span>
                  <div class="step-body">
                    <strong class="step-title">{{ op.operation }}</strong>
                    <p v-if="op.description" class="step-desc">{{ op.description }}</p>
                    <div class="step-meta">
                      <span v-if="op.time_in_mins">{{ op.time_in_mins }} دقیقه</span>
                      <span v-if="op.workstation">ایستگاه: {{ op.workstation }}</span>
                    </div>
                  </div>
                </li>
              </ol>
            </div>

            <!-- Prep notes -->
            <div class="bom-section" v-if="prepNotes">
              <h3 class="bom-section-title">یادداشت‌های آماده‌سازی</h3>
              <p class="bom-prep-text">{{ prepNotes }}</p>
            </div>

            <!-- BOM items table -->
            <div class="bom-section" v-if="bomItems.length">
              <h3 class="bom-section-title">مواد اولیه</h3>
              <div class="bom-table-wrap">
                <table class="bom-table">
                  <thead>
                    <tr>
                      <th>ماده</th>
                      <th>مقدار</th>
                      <th>واحد</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in bomItems" :key="row.item_code">
                      <td>{{ row.item_name || row.item_code }}</td>
                      <td class="bom-qty">{{ formatQty(row.qty) }}</td>
                      <td>{{ row.uom || 'واحد' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Gramezh (ingredient quantities) -->
            <div class="bom-section" v-if="gramezhData.length">
              <h3 class="bom-section-title">مقدار مواد (گرم)</h3>
              <div class="bom-table-wrap">
                <table class="bom-table">
                  <thead>
                    <tr>
                      <th>ماده</th>
                      <th>مقدار</th>
                      <th>واحد</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in gramezhData" :key="idx">
                      <td>{{ row.item_name }}</td>
                      <td class="bom-qty">{{ formatQty(row.qty) }}</td>
                      <td>{{ row.uom || 'گرم' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- BOM Tree -->
            <div class="bom-section" v-if="bomTreeData.length">
              <h3 class="bom-section-title">ساختار مواد (BOM)</h3>
              <BomTree :nodes="bomTreeData" :depth="0" :default-expanded="true" />
            </div>

            <!-- QC notes -->
            <div class="bom-section" v-if="qcNotes">
              <h3 class="bom-section-title">نکات کنترل کیفیت</h3>
              <p class="bom-prep-text">{{ qcNotes }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import BomTree from './BomTree.vue'
import { getBomPreview } from '@/utils/api'

function flt(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return 0
  return num
}

const props = defineProps({
  open: { type: Boolean, default: false },
  itemSlug: { type: String, default: '' },
  itemTitle: { type: String, default: '' },
  itemImage: { type: String, default: '' },
  itemCode: { type: String, default: '' },
  isStaffOnly: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref('')
const bomData = ref(null)

const hasBom = ref(false)
const bomItems = ref([])
const bomTreeData = ref([])
const prepNotes = ref('')
const gramezhData = ref([])
const operations = ref([])
const qcNotes = ref('')
const product = ref(null)

let abortController = null

const fallbackImage = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=60'

const productImage = computed(() => props.itemImage || product.value?.image || '')

const hasNutrition = computed(() => {
  const n = product.value?.nutrition
  return n && (n.kcal || n.protein_g || n.carb_g || n.fat_g)
})

function close() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  emit('close')
}

function formatQty(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return value || '0'
  return Number.isInteger(num) ? num.toString() : num.toFixed(2)
}

async function loadBom() {
  if (!props.itemSlug && !props.itemCode) return

  // Cancel any in-flight request
  if (abortController) {
    abortController.abort()
  }
  abortController = new AbortController()

  loading.value = true
  error.value = ''
  bomData.value = null
  hasBom.value = false
  bomItems.value = []
  bomTreeData.value = []
  prepNotes.value = ''
  gramezhData.value = []
  operations.value = []
  qcNotes.value = ''
  product.value = null

  try {
    // Prefer itemCode if available, fall back to slug
    const codeOrSlug = props.itemCode || props.itemSlug
    const data = await getBomPreview(codeOrSlug, abortController.signal)
    bomData.value = data

    product.value = data.product || {}
    hasBom.value = Number(product.value.has_bom || 0) === 1

    if (hasBom.value) {
      // BOM tree
      const tree = data.bom_tree
      if (tree && tree.children) {
        bomTreeData.value = tree.children
        // Collect leaf items for the flat table, aggregating duplicate quantities
        const qtyMap = new Map()
        function collectLeaves(nodes) {
          for (const node of nodes) {
            if (node.is_sub_assembly && node.children && node.children.length) {
              collectLeaves(node.children)
            } else {
              const key = node.item_code
              if (qtyMap.has(key)) {
                const existing = qtyMap.get(key)
                existing.qty = flt(existing.qty) + flt(node.qty)
              } else {
                qtyMap.set(key, {
                  item_code: node.item_code,
                  item_name: node.item_name,
                  qty: node.qty,
                  uom: node.uom,
                })
              }
            }
          }
        }
        collectLeaves(tree.children)
        bomItems.value = Array.from(qtyMap.values())
      }

      prepNotes.value = data.prep_notes || ''
      gramezhData.value = data.gramezh || []
      operations.value = data.operations || []
      qcNotes.value = data.bom_qc_notes || product.value?.qc_notes || ''
    }
  } catch (err) {
    if (err.name === 'AbortError') return
    error.value = err.message || 'خطا در دریافت اطلاعات فرمول.'
  } finally {
    loading.value = false
    abortController = null
  }
}

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      loadBom()
    }
  },
)

function handleKeydown(e) {
  if (e.key === 'Escape' && props.open) {
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.bom-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 130;
  background: rgb(15 23 42 / 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  padding-bottom: max(1rem, env(safe-area-inset-bottom, 1rem));
}

.bom-modal-panel {
  width: min(640px, 100%);
  max-height: calc(100dvh - 2rem);
  max-height: calc(100svh - 2rem);
  border-radius: 24px;
  background: rgb(var(--palette-eggshell-rgb) / 0.98);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.26);
  box-shadow: 0 24px 70px rgb(var(--palette-deep-sapphire-rgb) / 0.28);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.bom-modal-head {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.8rem 1rem;
  flex-shrink: 0;
  border-bottom: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.18);
}

.bom-head-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.bom-modal-title {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--ink-800, #1e1a17);
}

.bom-head-img {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.2);
}

.staff-badge {
  display: inline-flex;
  align-self: flex-start;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  color: rgb(var(--palette-deep-sapphire-rgb) / 1);
}

.bom-close-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
  background: rgb(var(--palette-eggshell-rgb) / 0.92);
  color: var(--ink-600, #4a4038);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.18s ease;
  flex-shrink: 0;
}

.bom-close-btn:hover {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.14);
}

/* Body */
.bom-modal-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Loading */
.bom-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  gap: 1rem;
  color: var(--text-muted, #7a6e64);
  font-size: 0.88rem;
}

.bom-spinner {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid rgb(var(--palette-deep-saffron-rgb) / 0.2);
  border-top-color: rgb(var(--palette-deep-sapphire-rgb) / 0.8);
  animation: bom-spin 0.7s linear infinite;
}

@keyframes bom-spin {
  to { transform: rotate(360deg); }
}

/* Error */
.bom-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  gap: 0.75rem;
  text-align: center;
  color: var(--text-muted, #7a6e64);
}

.bom-error svg {
  color: var(--text-muted, #7a6e64);
}

.bom-retry-btn {
  padding: 0.5rem 1.25rem;
  border-radius: 999px;
  border: none;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.bom-retry-btn:hover {
  background: rgb(var(--palette-deep-sapphire-rgb));
}

/* Empty */
.bom-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  gap: 0.75rem;
  text-align: center;
  color: var(--text-muted, #7a6e64);
  font-size: 0.9rem;
}

.bom-empty svg {
  color: var(--text-muted, #7a6e64);
}

/* BOM content */
.bom-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.bom-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bom-section-title {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--ink-800, #1e1a17);
}

/* Nutrition grid */
.bom-nutrition-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.nutri-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-radius: 12px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.06);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.12);
  min-width: 70px;
}

.nutri-chip small {
  font-size: 0.68rem;
  color: var(--text-muted, #7a6e64);
}

.nutri-chip strong {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--ink-800, #1e1a17);
}

/* Preparation steps */
.bom-steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bom-step {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.6rem 0.75rem;
  border-radius: 12px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.04);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.08);
}

.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.85);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
}

.step-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.step-title {
  font-size: 0.88rem;
  color: var(--ink-800, #1e1a17);
}

.step-desc {
  margin: 0;
  font-size: 0.82rem;
  color: var(--ink-700, #2e2820);
  line-height: 1.6;
}

.step-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: var(--text-muted, #7a6e64);
}

/* BOM table */
.bom-table-wrap {
  border: 1px solid var(--theme-border, #e5d9cc);
  border-radius: 12px;
  overflow: hidden;
}

.bom-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.bom-table th {
  background: rgb(var(--palette-deep-saffron-rgb) / 0.08);
  padding: 0.6rem 0.75rem;
  text-align: right;
  font-weight: 600;
  font-size: 0.78rem;
  color: var(--ink-600, #4a4038);
  border-bottom: 1px solid var(--theme-border, #e5d9cc);
}

.bom-table td {
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid var(--theme-border, #e5d9cc);
  color: var(--ink-800, #1e1a17);
}

.bom-table tr:last-child td {
  border-bottom: none;
}

.bom-qty {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.bom-prep-text {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.7;
  color: var(--ink-700, #2e2820);
  white-space: pre-line;
}
</style>
