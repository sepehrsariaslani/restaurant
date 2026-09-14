<template>
  <div class="hb" dir="rtl">
    <header class="hb__topbar">
      <div class="hb__title">
        <h1>\u0637\u0631\u0627\u062d\u06cc \u0635\u0641\u062d\u0647 \u0627\u0635\u0644\u06cc</h1>
        <p>\u0628\u0644\u0648\u06a9\u200c\u0647\u0627 \u0631\u0627 \u0628\u06a9\u0634\u06cc\u062f \u0648 \u062c\u0627\u0628\u0647\u200c\u062c\u0627 \u06a9\u0646\u06cc\u062f\u060c \u0637\u0631\u0627\u062d\u06cc \u0648 \u0645\u062d\u062a\u0648\u0627\u06cc \u0647\u0631 \u0628\u0644\u0648\u06a9 \u0631\u0627 \u062a\u0646\u0638\u06cc\u0645 \u06a9\u0646\u06cc\u062f.</p>
      </div>
      <div class="hb__actions">
        <span v-if="company" class="hb__company">\u0634\u0639\u0628\u0647: {{ company }}</span>
        <span class="hb__status" v-if="statusText">{{ statusText }}</span>
        <button class="hb__btn hb__btn--ghost" type="button" :disabled="loading || saving" @click="load">
          {{ loading ? '\u062f\u0631 \u062d\u0627\u0644 \u0628\u0627\u0631\u06af\u0630\u0627\u0631\u06cc...' : '\u0628\u0627\u0632\u0646\u0634\u0627\u0646\u06cc' }}
        </button>
        <button class="hb__btn hb__btn--primary" type="button" :disabled="loading || saving" @click="save">
          {{ saving ? '\u062f\u0631 \u062d\u0627\u0644 \u0630\u062e\u06cc\u0631\u0647...' : '\u0630\u062e\u06cc\u0631\u0647 \u0637\u0631\u0627\u062d\u06cc' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="hb__error">{{ error }}</p>

    <div class="hb__grid">
      <!-- LEFT: block list + palette -->
      <aside class="hb__panel">
        <section class="hb__card">
          <h2 class="hb__card-title">\u0628\u0644\u0648\u06a9\u200c\u0647\u0627\u06cc \u0635\u0641\u062d\u0647</h2>
          <ul class="hb__blocks">
            <li
              v-for="(block, index) in blocks"
              :key="block.id"
              class="hb__block"
              :class="{ active: selectedId === block.id, disabled: !block.enabled, dragging: dragIndex === index }"
              draggable="true"
              @dragstart="onDragStart(index)"
              @dragover.prevent="onDragOver(index)"
              @drop="onDrop(index)"
              @dragend="onDragEnd"
              @click="selectedId = block.id"
            >
              <span class="hb__handle" aria-hidden="true">\u2630</span>
              <span class="hb__block-info">
                <strong>{{ typeLabel(block.type) }}</strong>
                <small>{{ variantLabel(block) }}</small>
              </span>
              <span class="hb__block-tools">
                <button type="button" :title="block.enabled ? '\u063a\u06cc\u0631\u0641\u0639\u0627\u0644' : '\u0641\u0639\u0627\u0644'" @click.stop="toggleEnabled(block)">
                  {{ block.enabled ? '\u25c9' : '\u25cb' }}
                </button>
                <button type="button" title="\u062d\u0630\u0641" class="danger" @click.stop="removeBlock(index)">\u00d7</button>
              </span>
            </li>
            <li v-if="!blocks.length" class="hb__empty">\u0647\u0646\u0648\u0632 \u0628\u0644\u0648\u06a9\u06cc \u0627\u0636\u0627\u0641\u0647 \u0646\u0634\u062f\u0647.</li>
          </ul>
        </section>

        <section class="hb__card">
          <h2 class="hb__card-title">\u0627\u0641\u0632\u0648\u062f\u0646 \u0628\u0644\u0648\u06a9</h2>
          <div class="hb__palette">
            <button
              v-for="def in palette"
              :key="def.type"
              type="button"
              class="hb__palette-item"
              @click="addBlock(def.type)"
            >
              <strong>{{ def.label }}</strong>
              <small>{{ (def.variants || []).length }} \u0637\u0631\u0627\u062d\u06cc</small>
            </button>
          </div>
        </section>
      </aside>

      <!-- CENTER: live preview -->
      <main class="hb__preview">
        <div class="hb__preview-bar">
          <span>\u067e\u06cc\u0634\u200c\u0646\u0645\u0627\u06cc\u0634 \u0632\u0646\u062f\u0647</span>
          <div class="hb__device">
            <button :class="{ active: device === 'desktop' }" @click="device = 'desktop'">\u062f\u0633\u06a9\u062a\u0627\u067e</button>
            <button :class="{ active: device === 'mobile' }" @click="device = 'mobile'">\u06af\u0648\u0634\u06cc</button>
          </div>
        </div>
        <div class="hb__stage" :class="`hb__stage--${device}`">
          <div class="hb__viewport">
            <RestaurantLandingPage :key="previewKey" :boot="previewBoot" preview-mode />
          </div>
        </div>
      </main>

      <!-- RIGHT: editor for selected block -->
      <aside class="hb__panel">
        <section class="hb__card" v-if="selectedBlock">
          <h2 class="hb__card-title">{{ typeLabel(selectedBlock.type) }}</h2>

          <div class="hb__variants">
            <button
              v-for="variant in variantsFor(selectedBlock)"
              :key="variant.value"
              type="button"
              class="hb__variant"
              :class="{ selected: selectedBlock.variant === variant.value }"
              @click="setVariant(selectedBlock, variant.value)"
            >
              <strong>{{ variant.label }}</strong>
              <small>{{ variant.desc }}</small>
            </button>
          </div>

          <BlockPropsForm :block="selectedBlock" @update="updateProps" />
        </section>
        <section class="hb__card hb__card--muted" v-else>
          <p>\u06cc\u06a9 \u0628\u0644\u0648\u06a9 \u0631\u0627 \u0627\u0632 \u0644\u06cc\u0633\u062a \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f \u062a\u0627 \u0637\u0631\u0627\u062d\u06cc \u0648 \u0645\u062d\u062a\u0648\u0627\u06cc \u0622\u0646 \u0631\u0627 \u0648\u06cc\u0631\u0627\u06cc\u0634 \u06a9\u0646\u06cc\u062f.</p>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import RestaurantLandingPage from '@/pages/RestaurantLandingPage.vue'
import BlockPropsForm from '@/components/management/builder/BlockPropsForm.vue'
import { BLOCK_TYPE_LIST, getBlockType, createBlock } from '@/utils/blockRegistry'
import { resolveHomeLayout } from '@/utils/pageLayout'
import {
  getManagementPageLayout,
  setManagementPageLayout,
} from '@/utils/pageLayoutApi'

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

const palette = BLOCK_TYPE_LIST

const boot = (typeof window !== 'undefined' && window._BOOT) || {}

const selectedBlock = computed(() => blocks.value.find((b) => b.id === selectedId.value) || null)

const previewBoot = computed(() => ({
  ...boot,
  page_layout: {
    home: {
      blocks: blocks.value.map((b, i) => ({ ...b, order: i })),
    },
  },
}))

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
  const v = variantsFor(block).find((x) => x.value === block.variant)
  return v ? v.label : block.variant
}

function addBlock(type) {
  const block = createBlock(type)
  if (!block) return
  blocks.value = [...blocks.value, block]
  selectedId.value = block.id
  bumpPreview()
}

function removeBlock(index) {
  const removed = blocks.value[index]
  blocks.value = blocks.value.filter((_, i) => i !== index)
  if (removed && removed.id === selectedId.value) {
    selectedId.value = blocks.value[0]?.id || ''
  }
  bumpPreview()
}

function toggleEnabled(block) {
  block.enabled = !block.enabled
  bumpPreview()
}

function setVariant(block, variant) {
  block.variant = variant
  bumpPreview()
}

function updateProps(nextProps) {
  if (!selectedBlock.value) return
  selectedBlock.value.props = nextProps
  bumpPreview()
}

function ensureSelectedBlock() {
  if (!blocks.value.length) {
    selectedId.value = ''
    return
  }

  const hasSelected = blocks.value.some((block) => block.id === selectedId.value)
  if (!hasSelected) {
    selectedId.value = blocks.value[0]?.id || ''
  }
}

// --- native drag & drop reordering ---
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
}

function onDrop() {
  bumpPreview()
}

function onDragEnd() {
  dragIndex.value = -1
  bumpPreview()
}

async function load() {
  loading.value = true
  error.value = ''
  statusText.value = ''
  try {
    const result = await getManagementPageLayout('home')
    company.value = String(result?.company || '').trim()
    const stored = Array.isArray(result?.blocks) ? result.blocks : []
    if (stored.length) {
      blocks.value = stored.map((b) => ({
        ...createBlock(b.type),
        ...b,
        props: { ...(createBlock(b.type)?.props || {}), ...(b.props || {}) },
      }))
    } else {
      // Seed the builder with the current (legacy/derived) layout so the
      // admin starts from what the site already shows.
      blocks.value = resolveHomeLayout(boot).map((b) => ({ ...b }))
    }
    ensureSelectedBlock()
    statusText.value = 'بارگذاری شد.'
  } catch (e) {
    error.value = e?.message || 'بارگذاری طراحی ناموفق بود.'
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
    const payloadBlocks = blocks.value.map((b, i) => ({
      id: b.id,
      type: b.type,
      variant: b.variant,
      enabled: b.enabled ? 1 : 0,
      order: i,
      props: b.props || {},
    }))
    const result = await setManagementPageLayout({ page: 'home', blocks: payloadBlocks })
    company.value = String(result?.company || company.value || '').trim()
    statusText.value = 'طراحی ذخیره شد.'
  } catch (e) {
    error.value = e?.message || 'ذخیره طراحی ناموفق بود.'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.hb {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
}

.hb__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.hb__title h1 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 800;
}

.hb__title p {
  margin: 0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--text-muted, var(--mg-text-muted));
}

.hb__actions {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.hb__company {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-muted, var(--mg-text-muted));
  background: #f1e7db;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
}

.hb__status {
  font-size: 0.8rem;
  color: var(--accent-green, var(--mg-success));
  font-weight: 700;
}

.hb__btn {
  border: 0;
  cursor: pointer;
  padding: 0.6rem 1.15rem;
  border-radius: 10px;
  font: inherit;
  font-size: 0.85rem;
  font-weight: 700;
}

.hb__btn--primary {
  background: var(--accent-green, var(--mg-success));
  color: #fff;
}

.hb__btn--ghost {
  background: transparent;
  border: 1px solid var(--border, var(--mg-border-light));
  color: inherit;
}

.hb__btn:disabled {
  opacity: 0.55;
  cursor: default;
}

.hb__error {
  margin: 0;
  padding: 0.7rem 0.9rem;
  border-radius: 10px;
  background: #fbe9e9;
  color: var(--mg-danger);
  font-size: 0.85rem;
}

.hb__grid {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 1rem;
  align-items: start;
}

.hb__panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  position: sticky;
  top: 1rem;
}

.hb__card {
  background: #fff;
  border: 1px solid var(--border, var(--mg-border-light));
  border-radius: 14px;
  padding: 0.9rem;
}

.hb__card--muted {
  color: var(--text-muted, var(--mg-text-muted));
  font-size: 0.85rem;
}

.hb__card-title {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  font-weight: 800;
}

.hb__blocks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.hb__block {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.6rem;
  border-radius: 10px;
  border: 1px solid var(--border, var(--mg-border-light));
  background: #fdfaf6;
  cursor: grab;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.hb__block.active {
  border-color: var(--accent-green, var(--mg-success));
  background: var(--mg-bg-surface);
}

.hb__block.disabled {
  opacity: 0.55;
}

.hb__block.dragging {
  opacity: 0.4;
}

.hb__handle {
  color: var(--text-muted, #b3a494);
  font-size: 1rem;
}

.hb__block-info {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.hb__block-info strong {
  font-size: 0.85rem;
}

.hb__block-info small {
  font-size: 0.72rem;
  color: var(--text-muted, var(--mg-text-muted));
}

.hb__block-tools {
  display: flex;
  gap: 0.2rem;
}

.hb__block-tools button {
  border: 0;
  background: transparent;
  cursor: pointer;
  width: 26px;
  height: 26px;
  border-radius: 7px;
  font-size: 0.95rem;
  color: inherit;
}

.hb__block-tools button.danger {
  color: var(--mg-danger);
}

.hb__block-tools button:hover {
  background: #efe6da;
}

.hb__empty {
  font-size: 0.82rem;
  color: var(--text-muted, var(--mg-text-muted));
  text-align: center;
  padding: 0.8rem;
}

.hb__palette {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
}

.hb__palette-item {
  border: 1px dashed var(--border, var(--mg-border-light));
  background: transparent;
  cursor: pointer;
  padding: 0.6rem 0.5rem;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  text-align: center;
}

.hb__palette-item strong {
  font-size: 0.82rem;
}

.hb__palette-item small {
  font-size: 0.68rem;
  color: var(--text-muted, var(--mg-text-muted));
}

.hb__palette-item:hover {
  border-color: var(--accent-green, var(--mg-success));
  background: var(--mg-bg-surface);
}

.hb__preview {
  background: #fff;
  border: 1px solid var(--border, var(--mg-border-light));
  border-radius: 14px;
  overflow: hidden;
}

.hb__preview-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid var(--border, var(--mg-border-light));
  font-size: 0.82rem;
  font-weight: 700;
}

.hb__device {
  display: inline-flex;
  gap: 0.3rem;
}

.hb__device button {
  border: 1px solid var(--border, var(--mg-border-light));
  background: transparent;
  cursor: pointer;
  padding: 0.3rem 0.7rem;
  border-radius: 8px;
  font: inherit;
  font-size: 0.76rem;
}

.hb__device button.active {
  background: var(--accent-green, var(--mg-success));
  color: #fff;
  border-color: transparent;
}

.hb__stage {
  padding: 1rem;
  background: #f6f1ea;
  max-height: 78vh;
  overflow-y: auto;
}

.hb__viewport {
  margin-inline: auto;
  background: var(--bg-soft, #f7f5f2);
  transition: max-width 0.2s ease;
  position: relative;
}

.hb__viewport :deep(a),
.hb__viewport :deep(button) {
  pointer-events: none;
}

.hb__viewport :deep(.scroll-reveal) {
  opacity: 1;
  transform: none;
  transition: none;
}

.hb__stage--desktop .hb__viewport {
  max-width: 100%;
}

.hb__stage--mobile .hb__viewport {
  max-width: 390px;
  border: 8px solid var(--mg-text-main);
  border-radius: 28px;
  overflow: hidden;
}

.hb__variants {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-bottom: 1rem;
}

.hb__variant {
  border: 1px solid var(--border, var(--mg-border-light));
  background: #fff;
  cursor: pointer;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.hb__variant.selected {
  border-color: var(--accent-green, var(--mg-success));
  background: var(--mg-bg-surface);
}

.hb__variant strong {
  font-size: 0.84rem;
}

.hb__variant small {
  font-size: 0.72rem;
  color: var(--text-muted, var(--mg-text-muted));
}

@media (max-width: 1100px) {
  .hb__grid {
    grid-template-columns: 1fr;
  }

  .hb__panel {
    position: static;
  }
}
</style>
