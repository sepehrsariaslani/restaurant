<template>
  <section class="icon-selector">
    <div class="selector-head">
      <button
        class="selector-trigger"
        type="button"
        :aria-expanded="open ? 'true' : 'false'"
        aria-haspopup="listbox"
        @click="open = !open"
      >
        <div class="selected-preview" :class="{ empty: !selectedOption }" aria-hidden="true">
          <component :is="selectedComponent" :size="24" stroke-width="1.9" />
        </div>
        <div class="selector-copy">
          <strong>{{ selectedOption?.label || 'بدون آیکون اختصاصی' }}</strong>
          <small>برای نمایش دسته در منوی مشتری</small>
        </div>
        <span class="trigger-meta">{{ open ? 'بستن' : 'انتخاب آیکون' }}</span>
      </button>

      <button v-if="modelValue" class="clear-btn" type="button" @click="selectIcon('')">
        پاک کردن
      </button>
    </div>

    <div v-if="open" class="selector-panel">
      <label class="search-field">
        <span>جستجوی آیکون</span>
        <input
          v-model.trim="search"
          class="input"
          type="search"
          placeholder="مثال: coffee, pizza, arrow, user"
          autocomplete="off"
        />
      </label>

      <p class="helper-note">
        {{ search ? `نتایج جستجو: ${filteredOptions.length} آیکون` : `همه آیکون‌های Lucide در این لیست قابل انتخاب هستند.` }}
      </p>

      <div class="icon-grid" role="listbox" aria-label="انتخاب آیکون منو">
        <button
          v-for="option in visibleOptions"
          :key="option.value"
          type="button"
          class="icon-option"
          :class="{ selected: modelValue === option.value }"
          :aria-selected="modelValue === option.value ? 'true' : 'false'"
          :aria-label="`انتخاب آیکون ${option.label}`"
          role="option"
          @click="selectIcon(option.value)"
        >
          <component :is="option.component" :size="22" stroke-width="1.9" />
          <span>{{ option.label }}</span>
        </button>
      </div>

      <p v-if="!filteredOptions.length" class="empty-state">
        نتیجه‌ای پیدا نشد. با نام ساده‌تری مثل coffee یا pizza جستجو کنید.
      </p>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { MENU_ICON_OPTIONS, getMenuIconComponent, sanitizeMenuIcon } from '@/utils/menuIcons'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])
const search = ref('')
const open = ref(false)

const selectedValue = computed(() => sanitizeMenuIcon(props.modelValue))
const selectedOption = computed(() => MENU_ICON_OPTIONS.find((option) => option.value === selectedValue.value) || null)
const selectedComponent = computed(() => getMenuIconComponent(selectedValue.value))

const filteredOptions = computed(() => {
  const query = search.value.trim().toLowerCase()
  if (!query) {
    return MENU_ICON_OPTIONS
  }
  return MENU_ICON_OPTIONS.filter((option) => {
    const haystack = [option.value, option.label, ...(option.keywords || [])].join(' ').toLowerCase()
    return haystack.includes(query)
  })
})

const visibleOptions = computed(() => {
  const options = [...filteredOptions.value]
  if (!selectedOption.value) {
    return options
  }
  const exists = options.some((option) => option.value === selectedOption.value.value)
  if (!exists) {
    options.unshift(selectedOption.value)
  }
  return options
})

function selectIcon(value) {
  emit('update:modelValue', sanitizeMenuIcon(value))
  open.value = false
}

watch(open, (next) => {
  if (!next) {
    search.value = ''
  }
})
</script>

<style scoped>
.icon-selector {
  display: grid;
  gap: 0.75rem;
}

.selector-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.65rem;
  align-items: start;
}

.selector-trigger {
  width: 100%;
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) auto;
  gap: 0.65rem;
  align-items: center;
  text-align: right;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 18px;
  background: #fff;
  padding: 0.7rem 0.8rem;
  cursor: pointer;
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.selector-trigger:hover {
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.26);
  box-shadow: 0 10px 24px rgb(15 23 42 / 0.06);
  transform: translateY(-1px);
}

.selector-trigger:focus {
  outline: none;
}

.selected-preview {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  color: var(--ink-700, #6b4f3a);
  background: linear-gradient(145deg, rgb(var(--palette-eggshell-rgb) / 0.9), rgb(var(--palette-june-bud-rgb) / 0.18));
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  box-shadow: 0 10px 22px rgb(15 23 42 / 0.06);
}

.selected-preview.empty {
  color: var(--text-muted);
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.06);
  box-shadow: none;
}

.selector-copy {
  display: grid;
  gap: 0.16rem;
  min-width: 0;
}

.selector-copy strong {
  color: var(--text-primary);
  font-size: 0.9rem;
}

.trigger-meta {
  color: var(--ink-700, #6b4f3a);
  font-size: 0.76rem;
  font-weight: 800;
  white-space: nowrap;
}

.selector-copy small,
.search-field span,
.empty-state,
.helper-note {
  color: var(--text-muted);
  font-size: 0.76rem;
}

.helper-note {
  margin: -0.1rem 0 0;
  line-height: 1.8;
}

.clear-btn {
  min-height: 40px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 999px;
  background: #fff;
  color: var(--ink-700, #6b4f3a);
  font: inherit;
  font-size: 0.76rem;
  font-weight: 800;
  padding: 0.35rem 0.72rem;
  cursor: pointer;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.clear-btn:hover {
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.26);
  transform: translateY(-1px);
}

.selector-panel {
  display: grid;
  gap: 0.75rem;
  padding: 0.85rem;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 18px;
  background: rgb(var(--palette-eggshell-rgb) / 0.34);
}

.search-field {
  display: grid;
  gap: 0.32rem;
}

.search-field .input {
  background: #fff;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.46rem;
  max-height: 320px;
  overflow: auto;
  padding-inline-end: 0.2rem;
}

.icon-grid::-webkit-scrollbar {
  width: 8px;
}

.icon-grid::-webkit-scrollbar-thumb {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 999px;
}

.icon-grid::-webkit-scrollbar-track {
  background: transparent;
}

.icon-option {
  min-height: 74px;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.11);
  border-radius: 16px;
  background: #fff;
  color: var(--text-primary);
  display: grid;
  place-items: center;
  gap: 0.28rem;
  padding: 0.58rem 0.34rem;
  cursor: pointer;
  font: inherit;
  font-size: 0.72rem;
  font-weight: 800;
  transition: background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.icon-option svg {
  color: var(--ink-700, #6b4f3a);
}

.icon-option:hover {
  background: rgb(var(--palette-eggshell-rgb) / 0.56);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.22);
  transform: translateY(-1px);
}

.icon-option.selected {
  background: var(--module-500, var(--mg-primary));
  border-color: var(--module-500, var(--mg-primary));
  color: #fff;
  box-shadow: 0 12px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.2);
}

.icon-option.selected svg {
  color: #fff;
}

.empty-state {
  margin: 0;
  line-height: 1.8;
}

.selector-trigger:focus-visible,
.clear-btn:focus-visible,
.icon-option:focus-visible,
.search-field .input:focus-visible {
  outline: 3px solid rgb(var(--palette-june-bud-rgb) / 0.42);
  outline-offset: 2px;
}

@media (max-width: 420px) {
  .selector-head {
    grid-template-columns: 1fr;
  }

  .selector-trigger {
    grid-template-columns: 48px minmax(0, 1fr);
  }

  .trigger-meta {
    grid-column: 1 / -1;
    justify-self: start;
  }

  .clear-btn {
    justify-self: start;
  }

  .icon-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
