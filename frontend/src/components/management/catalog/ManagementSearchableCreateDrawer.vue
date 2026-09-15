<template>
  <Teleport to="body">
    <div v-if="open" class="create-drawer-backdrop" @click.self="$emit('close')">
      <aside class="create-drawer" dir="rtl" role="dialog" aria-modal="true" aria-label="ایجاد مورد جدید">
        <header class="create-drawer__head">
          <div>
            <span class="create-drawer__kicker">ایجاد سریع</span>
            <h2>{{ config?.title || `ایجاد ${config?.label || 'مورد'}` }}</h2>
            <p v-if="query">اگر این گزینه در فهرست نیست، همین‌جا آن را بسازید.</p>
          </div>
          <button type="button" class="create-drawer__close" aria-label="بستن" @click="$emit('close')">×</button>
        </header>

        <form class="create-drawer__body" @submit.prevent="submit">
          <div class="create-drawer__query" v-if="query">
            <span>عبارت جستجو</span>
            <strong>{{ query }}</strong>
          </div>
          <label v-for="field in config?.fields || []" :key="field.key" class="create-drawer__field" :class="{ 'is-check': field.type === 'checkbox' }">
            <template v-if="field.type === 'checkbox'">
              <span class="create-drawer__check">
                <input type="checkbox" v-model="draft[field.key]" />
                <span>{{ field.label }}</span>
              </span>
            </template>
            <template v-else>
              <span>{{ field.label }}<b v-if="field.required"> *</b></span>
              <select v-if="field.type === 'select'" class="input" v-model="draft[field.key]">
                <option v-for="option in field.options || []" :key="String(option.value ?? option)" :value="option.value ?? option">{{ option.label ?? option }}</option>
              </select>
              <textarea v-else-if="field.type === 'textarea'" class="textarea" rows="3" v-model.trim="draft[field.key]"></textarea>
              <input v-else class="input" :type="field.type === 'number' ? 'number' : 'text'" :required="field.required" v-model="draft[field.key]" :placeholder="field.placeholder || ''" />
              <small v-if="field.hint">{{ field.hint }}</small>
            </template>
          </label>
          <p v-if="error" class="create-drawer__error">{{ error }}</p>
          <footer class="create-drawer__actions">
            <button type="button" class="secondary-btn" :disabled="saving" @click="$emit('close')">انصراف</button>
            <button type="submit" class="primary-btn" :disabled="saving">{{ saving ? 'در حال ایجاد...' : `ایجاد و انتخاب ${config?.label || 'مورد'}` }}</button>
          </footer>
        </form>
      </aside>
    </div>
  </Teleport>
</template>

<script setup>
import { nextTick, reactive, watch } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  config: { type: Object, default: null },
  query: { type: String, default: '' },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
})

const emit = defineEmits(['close', 'submit'])
const draft = reactive({})

function hydrate() {
  for (const key of Object.keys(draft)) delete draft[key]
  for (const field of props.config?.fields || []) {
    draft[field.key] = props.config?.defaults?.[field.key] ?? field.default ?? (field.type === 'checkbox' ? false : '')
  }
  const nameField = (props.config?.fields || []).find((field) => ['item_name', 'item_code', 'item_group_name', 'warehouse_name', 'supplier_name', 'customer_name', 'account_name', 'price_list_name', 'uom_name'].includes(field.key))
  if (nameField && !draft[nameField.key]) draft[nameField.key] = props.query
  if (props.config?.doctype === 'Item' && !draft.item_code) draft.item_code = props.query
}

function submit() {
  const requiredMissing = (props.config?.fields || []).some((field) => field.required && !String(draft[field.key] ?? '').trim())
  if (requiredMissing) return
  emit('submit', { ...draft })
}

watch(() => [props.open, props.config, props.query], async () => {
  if (!props.open) return
  hydrate()
  await nextTick()
  document.querySelector('.create-drawer input:not([type="checkbox"])')?.focus?.()
}, { immediate: true })
</script>

<style scoped>
.create-drawer-backdrop { position: fixed; inset: 0; z-index: 14000; background: rgb(35 24 17 / .28); backdrop-filter: blur(3px); display: flex; justify-content: flex-start; }
.create-drawer { width: min(30rem, 100vw); height: 100%; overflow-y: auto; background: var(--mg-bg-surface, #fffaf4); color: var(--mg-text-main, #34271f); box-shadow: -12px 0 36px rgb(35 24 17 / .16); padding: 1.15rem; display: grid; align-content: start; gap: 1rem; }
.create-drawer__head { display: flex; justify-content: space-between; gap: .8rem; padding-bottom: .9rem; border-bottom: 1px solid var(--mg-border-light); }
.create-drawer__kicker { color: var(--mg-primary); font-size: .72rem; font-weight: 900; }
.create-drawer h2 { margin: .25rem 0; font-size: 1.1rem; }
.create-drawer__head p { margin: 0; color: var(--mg-text-muted); font-size: .76rem; line-height: 1.8; }
.create-drawer__close { flex: 0 0 auto; width: 2rem; height: 2rem; border: 1px solid var(--mg-border); border-radius: 999px; background: transparent; color: var(--mg-text-muted); font-size: 1.25rem; cursor: pointer; }
.create-drawer__body { display: grid; gap: .8rem; }
.create-drawer__query { display: flex; justify-content: space-between; gap: .7rem; padding: .65rem .75rem; border: 1px dashed var(--mg-border); border-radius: 12px; background: var(--mg-bg-soft); color: var(--mg-text-muted); font-size: .76rem; }
.create-drawer__query strong { color: var(--mg-text-main); direction: rtl; }
.create-drawer__field { display: grid; gap: .3rem; color: var(--mg-text-muted); font-size: .78rem; font-weight: 800; }
.create-drawer__field b { color: var(--mg-danger); }
.create-drawer__field small { color: var(--mg-text-muted); font-size: .68rem; font-weight: 500; }
.create-drawer__check { display: inline-flex; align-items: center; gap: .5rem; min-height: 2.5rem; color: var(--mg-text-main); }
.create-drawer__check input { accent-color: var(--mg-primary); }
.create-drawer__error { margin: 0; color: var(--mg-danger); font-size: .78rem; line-height: 1.8; }
.create-drawer__actions { display: flex; gap: .5rem; justify-content: flex-start; padding-top: .6rem; border-top: 1px solid var(--mg-border-light); }
@media (max-width: 520px) { .create-drawer { padding: .9rem; } .create-drawer__actions { flex-direction: column; } .create-drawer__actions > * { width: 100%; justify-content: center; } }
</style>
