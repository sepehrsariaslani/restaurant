<template>
  <section class="editable-table" :class="[`tone-${tone}`]">
    <header class="table-head">
      <div class="meta">
        <strong>{{ title }}</strong>
        <small v-if="subtitle">{{ subtitle }}</small>
      </div>
      <div class="head-actions">
        <slot name="toolbar" />
        <button type="button" class="primary-btn" @click="openAdd" :disabled="disabled || !allowCreate">
          {{ addButtonLabel }}
        </button>
      </div>
    </header>

    <ManagementDataTable :columns="tableColumns" :rows="rows" :row-key="rowKey">
      <template v-for="column in columns" :key="`slot-${column.key}`" #[`cell-${column.key}`]="slotProps">
        <slot :name="`cell-${column.key}`" v-bind="slotProps">
          {{ slotProps.value }}
        </slot>
      </template>

      <template #cell-actions="{ row, rowIndex }">
        <div class="row-actions">
          <button type="button" class="secondary-btn mini" @click="openEdit(row, rowIndex)" :disabled="disabled || !allowEdit">
            {{ editButtonLabel }}
          </button>
          <button
            type="button"
            class="secondary-btn mini danger"
            @click="removeRow(rowIndex)"
            :disabled="disabled || !allowDelete"
          >
            {{ deleteButtonLabel }}
          </button>
        </div>
      </template>

      <template #empty>{{ emptyText }}</template>
    </ManagementDataTable>

    <ManagementPopup v-model:open="editorOpen" :title="popupTitle" :subtitle="popupSubtitle">
      <p v-if="editorError" class="error">{{ editorError }}</p>
      <slot name="editor" :draft="draft" :mode="editorMode" />

      <template #footer>
        <div class="foot-actions">
          <button type="button" class="secondary-btn" @click="editorOpen = false">انصراف</button>
          <button type="button" class="primary-btn" @click="saveDraft" :disabled="disabled">
            {{ saveButtonLabel }}
          </button>
        </div>
      </template>
    </ManagementPopup>
  </section>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import ManagementDataTable from '@/components/management/ManagementDataTable.vue'
import ManagementPopup from '@/components/management/ManagementPopup.vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  columns: {
    type: Array,
    default: () => [],
  },
  rowKey: {
    type: [String, Function],
    default: 'name',
  },
  title: {
    type: String,
    default: 'جدول',
  },
  subtitle: {
    type: String,
    default: '',
  },
  tone: {
    type: String,
    default: 'default',
  },
  addButtonLabel: {
    type: String,
    default: 'افزودن آیتم',
  },
  editButtonLabel: {
    type: String,
    default: 'ویرایش',
  },
  deleteButtonLabel: {
    type: String,
    default: 'حذف',
  },
  saveButtonLabel: {
    type: String,
    default: 'ذخیره',
  },
  emptyText: {
    type: String,
    default: 'داده ای برای نمایش وجود ندارد.',
  },
  popupTitleAdd: {
    type: String,
    default: 'افزودن آیتم',
  },
  popupTitleEdit: {
    type: String,
    default: 'ویرایش آیتم',
  },
  popupSubtitle: {
    type: String,
    default: 'اطلاعات را تکمیل کنید.',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  allowCreate: {
    type: Boolean,
    default: true,
  },
  allowEdit: {
    type: Boolean,
    default: true,
  },
  allowDelete: {
    type: Boolean,
    default: true,
  },
  createEmptyRow: {
    type: Function,
    default: () => ({}),
  },
  normalizeRow: {
    type: Function,
    default: (row) => row,
  },
  validateRow: {
    type: Function,
    default: () => '',
  },
})

const emit = defineEmits(['update:modelValue'])

const rows = computed(() => (Array.isArray(props.modelValue) ? props.modelValue : []))
const tableColumns = computed(() => [...props.columns, { key: 'actions', label: 'عملیات' }])

const editorOpen = ref(false)
const editorMode = ref('add')
const editorIndex = ref(-1)
const editorError = ref('')
const draft = reactive({})

const popupTitle = computed(() => (editorMode.value === 'edit' ? props.popupTitleEdit : props.popupTitleAdd))

function cloneValue(value) {
  if (typeof structuredClone === 'function') {
    try {
      return structuredClone(value)
    } catch (cloneError) {
      // Fallback for objects that browser structuredClone cannot serialize.
    }
  }
  try {
    return JSON.parse(JSON.stringify(value || {}))
  } catch (jsonError) {
    return {}
  }
}

function writeDraft(payload) {
  for (const key of Object.keys(draft)) {
    delete draft[key]
  }
  const source = payload && typeof payload === 'object' ? payload : {}
  Object.assign(draft, cloneValue(source))
}

function openAdd() {
  editorMode.value = 'add'
  editorIndex.value = -1
  editorError.value = ''
  writeDraft(props.createEmptyRow())
  editorOpen.value = true
}

function openEdit(row, index) {
  editorMode.value = 'edit'
  editorIndex.value = Number(index || 0)
  editorError.value = ''
  writeDraft(row)
  editorOpen.value = true
}

function removeRow(index) {
  const next = [...rows.value]
  next.splice(index, 1)
  emit('update:modelValue', next)
}

function saveDraft() {
  const validationMessage = String(props.validateRow(draft) || '').trim()
  if (validationMessage) {
    editorError.value = validationMessage
    return
  }

  const normalized = props.normalizeRow(cloneValue(draft))
  const next = [...rows.value]

  if (editorMode.value === 'edit' && editorIndex.value >= 0) {
    next.splice(editorIndex.value, 1, normalized)
  } else {
    next.push(normalized)
  }

  emit('update:modelValue', next)
  editorOpen.value = false
}
</script>

<style scoped>
.editable-table {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 14px;
  background: rgb(var(--palette-eggshell-rgb) / 0.58);
  padding: 0.56rem;
  display: grid;
  gap: 0.48rem;
}

.editable-table.tone-accent {
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.34);
  background: linear-gradient(180deg, rgb(var(--palette-deep-saffron-rgb) / 0.05), rgb(var(--palette-eggshell-rgb) / 0.58));
}

.table-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 0.6rem;
}

.meta {
  display: grid;
  gap: 0.15rem;
}

.meta strong {
  font-size: 0.88rem;
}

.meta small {
  color: var(--text-muted);
  font-size: 0.76rem;
  line-height: 1.7;
}

.head-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  align-items: center;
  justify-content: end;
}

.row-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.26rem;
}

.mini {
  padding: 0.3rem 0.48rem;
  font-size: 0.7rem;
}

.danger {
  color: var(--danger);
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.35);
}

.foot-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.4rem;
}

.error {
  margin: 0;
  color: var(--danger);
  font-size: 0.78rem;
}

@media (max-width: 760px) {
  .table-head {
    display: grid;
  }

  .head-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }

  .head-actions :deep(.searchable-dropdown) {
    width: 100%;
  }
}
</style>
