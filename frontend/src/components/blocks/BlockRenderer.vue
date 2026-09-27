<template>
  <div v-if="def" class="design-block" :class="{ 'design-block--styled': hasDesign, 'design-block--editing': designer?.editing.value, 'design-block--selected': selected, 'design-block--locked': locked }" :data-design-id="block.id" :style="blockDesignStyle(block.design)" @click="selectBlock" @dblclick="editText">
    <span v-if="selected && designer?.editing.value" class="design-block__label">{{ block.name || def.label }}</span>
    <div v-if="block.type === 'section'" class="design-section" :class="`design-section--${block.variant}`">
      <BlockRenderer v-for="child in visibleChildren" :key="child.id" :block="child" :boot="boot" @quick-add="$emit('quick-add', $event)" />
      <p v-if="!visibleChildren.length && designer" class="design-section__empty">کامپوننت‌های این بخش را از کتابخانه اضافه کنید</p>
    </div>
    <component v-else :is="def.component" v-bind="resolvedProps" @quick-add="$emit('quick-add', $event)" />
  </div>
</template>
<script setup>
import { computed, inject } from 'vue'
import { getBlockType } from '@/utils/blockRegistry'
import { blockDesignStyle } from '@/utils/designBlockStyle'
const props = defineProps({ block: { type: Object, required: true }, boot: { type: Object, default: () => ({}) } })
defineEmits(['quick-add'])
const designer = inject('restaurant-design-session', null)
const def = computed(() => getBlockType(props.block?.type))
const selected = computed(() => designer?.selectedId.value === props.block.id)
const locked = computed(() => Boolean(props.block.locked || designer?.isLocked?.(props.block.id)))
const hasDesign = computed(() => Boolean(Object.keys(props.block.design?.desktop || {}).length || Object.keys(props.block.design?.mobile || {}).length))
const visibleChildren = computed(() => (props.block.children || []).filter(child => child.enabled !== false && child.enabled !== 0))
const resolvedProps = computed(() => def.value?.toProps?.(props.block, props.boot) || {})
function ownsTarget(event) { return event.target.closest('[data-design-id]')?.dataset.designId === props.block.id }
function selectBlock(event) {
  if (!designer || !designer.editing.value || locked.value || !ownsTarget(event) || event.target.isContentEditable) return
  event.preventDefault()
  event.stopPropagation()
  designer.select(props.block.id)
}
function editText(event) {
  if (!designer?.editing.value || locked.value || !ownsTarget(event)) return
  const target = event.target.closest('[data-design-field]') || event.target
  const marked = target.dataset?.designField
  const collection = target.dataset?.designCollection
  const index = Number(target.dataset?.designIndex)
  const siteKey = target.dataset?.designSiteKey
  const siteRow = collection ? props.boot[collection === 'about_sections' ? 'about_us_sections' : collection]?.[index] : null
  const fields = def.value?.props || []
  const field = fields.find(field => ['text', 'textarea'].includes(field.type) && (marked ? field.key === marked : String(props.block.props?.[field.key] || field.default || '').trim() === target.textContent.trim()))
  if ((!field && !siteRow) || target.querySelector('input,button,img') || target.children.length > 1) return
  event.preventDefault()
  event.stopPropagation()
  const original = siteRow ? String(siteRow[siteKey] || '') : target.textContent
  target.textContent = original
  target.contentEditable = 'plaintext-only'
  target.focus()
  const selection = window.getSelection()
  const range = document.createRange()
  range.selectNodeContents(target)
  selection.removeAllRanges()
  selection.addRange(range)
  let finished = false
  const finish = (cancel = false) => {
    if (finished) return
    finished = true
    target.removeEventListener('keydown', keydown)
    target.contentEditable = 'false'
    const value = cancel ? original : target.textContent
    target.textContent = value
    if (!cancel) {
      if (siteRow) designer.siteUpdate(collection, index, siteKey, value, props.block.id)
      else designer.update(props.block.id, field.key, value)
    }
  }
  const keydown = event => {
    event.stopPropagation()
    if (event.key === 'Escape') { event.preventDefault(); finish(true); target.blur() }
    if (event.key === 'Enter' && ((!siteRow && field.type !== 'textarea') || event.ctrlKey || event.metaKey)) { event.preventDefault(); target.blur() }
  }
  target.addEventListener('keydown', keydown)
  target.addEventListener('blur', () => finish(), { once: true })
}
</script>
<style scoped>
.design-block { position: relative; min-width: 0; display: var(--block-desktop-display, block); }
.design-block--styled { padding: var(--block-desktop-padding, 0); border-radius: var(--block-desktop-radius, 0); background: var(--block-desktop-background, transparent); color: var(--block-desktop-color, inherit); font-size: var(--block-desktop-font-size, inherit); text-align: var(--block-desktop-align, inherit); min-height: var(--block-desktop-min-height, 0); max-width: var(--block-desktop-max-width, none); margin-inline: auto; width: 100%; }
.design-block--editing { cursor: default; min-height: 24px; }
.design-block--editing:hover { outline: 1px dashed var(--ds-color-action-primary); outline-offset: 2px; }
.design-block--selected { outline: 2px solid var(--ds-color-action-primary) !important; outline-offset: 2px; }
.design-block__label { position: absolute; inset-inline-start: 0; top: 0; transform: translateY(-100%); background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); font-size: 11px; padding: 3px 8px; z-index: 10; pointer-events: none; }
.design-section { display: flex; flex-direction: column; gap: var(--block-desktop-gap, 24px); }
.design-section--grid { display: grid; grid-template-columns: repeat(var(--block-desktop-columns, 2), minmax(0, 1fr)); }
.design-section--row { flex-direction: row; flex-wrap: wrap; }
.design-section--row > * { flex: 1 1 0; }
.design-section__empty { margin: 0; padding: 2rem; text-align: center; color: var(--ds-color-text-muted); border: 1px dashed var(--ds-color-border); }
.design-block :deep([contenteditable="plaintext-only"]) { outline: 2px solid var(--ds-color-focus-ring); cursor: text; min-width: 1ch; }
@media (max-width: 767px) {
  .design-block { display: var(--block-mobile-display, var(--block-desktop-display, block)); }
  .design-block--styled { padding: var(--block-mobile-padding, var(--block-desktop-padding, 0)); border-radius: var(--block-mobile-radius, var(--block-desktop-radius, 0)); background: var(--block-mobile-background, var(--block-desktop-background, transparent)); color: var(--block-mobile-color, var(--block-desktop-color, inherit)); font-size: var(--block-mobile-font-size, var(--block-desktop-font-size, inherit)); text-align: var(--block-mobile-align, var(--block-desktop-align, inherit)); min-height: var(--block-mobile-min-height, var(--block-desktop-min-height, 0)); max-width: var(--block-mobile-max-width, var(--block-desktop-max-width, none)); }
  .design-section { gap: var(--block-mobile-gap, var(--block-desktop-gap, 16px)); }
  .design-section--grid { grid-template-columns: repeat(var(--block-mobile-columns, 1), minmax(0, 1fr)); }
  .design-section--row { flex-direction: column; }
}
</style>
