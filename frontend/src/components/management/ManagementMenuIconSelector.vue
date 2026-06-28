<template>
  <section class="icon-selector">
    <div class="selector-head">
      <div class="selected-preview" :class="{ empty: !selectedOption }" aria-hidden="true">
        <component :is="selectedComponent" :size="24" stroke-width="1.9" />
      </div>
      <div class="selector-copy">
        <strong>{{ selectedOption?.label || 'بدون آیکون اختصاصی' }}</strong>
        <small>برای نمایش دسته در منوی مشتری</small>
      </div>
      <button v-if="modelValue" class="clear-btn" type="button" @click="selectIcon('')">
        پاک کردن
      </button>
    </div>

    <label class="search-field">
      <span>جستجوی آیکون</span>
      <input
        v-model.trim="search"
        class="input"
        type="search"
        placeholder="مثال: قهوه، نوشیدنی، دسر"
        autocomplete="off"
      />
    </label>

    <div class="icon-grid" role="listbox" aria-label="انتخاب آیکون منو">
      <button
        v-for="option in filteredOptions"
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
      نتیجه‌ای پیدا نشد. با نام ساده‌تری مثل نوشیدنی یا دسر جستجو کنید.
    </p>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import { MENU_ICON_OPTIONS, getMenuIconComponent, sanitizeMenuIcon } from '@/utils/menuIcons'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue'])
const search = ref('')

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

function selectIcon(value) {
  emit('update:modelValue', sanitizeMenuIcon(value))
}
</script>

<style scoped>
.icon-selector {
  display: grid;
  gap: 0.75rem;
}

.selector-head {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) auto;
  gap: 0.65rem;
  align-items: center;
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

.selector-copy small,
.search-field span,
.empty-state {
  color: var(--text-muted);
  font-size: 0.76rem;
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

.search-field {
  display: grid;
  gap: 0.32rem;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.46rem;
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
  background: var(--module-500, #8b5e34);
  border-color: var(--module-500, #8b5e34);
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

@media (max-width: 420px) {
  .selector-head {
    grid-template-columns: 48px minmax(0, 1fr);
  }

  .clear-btn {
    grid-column: 1 / -1;
    justify-self: start;
  }

  .icon-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
