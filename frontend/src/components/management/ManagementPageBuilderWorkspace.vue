<template>
  <div class="pbw" dir="rtl">
    <header class="pbw__topbar">
      <div class="pbw__title">
        <h2>{{ pageMeta.label }}</h2>
        <p>{{ pageMeta.subtitle }}</p>
      </div>
      <div class="pbw__actions">
        <span v-if="company" class="pbw__company">شعبه: {{ company }}</span>
        <span class="pbw__status" v-if="statusText">{{ statusText }}</span>
        <button class="pbw__btn pbw__btn--ghost" type="button" :disabled="loading || saving" @click="load(true)">
          {{ loading ? 'در حال بارگذاری...' : 'بازنشانی' }}
        </button>
        <button class="pbw__btn pbw__btn--primary" type="button" :disabled="loading || saving" @click="save">
          {{ saving ? 'در حال ذخیره...' : 'ذخیره چیدمان' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="pbw__error">{{ error }}</p>

    <div class="pbw__grid">
      <aside class="pbw__panel">
        <section class="pbw__card">
          <h3 class="pbw__card-title">بلاک‌های صفحه</h3>
          <ul class="pbw__blocks">
            <li
              v-for="(block, index) in blocks"
              :key="block.id"
              class="pbw__block"
              :class="{ active: selectedId === block.id, disabled: !block.enabled, dragging: dragIndex === index }"
              draggable="true"
              @dragstart="onDragStart(index)"
              @dragover.prevent="onDragOver(index)"
              @drop="onDrop(index)"
              @dragend="onDragEnd"
              @click="selectedId = block.id"
            >
              <span class="pbw__handle" aria-hidden="true">☰</span>
              <span class="pbw__block-info">
                <strong>{{ typeLabel(block.type) }}</strong>
                <small>{{ variantLabel(block) }}</small>
              </span>
              <span class="pbw__block-tools">
                <button type="button" :title="block.enabled ? 'غیرفعال' : 'فعال'" @click.stop="toggleEnabled(block)">
                  {{ block.enabled ? '◉' : '○' }}
                </button>
                <button type="button" title="حذف" class="danger" @click.stop="removeBlock(index)">×</button>
              </span>
            </li>
            <li v-if="!blocks.length" class="pbw__empty">هنوز بلاکی اضافه نشده.</li>
          </ul>
        </section>

        <section class="pbw__card">
          <h3 class="pbw__card-title">افزودن بلاک</h3>
          <div class="pbw__palette">
            <button
              v-for="def in palette"
              :key="def.type"
              type="button"
              class="pbw__palette-item"
              @click="addBlock(def.type)"
            >
              <strong>{{ def.label }}</strong>
              <small>{{ (def.variants || []).length }} طراحی</small>
            </button>
          </div>
        </section>
      </aside>

      <main class="pbw__preview">
        <div class="pbw__preview-bar">
          <span>پیش‌نمایش زنده</span>
          <div class="pbw__device">
            <button :class="{ active: device === 'desktop' }" @click="device = 'desktop'">دسکتاپ</button>
            <button :class="{ active: device === 'mobile' }" @click="device = 'mobile'">گوشی</button>
          </div>
        </div>
        <div class="pbw__stage" :class="`pbw__stage--${device}`">
          <div class="pbw__viewport">
            <component :is="pageMeta.previewComponent" :key="previewKey" :boot="previewBoot" preview-mode />
          </div>
        </div>
      </main>

      <aside class="pbw__panel">
        <section class="pbw__card" v-if="selectedBlock">
          <h3 class="pbw__card-title">{{ typeLabel(selectedBlock.type) }}</h3>
          <div class="pbw__variants">
            <button
              v-for="variant in variantsFor(selectedBlock)"
              :key="variant.value"
              type="button"
              class="pbw__variant"
              :class="{ selected: selectedBlock.variant === variant.value }"
              @click="setVariant(selectedBlock, variant.value)"
            >
              <strong>{{ variant.label }}</strong>
              <small>{{ variant.desc }}</small>
            </button>
          </div>
          <BlockPropsForm :block="selectedBlock" @update="updateProps" />
        </section>
        <section class="pbw__card pbw__card--muted" v-else>
          <p>یک بلاک را از لیست انتخاب کنید تا محتوای آن را ویرایش کنید.</p>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import RestaurantLandingPage from '@/pages/RestaurantLandingPage.vue'
import AboutUsPage from '@/pages/AboutUsPage.vue'
import FaqPage from '@/pages/FaqPage.vue'
import ProductGroupsPage from '@/pages/ProductGroupsPage.vue'
import BlockPropsForm from '@/components/management/builder/BlockPropsForm.vue'
import {
  createBlock,
  getBlockType,
  getPageBlockPalette,
  normalizePageBuilderKey,
} from '@/utils/blockRegistry'
import { buildLegacyPageLayout } from '@/utils/pageLayout'
import { getManagementPageLayout, setManagementPageLayout } from '@/utils/pageLayoutApi'

const DRAFT_CACHE = new Map()

function cloneValue(value) {
  try {
    return JSON.parse(JSON.stringify(value))
  } catch (_) {
    return value
  }
}

const props = defineProps({
  page: { type: String, default: 'home' },
  boot: { type: Object, default: () => ({}) },
  loadLayoutFn: { type: Function, default: null },
  saveLayoutFn: { type: Function, default: null },
  refreshKey: { type: Number, default: 0 },
})

const PAGE_META = {
  home: {
    label: 'صفحه اصلی',
    subtitle: 'چیدمان و ترتیب نمایش بلاک‌های خانه.',
    previewComponent: RestaurantLandingPage,
  },
  about: {
    label: 'درباره ما',
    subtitle: 'نمایش بلاک‌های معرفی برند و داستان مجموعه.',
    previewComponent: AboutUsPage,
  },
  faq: {
    label: 'سوالات متداول',
    subtitle: 'نمایش سکشن‌های پرسش و پاسخ عمومی.',
    previewComponent: FaqPage,
  },
  product_groups: {
    label: 'گروه‌های محصول',
    subtitle: 'نحوه نمایش گروه‌ها و ورودی منوهای دسته‌بندی‌شده.',
    previewComponent: ProductGroupsPage,
  },
}

const normalizedPage = computed(() => normalizePageBuilderKey(props.page))
const pageMeta = computed(() => PAGE_META[normalizedPage.value] || PAGE_META.home)
const palette = computed(() => getPageBlockPalette(normalizedPage.value))

const blocks = ref([])
const selectedId = ref('')
const company = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const statusText = ref('')
const device = ref('desktop')
const dragIndex = ref(-1)
let previewCounter = 0
const previewKey = ref(0)

const selectedBlock = computed(() => blocks.value.find((block) => block.id === selectedId.value) || null)
const previewBoot = computed(() => ({
  ...props.boot,
  page_layout: {
    ...(props.boot?.page_layout || {}),
    [normalizedPage.value]: {
      blocks: blocks.value.map((block, index) => ({ ...block, order: index })),
    },
  },
}))

function cacheDraft() {
  DRAFT_CACHE.set(normalizedPage.value, {
    blocks: cloneValue(blocks.value),
    selectedId: selectedId.value,
    company: company.value,
  })
}

function bumpPreview() {
  previewCounter += 1
  previewKey.value = previewCounter
}

function typeLabel(type) {
  return getBlockType(type)?.label || type
}

function variantsFor(block) {
  return getBlockType(block.type)?.variants || []
}

function variantLabel(block) {
  const variant = variantsFor(block).find((item) => item.value === block.variant)
  return variant ? variant.label : block.variant
}

function ensureSelectedBlock() {
  if (!blocks.value.length) {
    selectedId.value = ''
    return
  }
  if (!blocks.value.some((block) => block.id === selectedId.value)) {
    selectedId.value = blocks.value[0]?.id || ''
  }
}

function addBlock(type) {
  const block = createBlock(type)
  if (!block) return
  blocks.value = [...blocks.value, block]
  selectedId.value = block.id
  cacheDraft()
  bumpPreview()
}

function removeBlock(index) {
  const removed = blocks.value[index]
  blocks.value = blocks.value.filter((_, itemIndex) => itemIndex !== index)
  if (removed?.id === selectedId.value) {
    ensureSelectedBlock()
  }
  cacheDraft()
  bumpPreview()
}

function toggleEnabled(block) {
  block.enabled = !block.enabled
  cacheDraft()
  bumpPreview()
}

function setVariant(block, variant) {
  block.variant = variant
  cacheDraft()
  bumpPreview()
}

function updateProps(nextProps) {
  if (!selectedBlock.value) return
  selectedBlock.value.props = nextProps
  cacheDraft()
  bumpPreview()
}

function onDragStart(index) {
  dragIndex.value = index
}

function onDragOver(index) {
  if (dragIndex.value === -1 || dragIndex.value === index) return
  const list = blocks.value.slice()
  const [moved] = list.splice(dragIndex.value, 1)
  list.splice(index, 0, moved)
  blocks.value = list
  dragIndex.value = index
  cacheDraft()
}

function onDrop() {
  bumpPreview()
}

function onDragEnd() {
  dragIndex.value = -1
  bumpPreview()
}

async function load(forceServer = false) {
  loading.value = true
  error.value = ''
  statusText.value = ''

  try {
    const cached = !forceServer ? DRAFT_CACHE.get(normalizedPage.value) : null
    if (cached?.blocks?.length) {
      blocks.value = cloneValue(cached.blocks)
      selectedId.value = cached.selectedId || ''
      company.value = String(cached.company || '').trim()
      ensureSelectedBlock()
      statusText.value = 'پیش‌نویس محلی بارگذاری شد.'
      return
    }

    const result = props.loadLayoutFn
      ? await props.loadLayoutFn(normalizedPage.value, { forceServer })
      : await getManagementPageLayout(normalizedPage.value)
    company.value = String(result?.company || '').trim()
    const stored = Array.isArray(result?.blocks) ? result.blocks : []

    if (stored.length) {
      blocks.value = stored.map((block) => ({
        ...createBlock(block.type),
        ...block,
        props: { ...(createBlock(block.type)?.props || {}), ...(block.props || {}) },
      }))
    } else {
      blocks.value = buildLegacyPageLayout(props.boot, normalizedPage.value).map((block) => ({ ...block }))
    }

    ensureSelectedBlock()
    cacheDraft()
    statusText.value = 'بارگذاری شد.'
  } catch (loadError) {
    error.value = loadError?.message || 'بارگذاری چیدمان ناموفق بود.'
  } finally {
    loading.value = false
    bumpPreview()
  }
}

async function save() {
  saving.value = true
  error.value = ''
  statusText.value = ''

  try {
    const payloadBlocks = blocks.value.map((block, index) => ({
      id: block.id,
      type: block.type,
      variant: block.variant,
      enabled: block.enabled ? 1 : 0,
      order: index,
      props: block.props || {},
    }))
    const result = props.saveLayoutFn
      ? await props.saveLayoutFn(normalizedPage.value, payloadBlocks)
      : await setManagementPageLayout({
          page: normalizedPage.value,
          blocks: payloadBlocks,
        })
    company.value = String(result?.company || company.value || '').trim()
    cacheDraft()
    statusText.value = 'چیدمان ذخیره شد.'
  } catch (saveError) {
    error.value = saveError?.message || 'ذخیره چیدمان ناموفق بود.'
  } finally {
    saving.value = false
  }
}

watch(
  normalizedPage,
  () => {
    load()
  },
  { immediate: true },
)

watch(
  () => props.refreshKey,
  (next, previous) => {
    if (next === previous) {
      return
    }
    DRAFT_CACHE.delete(normalizedPage.value)
    load(true)
  },
)
</script>

<style scoped>
.pbw {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.pbw__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.pbw__title h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
}

.pbw__title p {
  margin: 0.25rem 0 0;
  font-size: 0.82rem;
  color: var(--text-muted, #8a7867);
}

.pbw__actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.pbw__company {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-muted, #8a7867);
  background: #f1e7db;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
}

.pbw__status {
  font-size: 0.8rem;
  color: var(--accent-green, #2f8f5b);
  font-weight: 700;
}

.pbw__btn {
  border: 0;
  cursor: pointer;
  padding: 0.6rem 1.15rem;
  border-radius: 10px;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 700;
}

.pbw__btn--primary {
  background: var(--accent-green, #2f8f5b);
  color: #fff;
}

.pbw__btn--ghost {
  background: transparent;
  border: 1px solid var(--border, #ddd0c2);
  color: inherit;
}

.pbw__btn:disabled {
  opacity: 0.55;
  cursor: default;
}

.pbw__error {
  margin: 0;
  padding: 0.7rem 0.9rem;
  border-radius: 10px;
  background: #fbe9e9;
  color: #b84f4f;
  font-size: 0.85rem;
}

.pbw__grid {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 1rem;
  align-items: start;
}

.pbw__panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  position: sticky;
  top: 1rem;
}

.pbw__card {
  background: #fff;
  border: 1px solid var(--border, #e6dccf);
  border-radius: 14px;
  padding: 0.9rem;
}

.pbw__card--muted {
  color: var(--text-muted, #8a7867);
  font-size: 0.85rem;
}

.pbw__card-title {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  font-weight: 800;
}

.pbw__blocks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.pbw__block {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.6rem;
  border-radius: 10px;
  border: 1px solid var(--border, #e6dccf);
  background: #fdfaf6;
  cursor: grab;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.pbw__block.active {
  border-color: var(--accent-green, #2f8f5b);
  background: #f2f8f4;
}

.pbw__block.disabled {
  opacity: 0.55;
}

.pbw__block.dragging {
  opacity: 0.4;
}

.pbw__handle {
  color: var(--text-muted, #b3a494);
  font-size: 1rem;
}

.pbw__block-info {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.pbw__block-info strong {
  font-size: 0.85rem;
}

.pbw__block-info small {
  font-size: 0.72rem;
  color: var(--text-muted, #8a7867);
}

.pbw__block-tools {
  display: flex;
  gap: 0.2rem;
}

.pbw__block-tools button {
  border: 0;
  background: transparent;
  cursor: pointer;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  font-size: 0.95rem;
  color: inherit;
}

.pbw__block-tools button.danger {
  color: #b84f4f;
}

.pbw__block-tools button:hover {
  background: #efe6da;
}

.pbw__empty {
  font-size: 0.82rem;
  color: var(--text-muted, #8a7867);
  text-align: center;
  padding: 0.8rem;
}

.pbw__palette {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.pbw__palette-item {
  border: 1px dashed var(--border, #ddd0c2);
  background: transparent;
  cursor: pointer;
  padding: 0.6rem 0.5rem;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  text-align: center;
}

.pbw__palette-item strong {
  font-size: 0.82rem;
}

.pbw__palette-item small {
  font-size: 0.68rem;
  color: var(--text-muted, #8a7867);
}

.pbw__palette-item:hover {
  border-color: var(--accent-green, #2f8f5b);
  background: #f2f8f4;
}

.pbw__preview {
  background: #fff;
  border: 1px solid var(--border, #e6dccf);
  border-radius: 14px;
  overflow: hidden;
}

.pbw__preview-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid var(--border, #e6dccf);
  font-size: 0.82rem;
  font-weight: 700;
}

.pbw__device {
  display: inline-flex;
  gap: 0.3rem;
}

.pbw__device button {
  border: 1px solid var(--border, #ddd0c2);
  background: transparent;
  cursor: pointer;
  padding: 0.3rem 0.7rem;
  border-radius: 8px;
  font: inherit;
  font-size: 0.76rem;
}

.pbw__device button.active {
  background: var(--accent-green, #2f8f5b);
  color: #fff;
  border-color: transparent;
}

.pbw__stage {
  padding: 1rem;
  background: #f6f1ea;
  max-height: 78vh;
  overflow-y: auto;
}

.pbw__viewport {
  margin-inline: auto;
  background: var(--bg-soft, #f7f5f2);
  transition: max-width 0.2s ease;
  position: relative;
}

.pbw__viewport :deep(a),
.pbw__viewport :deep(button) {
  pointer-events: none;
}

.pbw__viewport :deep(.scroll-reveal) {
  opacity: 1;
  transform: none;
  transition: none;
}

.pbw__stage--desktop .pbw__viewport {
  max-width: 100%;
}

.pbw__stage--mobile .pbw__viewport {
  max-width: 390px;
  border: 8px solid #1c1411;
  border-radius: 28px;
  overflow: hidden;
}

.pbw__variants {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.pbw__variant {
  border: 1px solid var(--border, #e6dccf);
  background: #fff;
  cursor: pointer;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.pbw__variant.selected {
  border-color: var(--accent-green, #2f8f5b);
  background: #f2f8f4;
}

.pbw__variant strong {
  font-size: 0.84rem;
}

.pbw__variant small {
  font-size: 0.72rem;
  color: var(--text-muted, #8a7867);
}

@media (max-width: 1100px) {
  .pbw__grid {
    grid-template-columns: 1fr;
  }

  .pbw__panel {
    position: static;
  }
}
</style>
