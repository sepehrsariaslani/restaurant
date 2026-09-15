<template>
  <section class="product-history-panel" dir="rtl">
    <ManagementSurfaceCard title="تاریخچه تغییرات" subtitle="ثبت تغییرات و یادداشت‌های مرتبط با این محصول">
      <p v-if="loading" class="muted">در حال بارگذاری تاریخچه...</p>
      <ManagementSmartDataTable
        v-else
        :columns="historyColumns"
        :rows="historyRows"
        row-key="key"
        :show-search="true"
        :filterable="true"
        :freezable="false"
        :resizable="false"
        empty-text="تغییری برای این محصول ثبت نشده است."
      >
        <template #cell-date="{ value }">{{ formatPersianDate(value, true) }}</template>
        <template #cell-field="{ value }">{{ value || 'فیلد محصول' }}</template>
        <template #cell-old_value="{ value }"><span class="change-value">{{ value || '—' }}</span></template>
        <template #cell-new_value="{ value }"><span class="change-value change-value--new">{{ value || '—' }}</span></template>
      </ManagementSmartDataTable>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="یادداشت‌های محصول" subtitle="یادداشت‌هایی که اعضای تیم درباره این محصول ثبت کرده‌اند" tone="soft">
      <div v-if="comments.length" class="comments-list">
        <article v-for="comment in comments" :key="comment.name" class="comment-item">
          <div class="comment-item-head">
            <strong>{{ comment.owner || 'کاربر' }}</strong>
            <span>{{ formatPersianDate(comment.creation, true) }}</span>
          </div>
          <p>{{ comment.content }}</p>
        </article>
      </div>
      <p v-else class="muted">هنوز یادداشتی ثبت نشده است.</p>
      <div class="comment-form">
        <textarea v-model="draft" class="textarea" rows="2" placeholder="یادداشت خود را بنویسید..."></textarea>
        <button class="primary-btn" type="button" :disabled="saving || !draft.trim()" @click="submitComment">
          {{ saving ? 'در حال ثبت...' : 'ثبت یادداشت' }}
        </button>
      </div>
    </ManagementSurfaceCard>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import ManagementSmartDataTable from '@/components/management/ManagementSmartDataTable.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { formatPersianDate } from '@/utils/managementProductDetail'

const props = defineProps({
  versions: { type: Array, default: () => [] },
  comments: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['submit-comment'])
const draft = ref('')
const fieldLabels = {
  item_name: 'نام کالا', item_code: 'کد کالا', item_group: 'گروه کالا', stock_uom: 'واحد',
  restaurant_enabled: 'وضعیت نمایش', restaurant_coming_soon: 'به‌زودی', restaurant_out_of_stock: 'ناموجود',
  restaurant_short_desc: 'توضیح کوتاه', restaurant_long_desc: 'توضیح کامل', restaurant_sort_order: 'ترتیب نمایش',
  restaurant_prep_time_mins: 'زمان آماده‌سازی', restaurant_is_featured: 'محصول ویژه', restaurant_branch: 'شعبه',
  restaurant_slug: 'نشانی محصول', image: 'تصویر', disabled: 'غیرفعال در سیستم',
}

const historyColumns = [
  { key: 'date', label: 'زمان' }, { key: 'owner', label: 'ثبت‌کننده' }, { key: 'field', label: 'بخش تغییرکرده' },
  { key: 'old_value', label: 'مقدار قبلی' }, { key: 'new_value', label: 'مقدار جدید' },
]

const historyRows = computed(() => {
  const rows = []
  for (const version of props.versions || []) {
    let parsed = {}
    try { parsed = JSON.parse(version?.data || '{}') } catch (_) { parsed = {} }
    for (const entry of parsed.changed || []) {
      if (!Array.isArray(entry) || entry.length < 3 || ['modified', 'modified_by'].includes(entry[0])) continue
      rows.push({
        key: `${version.name || version.creation}-${entry[0]}-${rows.length}`,
        date: version.creation,
        owner: version.owner || 'سیستم',
        field: fieldLabels[entry[0]] || 'فیلد محصول',
        old_value: formatChangeValue(entry[1]),
        new_value: formatChangeValue(entry[2]),
      })
    }
  }
  return rows
})

function formatChangeValue(value) {
  if (value === 1 || value === true) return 'بله'
  if (value === 0 || value === false) return 'خیر'
  if (value === null || value === undefined || value === '') return '—'
  const text = String(value)
  return text.length > 60 ? `${text.slice(0, 60)}…` : text
}

function submitComment() {
  const value = draft.value.trim()
  if (!value || props.saving) return
  emit('submit-comment', value)
  draft.value = ''
}
</script>

<style scoped>
.product-history-panel { display: grid; gap: .75rem; min-width: 0; }
.change-value { display: inline-block; max-width: 18rem; white-space: normal; color: var(--mg-text-muted); }
.change-value--new { color: var(--mg-text-main); font-weight: 700; }
.comments-list { display: grid; gap: .55rem; }
.comment-item { border: 1px solid var(--mg-border-light); border-radius: 12px; background: var(--mg-bg-surface); padding: .65rem .75rem; }
.comment-item-head { display: flex; justify-content: space-between; gap: .5rem; color: var(--mg-text-muted); font-size: .72rem; }
.comment-item p { margin: .45rem 0 0; line-height: 1.8; }
.comment-form { display: grid; gap: .5rem; margin-top: .75rem; }
.comment-form .primary-btn { justify-self: start; }
@media (max-width: 560px) { .comment-form .primary-btn { width: 100%; justify-content: center; } }
</style>
