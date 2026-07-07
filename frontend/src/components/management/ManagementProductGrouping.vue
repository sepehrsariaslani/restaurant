<template>
  <ManagementSurfaceCard title="گروه‌بندی کالاها" subtitle="نمایش دسته‌ای کالاها برای مدیریت سریع‌تر">
    <div class="grouping-toolbar">
      <label class="mode-field">
        <span>گروه‌بندی بر اساس</span>
        <SearchableDropdown
          :model-value="modelValue"
          :options="options"
          placeholder="انتخاب نوع گروه‌بندی"
          search-placeholder="جستجوی نوع گروه‌بندی..."
          @update:model-value="$emit('update:modelValue', $event)"
        />
      </label>
      <label class="check-inline">
        <input type="checkbox" :checked="collapsed" @change="$emit('update:collapsed', $event.target.checked)" />
        جمع‌کردن گروه‌ها در حالت پیش‌فرض
      </label>
    </div>

    <p class="muted grouping-hint">
      {{
        modelValue === 'none'
          ? 'گروه‌بندی خاموش است و لیست به صورت یکپارچه نمایش داده می‌شود.'
          : 'برای باز/بسته کردن هر بخش، روی عنوان آن بخش بزنید.'
      }}
    </p>
  </ManagementSurfaceCard>
</template>

<script setup>
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'

defineProps({
  modelValue: {
    type: String,
    default: 'none',
  },
  collapsed: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['update:modelValue', 'update:collapsed'])

const options = [
  { value: 'none', label: 'بدون گروه‌بندی' },
  { value: 'category', label: 'دسته‌بندی منو' },
  { value: 'status', label: 'وضعیت فعال/غیرفعال' },
  { value: 'stock', label: 'وضعیت موجودی' },
]
</script>

<style scoped>
.grouping-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 0.7rem;
}

.mode-field {
  display: grid;
  gap: 0.24rem;
  min-width: 230px;
}

.mode-field span {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.check-inline {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
}

.grouping-hint {
  margin: 0.4rem 0 0;
  font-size: 0.76rem;
}
</style>
