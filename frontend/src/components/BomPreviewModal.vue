<template>
  <teleport to="body">
    <div class="sheet-overlay" v-if="open" @click.self="close">
      <section class="sheet-panel" ref="panelRef" dir="rtl">
        <header class="sheet-head">
          <div class="drag-handle" aria-hidden="true"></div>
          <div class="sheet-head__row">
            <button class="icon-btn back-btn" type="button" @click="close" aria-label="بازگشت">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
            </button>
            <span class="sheet-title">Preview BOM</span>
            <button class="icon-btn close-btn" type="button" @click="close" aria-label="بستن">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </header>

        <div class="sheet-body" ref="bodyRef">
          <template v-if="loading">
            <div class="hero-skeleton shimmer"></div>
            <div class="card-skeleton shimmer"></div>
            <div class="card-skeleton shimmer short"></div>
          </template>

          <template v-else>
            <section class="bom-hero-card">
              <div class="bom-hero-media">
                <img class="bom-hero-image" :src="resolvedProductImage" :alt="resolvedTitle" />
                <div class="bom-hero-overlay"></div>
                <div class="bom-hero-actions">
                  <a v-if="previewLink" class="hero-glass-btn" :href="previewLink" aria-label="نمایش صفحه کامل">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>
                  </a>
                </div>
                <div class="bom-hero-copy">
                  <span v-if="productCategory" class="hero-category">{{ productCategory }}</span>
                  <h2>{{ resolvedTitle }}</h2>
                  <p v-if="productDescription">{{ productDescription }}</p>
                  <div class="hero-meta-pills">
                    <span class="hero-pill" v-if="productBasePrice">{{ productBasePrice }}</span>
                    <span class="hero-pill" v-if="leafIngredientCount">{{ leafIngredientCount }} ماده نهایی</span>
                    <span class="hero-pill" v-if="assemblyCount">{{ assemblyCount }} زیرمونتاژ</span>
                    <span class="hero-pill" v-if="productPrepTime">{{ productPrepTime }}</span>
                  </div>
                </div>
              </div>

              <div class="summary-grid summary-grid--single" v-if="hasBom && !error">
                <article class="summary-card">
                  <span>ساختار BOM</span>
                  <strong>{{ bomTreeData.length ? 'چندسطحی' : 'تک‌سطحی' }}</strong>
                  <small>مقادیر زیر-BOMها بر اساس مقدار مصرف واقعی محاسبه می‌شود</small>
                </article>
              </div>
            </section>

            <div class="state-card" v-if="error">
              <div class="state-box">
                <p>{{ error }}</p>
                <button class="primary-btn" type="button" @click="loadBom">تلاش مجدد</button>
              </div>
            </div>

            <div class="state-card" v-else-if="!hasBom">
              <div class="state-box">
                <p>فرمول ساخت برای این محصول ثبت نشده است.</p>
              </div>
            </div>

            <template v-else>
              <nav class="tabs-row" aria-label="تب‌های BOM">
                <button
                  v-for="tab in visibleTabs"
                  :key="tab.key"
                  type="button"
                  class="tab-btn"
                  :class="{ active: activeTab === tab.key }"
                  @click="activeTab = tab.key"
                >
                  <span>{{ tab.label }}</span>
                  <small v-if="tab.count">{{ tab.count }}</small>
                </button>
              </nav>

              <section v-if="activeTab === 'bom'" class="content-stack">
                <article class="content-card production-calculator" v-if="productionOptions.length">
                  <details class="production-accordion">
                    <summary class="production-summary">
                      <span>
                        <strong>ماشین‌حساب تولید</strong>
                        <small>محصول نهایی یا زیر-BOM را انتخاب کنید و مقدار تولید را بزنید</small>
                      </span>
                      <span class="final-bom-badge">ابزار تولید</span>
                    </summary>

                    <div class="production-accordion-body">
                      <div class="calc-form">
                        <label class="calc-field">
                          <span>انتخاب فرمول تولید</span>
                          <select v-model="selectedProductionKey">
                            <option v-for="option in productionOptions" :key="option.key" :value="option.key">
                              {{ option.label }} — خروجی اصلی {{ formatQty(option.batchQty) }} {{ option.uom || 'واحد' }}
                            </option>
                          </select>
                        </label>

                        <label class="calc-field compact">
                          <span>مقدار هدف</span>
                          <div class="target-input-wrap">
                            <input v-model.number="productionTargetQty" type="number" min="0" step="1" inputmode="decimal" />
                            <small>{{ selectedProductionOption?.uom || 'واحد' }}</small>
                          </div>
                        </label>
                      </div>

                      <div class="calc-presets" v-if="selectedProductionOption">
                        <button type="button" @click="setProductionTarget(selectedProductionOption.requiredQty)">
                          مقدار این محصول: {{ formatQty(selectedProductionOption.requiredQty) }} {{ selectedProductionOption.uom || 'واحد' }}
                        </button>
                        <button type="button" @click="setProductionTarget(selectedProductionOption.batchQty)">
                          یک بچ کامل: {{ formatQty(selectedProductionOption.batchQty) }} {{ selectedProductionOption.uom || 'واحد' }}
                        </button>
                        <button type="button" @click="setProductionTarget(selectedProductionOption.batchQty * 3)">
                          ۳ بچ
                        </button>
                        <button type="button" @click="setProductionTarget(1000)" v-if="selectedProductionOption.uom === 'گرم'">
                          ۱۰۰۰ گرم
                        </button>
                      </div>

                      <div class="calc-result" v-if="productionRows.length">
                        <div class="calc-result-head">
                          <div>
                            <strong>مواد لازم برای {{ formatQty(productionTargetQty) }} {{ selectedProductionOption?.uom || 'واحد' }}</strong>
                            <small>ضریب تولید: ×{{ formatQty(productionScale) }}</small>
                          </div>
                          <button class="copy-list-btn" type="button" @click="copyProductionList">
                            {{ copyState || 'کپی لیست' }}
                          </button>
                        </div>
                        <div class="ingredient-list">
                          <div class="ingredient-row" v-for="row in productionRows" :key="`${row.item_code || row.item_name}-${row.uom || ''}`">
                            <div>
                              <strong>{{ row.item_name || row.item_code }}</strong>
                              <small v-if="row.item_code && row.item_code !== row.item_name">{{ row.item_code }}</small>
                            </div>
                            <span class="qty-chip">{{ formatQty(row.qty) }} {{ row.uom || 'واحد' }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </details>
                </article>

                <article class="content-card" v-if="bomTreeData.length">
                  <div class="section-head">
                    <h3>ساختار BOM</h3>
                    <p>برای دیدن مواد داخلی هر زیر-BOM، روی همان ردیف بزنید</p>
                  </div>
                  <BomTree :nodes="bomTreeData" :depth="0" :default-expanded="false" />
                </article>

                <article class="content-card" v-if="finalBomRows.length">
                  <details class="final-bom-accordion">
                    <summary class="final-bom-summary">
                      <span>
                        <strong>سطح آخر BOM</strong>
                        <small>مواد نهایی بعد از باز شدن همه زیر-BOMها</small>
                      </span>
                      <span class="final-bom-badge">{{ finalBomRows.length }} ماده</span>
                    </summary>
                    <div class="ingredient-list final-bom-list">
                      <div class="ingredient-row" v-for="row in finalBomRows" :key="`${row.item_code || row.item_name}-${row.uom || ''}`">
                        <div>
                          <strong>{{ row.item_name || row.item_code }}</strong>
                          <small v-if="row.item_code && row.item_code !== row.item_name">{{ row.item_code }}</small>
                        </div>
                        <span class="qty-chip">{{ formatQty(row.qty) }} {{ row.uom || 'واحد' }}</span>
                      </div>
                    </div>
                  </details>
                </article>
              </section>

              <section v-else-if="activeTab === 'recipe'" class="content-stack">
                <article class="content-card" v-if="operations.length">
                  <div class="section-head">
                    <h3>رسپی / مراحل</h3>
                    <p>مراحل آماده‌سازی ثبت‌شده</p>
                  </div>
                  <ol class="steps-list">
                    <li v-for="(op, idx) in operations" :key="idx" class="step-card">
                      <span class="step-num">{{ idx + 1 }}</span>
                      <div class="step-body">
                        <strong>{{ op.operation }}</strong>
                        <p v-if="op.description">{{ op.description }}</p>
                        <div class="step-meta">
                          <span v-if="op.time_in_mins">{{ op.time_in_mins }} دقیقه</span>
                          <span v-if="op.workstation">ایستگاه: {{ op.workstation }}</span>
                        </div>
                      </div>
                    </li>
                  </ol>
                </article>
                <article class="content-card" v-if="prepNotes">
                  <div class="section-head">
                    <h3>یادداشت‌های آماده‌سازی</h3>
                  </div>
                  <p class="rich-text">{{ prepNotes }}</p>
                </article>
              </section>

              <section v-else-if="activeTab === 'quality'" class="content-stack">
                <article class="content-card" v-if="qcNotes">
                  <div class="section-head">
                    <h3>کنترل کیفیت</h3>
                  </div>
                  <p class="rich-text">{{ qcNotes }}</p>
                </article>
              </section>

              <section v-else-if="activeTab === 'product'" class="content-stack">
                <article class="content-card">
                  <div class="section-head">
                    <h3>اطلاعات محصول</h3>
                    <p>خلاصه مشخصات محصول نهایی</p>
                  </div>
                  <div class="info-grid">
                    <div class="info-item" v-if="productCategory"><span>دسته‌بندی</span><strong>{{ productCategory }}</strong></div>
                    <div class="info-item" v-if="resolvedTitle"><span>نام محصول</span><strong>{{ resolvedTitle }}</strong></div>
                    <div class="info-item" v-if="productBasePrice"><span>قیمت پایه</span><strong>{{ productBasePrice }}</strong></div>
                    <div class="info-item" v-if="productPrepTime"><span>آماده‌سازی</span><strong>{{ productPrepTime }}</strong></div>
                  </div>
                </article>
              </section>
            </template>
          </template>
        </div>


      </section>
    </div>
  </teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import BomTree from './BomTree.vue'
import { getBomPreview } from '@/utils/api'
import { formatMoney } from '@/utils/format'

function flt(value) {
  const num = Number(value)
  return Number.isFinite(num) ? num : 0
}

const props = defineProps({
  open: { type: Boolean, default: false },
  item: { type: Object, default: null },
  currency: { type: String, default: 'TOMAN' },
  branch: { type: String, default: '' },
  isStaffOnly: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref('')
const bomItems = ref([])
const bomTreeData = ref([])
const prepNotes = ref('')
const gramezhData = ref([])
const operations = ref([])
const qcNotes = ref('')
const product = ref(null)
const hasBom = ref(false)
const activeTab = ref('bom')
const selectedProductionKey = ref('')
const productionTargetQty = ref(0)
const copyState = ref('')
let copyTimer = null
let abortController = null

const fallbackImage = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=60'
const item = computed(() => props.item || null)
const resolvedTitle = computed(() => item.value?.title || product.value?.item_name || 'Preview BOM')
const resolvedProductImage = computed(() => String(product.value?.image || item.value?.image || item.value?.item_image || item.value?.website_image || '').trim() || fallbackImage)
const productDescription = computed(() => product.value?.description || item.value?.short_desc || '')
const productCategory = computed(() => item.value?.category_title || product.value?.category || '')
const productBasePrice = computed(() => {
  const price = Number(item.value?.base_price || product.value?.base_price || 0)
  return price > 0 ? formatMoney(price, props.currency || product.value?.currency || 'TOMAN') : ''
})

const productPrepTime = computed(() => {
  const mins = Number(product.value?.prep_time_mins || item.value?.prep_time_mins || 0)
  return mins > 0 ? `${mins} دقیقه` : ''
})
const previewLink = computed(() => {
  const slug = item.value?.slug || product.value?.slug || ''
  return slug ? `/bom-preview/${slug}` : ''
})
const finalBomRows = computed(() => mergeQtyRows(bomItems.value))
const leafIngredientCount = computed(() => finalBomRows.value.length)
const assemblyCount = computed(() => countAssemblies(bomTreeData.value))
const productionOptions = computed(() => {
  const rootRows = bomTreeData.value || []
  const rootBatchQty = flt(product.value?.bom_batch_qty || product.value?.recipe_yield_qty || 1) || 1
  const rootUom = product.value?.bom_batch_uom || product.value?.recipe_uom || 'عدد'
  const rootOption = rootRows.length
    ? [{
        key: 'root-product',
        label: `محصول نهایی — ${resolvedTitle.value}`,
        item_code: product.value?.item_code || item.value?.item_code || '',
        uom: rootUom,
        batchQty: rootBatchQty,
        requiredQty: rootBatchQty,
        baseQty: rootBatchQty,
        children: rootRows,
      }]
    : []
  return [...rootOption, ...collectProductionOptions(rootRows)]
})
const selectedProductionOption = computed(() => productionOptions.value.find((row) => row.key === selectedProductionKey.value) || productionOptions.value[0] || null)
const productionScale = computed(() => {
  const option = selectedProductionOption.value
  if (!option) return 1
  // Children inside each production option are already scaled to `requiredQty`
  // by the backend. The calculator must therefore scale from requiredQty → target,
  // not from full batchQty → target; otherwise values get scaled twice.
  const baseQty = Number(option.baseQty || option.requiredQty || option.batchQty || 1)
  const target = Number(productionTargetQty.value || option.requiredQty || option.batchQty || 0)
  return target > 0 && baseQty > 0 ? target / baseQty : 0
})
const productionRows = computed(() => {
  const option = selectedProductionOption.value
  if (!option) return []
  const rows = collectLeafRows(option.children || [])
  return mergeQtyRows(rows.map((row) => ({ ...row, qty: flt(row.qty) * productionScale.value })))
})
const visibleTabs = computed(() => {
  const tabs = [
    { key: 'bom', label: 'BOM', visible: hasBom.value, count: assemblyCount.value || leafIngredientCount.value },
    { key: 'recipe', label: 'رسپی', visible: operations.value.length || prepNotes.value, count: operations.value.length || '' },
    { key: 'quality', label: 'کنترل کیفیت', visible: qcNotes.value, count: '' },
    { key: 'product', label: 'اطلاعات محصول', visible: true, count: '' },
  ]
  return tabs.filter((tab) => tab.visible)
})

function resetState() {
  error.value = ''
  bomItems.value = []
  bomTreeData.value = []
  prepNotes.value = ''
  gramezhData.value = []
  operations.value = []
  qcNotes.value = ''
  product.value = null
  hasBom.value = false
  activeTab.value = 'bom'
  selectedProductionKey.value = ''
  productionTargetQty.value = 0
  copyState.value = ''
}

function close() {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  emit('close')
}

function normalizeBomNodes(tree) {
  if (!tree) return []
  if (Array.isArray(tree)) return tree
  if (Array.isArray(tree.children)) return tree.children
  return []
}

function countAssemblies(nodes = []) {
  let total = 0
  for (const node of nodes || []) {
    if (node?.is_sub_assembly || (Array.isArray(node?.children) && node.children.length)) {
      total += 1
      total += countAssemblies(node.children || [])
    }
  }
  return total
}

function getProductionKey(node, indexPath) {
  return `${indexPath.join('.')}:${node.item_code || node.item_name || node.title || 'bom'}`
}

function collectProductionOptions(nodes = [], path = []) {
  const options = []
  for (const [index, node] of (nodes || []).entries()) {
    const nextPath = [...path, index]
    const children = Array.isArray(node.children) ? node.children : []
    if ((node.is_sub_assembly || children.length) && children.length) {
      const batchQty = flt(node.bom_batch_qty || node.qty || 1) || 1
      const requiredQty = flt(node.bom_required_qty || node.qty || batchQty)
      options.push({
        key: getProductionKey(node, nextPath),
        label: node.item_name || node.title || node.item_code || 'فرمول تولید',
        item_code: node.item_code || '',
        uom: node.bom_batch_uom || node.uom || 'واحد',
        batchQty,
        requiredQty,
        baseQty: requiredQty || batchQty,
        children,
      })
      options.push(...collectProductionOptions(children, nextPath))
    }
  }
  return options
}

function collectLeafRows(nodes = []) {
  const rows = []
  for (const node of nodes || []) {
    const children = Array.isArray(node.children) ? node.children : []
    if ((node.is_sub_assembly || children.length) && children.length) {
      rows.push(...collectLeafRows(children))
    } else {
      rows.push({
        item_code: node.item_code || '',
        item_name: node.item_name || node.title || node.item_code,
        qty: flt(node.qty),
        uom: node.uom || 'واحد',
      })
    }
  }
  return rows
}

function setProductionTarget(value) {
  productionTargetQty.value = flt(value)
}

async function copyProductionList() {
  const option = selectedProductionOption.value
  if (!option || !productionRows.value.length) return
  const lines = [
    `فرمول: ${option.label}`,
    `مقدار تولید: ${formatQty(productionTargetQty.value)} ${option.uom || 'واحد'}`,
    `ضریب تولید: ×${formatQty(productionScale.value)}`,
    '',
    ...productionRows.value.map((row) => `${row.item_name || row.item_code}: ${formatQty(row.qty)} ${row.uom || 'واحد'}`),
  ]
  try {
    await navigator.clipboard?.writeText(lines.join('\n'))
    copyState.value = 'کپی شد ✓'
  } catch (_) {
    copyState.value = 'آماده کپی'
  }
  clearTimeout(copyTimer)
  copyTimer = setTimeout(() => { copyState.value = '' }, 1800)
}

function formatQty(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return value || '0'
  return Number.isInteger(num) ? num.toString() : num.toFixed(2)
}

function mergeQtyRows(rows = []) {
  const map = new Map()
  for (const row of rows || []) {
    const itemCode = String(row.item_code || '').trim()
    const itemName = String(row.item_name || row.title || row.item_code || '').trim()
    const uom = String(row.uom || 'واحد').trim()
    const key = `${itemCode || itemName}::${uom}`
    if (map.has(key)) {
      map.get(key).qty += flt(row.qty)
    } else {
      map.set(key, { item_code: itemCode, item_name: itemName, qty: flt(row.qty), uom })
    }
  }
  return Array.from(map.values()).sort((a, b) => String(a.item_name || '').localeCompare(String(b.item_name || ''), 'fa'))
}

function syncActiveTab() {
  const keys = visibleTabs.value.map((tab) => tab.key)
  if (!keys.includes(activeTab.value)) activeTab.value = keys[0] || 'product'
}

async function loadBom() {
  if (!item.value?.slug && !item.value?.item_code) return
  if (abortController) abortController.abort()
  abortController = new AbortController()

  loading.value = true
  resetState()

  try {
    const codeOrSlug = item.value?.item_code || item.value?.slug
    const data = await getBomPreview(codeOrSlug, abortController.signal)
    product.value = data.product || {}
    hasBom.value = Number(product.value.has_bom || 0) === 1

    const normalizedTree = normalizeBomNodes(data.bom_tree)
    bomTreeData.value = normalizedTree
    const options = productionOptions.value.length ? productionOptions.value : collectProductionOptions(normalizedTree)
    if (options.length) {
      selectedProductionKey.value = options[0].key
      productionTargetQty.value = options[0].requiredQty || options[0].batchQty || 1
    }

    if (normalizedTree.length) {
      const qtyMap = new Map()
      function collectLeaves(nodes) {
        for (const node of nodes) {
          if ((node.is_sub_assembly || (node.children && node.children.length)) && node.children && node.children.length) {
            collectLeaves(node.children)
          } else {
            const key = node.item_code || node.item_name || node.title
            if (qtyMap.has(key)) {
              const existing = qtyMap.get(key)
              existing.qty = flt(existing.qty) + flt(node.qty)
            } else {
              qtyMap.set(key, {
                item_code: node.item_code || '',
                item_name: node.item_name || node.title || node.item_code,
                qty: node.qty,
                uom: node.uom,
              })
            }
          }
        }
      }
      collectLeaves(normalizedTree)
      bomItems.value = Array.from(qtyMap.values())
    }

    prepNotes.value = data.prep_notes || ''
    gramezhData.value = data.gramezh || []
    operations.value = data.operations || []
    qcNotes.value = data.bom_qc_notes || product.value?.qc_notes || ''
    syncActiveTab()
  } catch (err) {
    if (err.name === 'AbortError') return
    error.value = err.message || 'خطا در دریافت اطلاعات BOM.'
  } finally {
    loading.value = false
    abortController = null
  }
}



watch(
  () => [props.open, item.value?.slug, item.value?.item_code],
  ([isOpen]) => {
    if (isOpen) {
      loadBom()
    } else {
      resetState()
    }
  },
  { deep: true },
)
</script>

<style scoped>
.sheet-overlay {
  position: fixed;
  inset: 0;
  z-index: 125;
  background: rgb(15 23 42 / 0.35);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.sheet-panel {
  width: min(640px, 100%);
  max-height: calc(100dvh - 0.5rem);
  max-height: calc(100svh - 0.5rem);
  border-radius: 22px 22px 0 0;
  padding: 0 0 1rem;
  background: var(--pos-surface-color, #ffffff);
  box-shadow: 0 -12px 48px rgba(0, 0, 0, 0.10);
  display: flex;
  flex-direction: column;
}
.sheet-head {
  position: relative;
  z-index: 2;
  background: var(--pos-surface-color, #ffffff);
  border-radius: 22px 22px 0 0;
  padding: 1.35rem 1rem 0.65rem;
  flex-shrink: 0;
}
.sheet-head__row {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 42px;
  direction: ltr;
}
.sheet-title {
  position: absolute;
  inset-inline: 52px;
  text-align: center;
  color: var(--accent-green);
  font-size: 1rem;
  font-weight: 900;
}
.drag-handle {
  position: absolute;
  top: 0.48rem;
  left: 50%;
  transform: translateX(-50%);
  width: 42px;
  height: 5px;
  border-radius: 999px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.14);
}
.icon-btn {
  width: 42px;
  height: 42px;
  border-radius: 15px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  background: var(--pos-surface-color, #ffffff);
  color: var(--accent-green);
  display: flex;
  align-items: center;
  justify-content: center;
}
.sheet-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  padding: 0 0.85rem 0.85rem;
  display: grid;
  gap: 0.75rem;
}
.bom-hero-card {
  display: grid;
  gap: 0.8rem;
}
.bom-hero-media {
  position: relative;
  min-height: 340px;
  border-radius: 28px;
  overflow: hidden;
  background: linear-gradient(180deg, #fff, #f2eee8);
}
.bom-hero-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  position: absolute;
  inset: 0;
  padding: 0.35rem;
}
.bom-hero-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgb(17 24 39 / 0.02), rgb(17 24 39 / 0.58));
}
.bom-hero-actions {
  position: absolute;
  top: 1rem;
  left: 1rem;
  z-index: 2;
}
.hero-glass-btn {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background: rgb(255 255 255 / 0.14);
  border: 1px solid rgb(255 255 255 / 0.24);
  text-decoration: none;
}
.bom-hero-copy {
  position: absolute;
  right: 1rem;
  left: 1rem;
  bottom: 1rem;
  z-index: 2;
  color: #fff;
}
.bom-hero-copy h2 { margin: 0; font-size: 2rem; font-weight: 900; }
.bom-hero-copy p { margin: 0.35rem 0 0; line-height: 1.8; font-size: 0.88rem; color: rgb(255 255 255 / 0.85); }
.hero-category {
  display: inline-flex;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.14);
  margin-bottom: 0.55rem;
}
.hero-meta-pills { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.8rem; }
.hero-pill {
  padding: 0.38rem 0.75rem;
  border-radius: 999px;
  background: rgb(255 255 255 / 0.14);
  border: 1px solid rgb(255 255 255 / 0.18);
  font-size: 0.78rem;
}
.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}
.summary-grid--single {
  grid-template-columns: 1fr;
}
.summary-card, .content-card, .state-card {
  background: linear-gradient(180deg, rgb(255 255 255 / 0.98), rgb(255 252 248 / 0.98));
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.18);
  border-radius: 22px;
  box-shadow: 0 8px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.06);
}
.summary-card { padding: 1rem; display: flex; flex-direction: column; gap: 0.2rem; }
.summary-card span, .summary-card small { color: var(--text-muted); font-size: 0.74rem; }
.summary-card strong { color: var(--ink-900); font-size: 1.02rem; }
.tabs-row {
  position: sticky;
  top: 0;
  z-index: 5;
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(7rem, 1fr);
  gap: 0.4rem;
  overflow-x: auto;
  padding: 0.35rem;
  background: rgb(255 255 255 / 0.88);
  backdrop-filter: blur(18px);
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.18);
  border-radius: 999px;
  scrollbar-width: none;
  box-shadow: 0 10px 28px rgb(var(--palette-deep-sapphire-rgb) / 0.06);
}
.tabs-row::-webkit-scrollbar { display: none; }
.tab-btn {
  min-height: 44px;
  border: none;
  background: transparent;
  font: inherit;
  padding: 0.55rem 0.85rem;
  border-radius: 999px;
  font-weight: 800;
  color: var(--ink-700);
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease;
}
.tab-btn small {
  min-width: 1.25rem;
  height: 1.25rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  font-size: 0.68rem;
}
.tab-btn:active { transform: scale(0.97); }
.tab-btn.active { background: #4b2e1f; color: #fff; box-shadow: 0 8px 20px rgb(75 46 31 / 0.22); }
.tab-btn.active small { background: rgb(255 255 255 / 0.18); color: #fff; }
.content-stack { display: grid; gap: 0.75rem; }
.content-card { padding: 1rem; }
.section-head h3 { margin: 0; font-size: 1rem; }
.section-head p { margin: 0.25rem 0 0.85rem; font-size: 0.8rem; color: var(--text-muted); }
.ingredient-list { display: grid; gap: 0.65rem; }
.ingredient-row {
  display: flex; justify-content: space-between; align-items: center; gap: 0.75rem;
  padding: 0.8rem 0.9rem; border-radius: 18px; background: rgb(var(--palette-deep-saffron-rgb) / 0.05);
}
.ingredient-row small { display: block; color: var(--text-muted); margin-top: 0.15rem; }
.qty-chip { padding: 0.35rem 0.7rem; border-radius: 999px; background: rgb(var(--palette-deep-sapphire-rgb) / 0.08); font-weight: 800; }
.steps-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.7rem; }
.step-card { display: flex; gap: 0.75rem; padding: 0.85rem; border-radius: 18px; background: rgb(var(--palette-deep-saffron-rgb) / 0.05); }
.step-num { width: 28px; height: 28px; border-radius: 999px; background: #4b2e1f; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; }
.step-body p, .rich-text { margin: 0.3rem 0 0; line-height: 1.85; white-space: pre-line; }
.step-meta { display: flex; flex-wrap: wrap; gap: 0.7rem; color: var(--text-muted); font-size: 0.76rem; margin-top: 0.35rem; }
.production-calculator {
  background: linear-gradient(180deg, #fff, rgb(var(--palette-deep-saffron-rgb) / 0.035));
}
.production-accordion {
  border-radius: 18px;
  overflow: hidden;
}
.production-summary {
  min-height: 56px;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  cursor: pointer;
  touch-action: manipulation;
}
.production-summary::-webkit-details-marker { display: none; }
.production-summary strong {
  display: block;
  color: var(--ink-900);
}
.production-summary small {
  display: block;
  margin-top: 0.2rem;
  color: var(--text-muted);
}
.production-accordion-body {
  padding-top: 1rem;
  animation: soft-reveal 0.24s ease-out;
}
.calc-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px;
  gap: 0.75rem;
}
.calc-field {
  display: grid;
  gap: 0.35rem;
}
.calc-field span {
  font-size: 0.76rem;
  font-weight: 800;
  color: var(--ink-700);
}
.calc-field select,
.calc-field input {
  min-height: 44px;
  border-radius: 15px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.22);
  background: #fff;
  padding: 0.65rem 0.8rem;
  font: inherit;
  color: var(--ink-900);
}
.target-input-wrap {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.4rem;
}
.target-input-wrap small {
  padding: 0.55rem 0.65rem;
  border-radius: 12px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  color: var(--ink-700);
  font-weight: 800;
}
.calc-presets {
  display: flex;
  gap: 0.45rem;
  overflow-x: auto;
  padding: 0.75rem 0 0.25rem;
}
.calc-presets button {
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.18);
  background: #fff;
  border-radius: 999px;
  padding: 0.55rem 0.8rem;
  white-space: nowrap;
  font: inherit;
  font-size: 0.78rem;
  font-weight: 800;
  color: var(--ink-800);
}
.calc-result {
  margin-top: 0.75rem;
  border-radius: 18px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.03);
  padding: 0.85rem;
}
.calc-result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.calc-result-head small {
  display: block;
  margin-top: 0.2rem;
  color: var(--text-muted);
  font-weight: 800;
}
.copy-list-btn {
  min-height: 38px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.22);
  border-radius: 999px;
  background: #fff;
  color: var(--ink-800);
  font: inherit;
  font-size: 0.78rem;
  font-weight: 900;
  padding: 0.4rem 0.75rem;
  white-space: nowrap;
}
.copy-list-btn:active { transform: scale(0.97); }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.info-item { padding: 0.9rem; border-radius: 18px; background: rgb(var(--palette-deep-sapphire-rgb) / 0.05); display: grid; gap: 0.2rem; }
.info-item span { color: var(--text-muted); font-size: 0.74rem; }
.final-bom-accordion {
  border-radius: 18px;
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.03);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  overflow: hidden;
}
.final-bom-accordion[open] .final-bom-list {
  animation: soft-reveal 0.24s ease-out;
}
.final-bom-summary {
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.95rem 1rem;
  cursor: pointer;
}
.final-bom-summary::-webkit-details-marker { display: none; }
.final-bom-summary strong { display: block; color: var(--ink-900); }
.final-bom-summary small { display: block; margin-top: 0.2rem; color: var(--text-muted); }
.final-bom-badge {
  flex-shrink: 0;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.14);
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--ink-800);
}
.final-bom-list { padding: 0 1rem 1rem; }
.state-card { padding: 1rem; }
.state-box { min-height: 160px; display: grid; place-items: center; text-align: center; color: var(--text-muted); }
.primary-btn {
  margin-top: 0.75rem; border: none; border-radius: 999px; padding: 0.7rem 1.2rem; background: #4b2e1f; color: #fff; font: inherit;
}

.hero-skeleton, .card-skeleton { border-radius: 24px; background: var(--surface-alt); }
.hero-skeleton { min-height: 320px; }
.card-skeleton { height: 180px; }
.card-skeleton.short { height: 120px; }
.shimmer {
  background: linear-gradient(90deg, var(--surface-alt) 25%, var(--surface) 50%, var(--surface-alt) 75%);
  background-size: 200% 100%; animation: shimmer 1.5s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
@keyframes soft-reveal {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 640px) {
  .sheet-overlay { padding: 0; }
  .sheet-panel { width: 100%; }
  .bom-hero-media { min-height: 360px; }
}
@media (max-width: 480px) {
  .summary-grid, .info-grid, .calc-form { grid-template-columns: 1fr; }
  .ingredient-row { flex-direction: column; align-items: flex-start; }
  .qty-chip { align-self: flex-start; }
}
</style>
