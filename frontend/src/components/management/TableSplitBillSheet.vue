<template>
  <Teleport to="body">
    <div v-if="open" class="split-backdrop" @click.self="$emit('close')">
      <section class="split-sheet" dir="rtl">
        <header class="split-head">
          <div class="split-head-info">
            <h3>تقسیم صورت‌حساب — {{ tableLabel }}</h3>
            <p>
              جمع کل: <strong>{{ formatMoney(grandTotal, currency) }}</strong>
              <span v-if="unassignedTotal > 0" class="unassigned-warn">
                · {{ formatMoney(unassignedTotal, currency) }} تخصیص نیافته
              </span>
            </p>
          </div>
          <div class="split-head-actions">
            <button type="button" class="split-action-btn" @click="equalSplit">تقسیم مساوی</button>
            <button type="button" class="split-action-btn" @click="resetAssignments">پاک کردن</button>
            <button type="button" class="split-close-btn" @click="$emit('close')">✕</button>
          </div>
        </header>

        <div class="split-body">
          <aside class="split-items-panel">
            <div class="split-panel-head">
              <span>آیتم‌های میز</span>
              <small>{{ flatItems.length }} آیتم</small>
            </div>
            <div class="split-items-list">
              <div
                v-for="item in flatItems"
                :key="item.uid"
                class="split-item-row"
                :class="{ 'is-assigned': item.assignedTo !== null }"
              >
                <div class="split-item-info">
                  <span class="split-item-name">{{ item.menu_item_title }}</span>
                  <small class="split-item-price">
                    {{ toFaDigits(item.quantity) }} × {{ formatMoney(item.price_at_time, currency) }}
                    = {{ formatMoney(item.line_total, currency) }}
                  </small>
                  <small v-if="item.note" class="split-item-note">{{ item.note }}</small>
                </div>
                <div class="split-item-btns">
                  <button
                    v-for="p in persons"
                    :key="p.id"
                    type="button"
                    class="split-person-tag"
                    :class="{ active: item.assignedTo === p.id }"
                    :style="{ '--tag-color': p.color }"
                    @click="toggleAssign(item, p.id)"
                  >
                    {{ p.label }}
                  </button>
                </div>
              </div>
              <p v-if="!flatItems.length" class="split-empty">سفارش تأیید شده‌ای وجود ندارد.</p>
            </div>
          </aside>

          <main class="split-persons-panel">
            <div class="split-panel-head">
              <span>افراد</span>
              <button type="button" class="split-add-person-btn" @click="addPerson">+ افزودن نفر</button>
            </div>
            <div class="split-persons-list">
              <article v-for="p in persons" :key="p.id" class="split-person-card" :style="{ '--card-color': p.color }">
                <header class="split-person-head">
                  <div class="split-person-label-wrap">
                    <span class="split-person-dot" :style="{ background: p.color }"></span>
                    <input
                      v-model="p.label"
                      class="split-person-name-input"
                      maxlength="20"
                      :placeholder="`نفر ${p.id}`"
                    />
                  </div>
                  <div class="split-person-meta">
                    <strong class="split-person-total">{{ formatMoney(personTotal(p.id), currency) }}</strong>
                    <button
                      v-if="persons.length > 1"
                      type="button"
                      class="split-remove-person"
                      @click="removePerson(p.id)"
                      title="حذف نفر"
                    >✕</button>
                  </div>
                </header>
                <ul class="split-person-items">
                  <li v-for="item in personItems(p.id)" :key="item.uid" class="split-person-item">
                    <span>{{ item.menu_item_title }}</span>
                    <span class="split-person-item-total">{{ formatMoney(item.line_total, currency) }}</span>
                  </li>
                  <li v-if="!personItems(p.id).length" class="split-person-empty">آیتمی تخصیص نیافته</li>
                </ul>
                <footer class="split-person-footer">
                  <button type="button" class="split-print-btn" @click="printPerson(p)" :disabled="!personItems(p.id).length">
                    🖨 چاپ صورتحساب
                  </button>
                </footer>
              </article>
            </div>
          </main>
        </div>

        <div v-if="printPreview" class="split-print-area" @click.self="printPreview = null">
          <div class="split-print-receipt">
            <div class="receipt-header">
              <h4>صورتحساب {{ printPreview.label }}</h4>
              <p>{{ tableLabel }}</p>
            </div>
            <ul class="receipt-items">
              <li v-for="item in printPreview.items" :key="item.uid">
                <span>{{ item.menu_item_title }} × {{ toFaDigits(item.quantity) }}</span>
                <span>{{ formatMoney(item.line_total, currency) }}</span>
              </li>
            </ul>
            <div class="receipt-total">
              <strong>جمع قابل پرداخت</strong>
              <strong>{{ formatMoney(printPreview.total, currency) }}</strong>
            </div>
            <div class="receipt-print-actions">
              <button type="button" class="split-action-btn" @click="doPrint">چاپ</button>
              <button type="button" class="split-action-btn" @click="printPreview = null">بستن</button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  open: { type: Boolean, default: false },
  orders: { type: Array, default: () => [] },
  currency: { type: String, default: 'IRR' },
  tableLabel: { type: String, default: '' },
})

defineEmits(['close'])

function toFaDigits(val) {
  return String(val ?? '').replace(/\d/g, (d) => '۰۱۲۳۴۵۶۷۸۹'[d])
}

const PERSON_COLORS = ['#2563eb', '#16a34a', '#dc2626', '#d97706', '#7c3aed', '#db2777', '#0891b2']

let personCounter = 0

function makePersons(n) {
  return Array.from({ length: n }, (_, i) => ({
    id: ++personCounter,
    label: `نفر ${i + 1}`,
    color: PERSON_COLORS[i % PERSON_COLORS.length],
  }))
}

const persons = ref(makePersons(2))
const assignments = ref({})
const printPreview = ref(null)

const flatItems = computed(() => {
  const items = []
  let uid = 0
  for (const order of props.orders) {
    for (const item of order.items || []) {
      items.push({
        uid: `${order.name}_${item.row_name}_${uid++}`,
        row_name: item.row_name,
        order_name: order.name,
        menu_item: item.menu_item,
        menu_item_title: item.menu_item_title || item.menu_item,
        quantity: Number(item.quantity || 1),
        price_at_time: Number(item.price_at_time || 0),
        line_total: Number(item.line_total || 0),
        note: item.note || '',
        assignedTo: assignments.value[`${order.name}_${item.row_name}`] ?? null,
      })
    }
  }
  return items
})

const grandTotal = computed(() =>
  flatItems.value.reduce((sum, item) => sum + item.line_total, 0),
)

const unassignedTotal = computed(() =>
  flatItems.value
    .filter((item) => item.assignedTo === null)
    .reduce((sum, item) => sum + item.line_total, 0),
)

function assignmentKey(item) {
  return `${item.order_name}_${item.row_name}`
}

function toggleAssign(item, personId) {
  const key = assignmentKey(item)
  if (assignments.value[key] === personId) {
    delete assignments.value[key]
    assignments.value = { ...assignments.value }
  } else {
    assignments.value = { ...assignments.value, [key]: personId }
  }
}

function personItems(personId) {
  return flatItems.value.filter((item) => item.assignedTo === personId)
}

function personTotal(personId) {
  return personItems(personId).reduce((sum, item) => sum + item.line_total, 0)
}

function addPerson() {
  const n = persons.value.length
  persons.value.push({
    id: ++personCounter,
    label: `نفر ${n + 1}`,
    color: PERSON_COLORS[n % PERSON_COLORS.length],
  })
}

function removePerson(personId) {
  persons.value = persons.value.filter((p) => p.id !== personId)
  const newMap = {}
  for (const [k, v] of Object.entries(assignments.value)) {
    if (v !== personId) newMap[k] = v
  }
  assignments.value = newMap
}

function resetAssignments() {
  assignments.value = {}
}

function equalSplit() {
  if (!persons.value.length || !flatItems.value.length) return
  const newMap = {}
  flatItems.value.forEach((item, idx) => {
    const person = persons.value[idx % persons.value.length]
    newMap[assignmentKey(item)] = person.id
  })
  assignments.value = newMap
}

function printPerson(person) {
  const items = personItems(person.id)
  if (!items.length) return
  printPreview.value = {
    label: person.label,
    items,
    total: personTotal(person.id),
  }
}

function doPrint() {
  window.print()
}

watch(
  () => props.open,
  (val) => {
    if (val) {
      personCounter = 0
      persons.value = makePersons(2)
      assignments.value = {}
      printPreview.value = null
    }
  },
)
</script>

<style scoped>
.split-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  background: rgb(0 0 0 / 0.55);
  display: grid;
  place-items: center;
  padding: 1rem;
}

.split-sheet {
  width: min(1180px, 100%);
  max-height: calc(100vh - 2rem);
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 24px 60px rgb(0 0 0 / 0.25);
  display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
  font-family: inherit;
}

.split-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.2rem 0.9rem;
  border-bottom: 1px solid #e5eaef;
  background: #f8fafc;
}

.split-head-info h3 {
  margin: 0 0 0.2rem;
  font-size: 1rem;
  font-weight: 700;
  color: #0f3146;
}

.split-head-info p {
  margin: 0;
  font-size: 0.84rem;
  color: #4a6378;
}

.unassigned-warn {
  color: #c75c00;
  font-weight: 600;
}

.split-head-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.split-action-btn {
  background: #015a72;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0.42rem 0.85rem;
  font-size: 0.8rem;
  cursor: pointer;
  font-family: inherit;
}

.split-action-btn:hover {
  background: #013f52;
}

.split-action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.split-close-btn {
  background: transparent;
  border: 1px solid #d0dae3;
  border-radius: 10px;
  color: #4a6378;
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  cursor: pointer;
  font-size: 0.85rem;
}

.split-close-btn:hover {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #dc2626;
}

.split-body {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(320px, 1.2fr);
  overflow: hidden;
}

.split-items-panel,
.split-persons-panel {
  display: grid;
  grid-template-rows: auto 1fr;
  overflow: hidden;
  border-inline-start: 1px solid #e5eaef;
}

.split-items-panel {
  border-inline-start: none;
}

.split-panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.9rem;
  border-bottom: 1px solid #e5eaef;
  background: #f3f6f9;
  font-size: 0.82rem;
  font-weight: 600;
  color: #2e4a5a;
}

.split-panel-head small {
  font-weight: 400;
  color: #6b84949c;
  font-size: 0.78rem;
}

.split-add-person-btn {
  background: transparent;
  border: 1px dashed #015a72;
  color: #015a72;
  border-radius: 8px;
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
  cursor: pointer;
  font-family: inherit;
}

.split-items-list,
.split-persons-list {
  overflow-y: auto;
  padding: 0.5rem;
  display: grid;
  gap: 0.4rem;
  align-content: start;
}

.split-item-row {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.55rem 0.7rem;
  background: #fff;
  display: grid;
  gap: 0.4rem;
  transition: border-color 0.15s;
}

.split-item-row.is-assigned {
  border-color: #bfdbfe;
  background: #f0f7ff;
}

.split-item-info {
  display: grid;
  gap: 0.12rem;
}

.split-item-name {
  font-size: 0.84rem;
  font-weight: 600;
  color: #0f3146;
}

.split-item-price {
  font-size: 0.75rem;
  color: #4a6378;
}

.split-item-note {
  font-size: 0.72rem;
  color: #8a9fb0;
  font-style: italic;
}

.split-item-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.split-person-tag {
  border: 1.5px solid var(--tag-color, #015a72);
  border-radius: 8px;
  background: transparent;
  color: var(--tag-color, #015a72);
  padding: 0.2rem 0.55rem;
  font-size: 0.74rem;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.12s;
}

.split-person-tag.active {
  background: var(--tag-color, #015a72);
  color: #fff;
}

.split-empty {
  color: #8a9fb0;
  font-size: 0.8rem;
  text-align: center;
  padding: 1rem;
}

.split-person-card {
  border: 1.5px solid rgb(from var(--card-color, #015a72) r g b / 0.25);
  border-radius: 14px;
  background: #fff;
  overflow: hidden;
}

.split-person-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.7rem;
  background: rgb(from var(--card-color, #015a72) r g b / 0.06);
  border-bottom: 1px solid rgb(from var(--card-color, #015a72) r g b / 0.12);
}

.split-person-label-wrap {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.split-person-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.split-person-name-input {
  border: none;
  background: transparent;
  font-size: 0.84rem;
  font-weight: 600;
  color: #0f3146;
  font-family: inherit;
  width: 100px;
  outline: none;
}

.split-person-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.split-person-total {
  font-size: 0.84rem;
  color: #0f3146;
}

.split-remove-person {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.78rem;
  padding: 0.1rem 0.2rem;
}

.split-remove-person:hover {
  color: #dc2626;
}

.split-person-items {
  list-style: none;
  margin: 0;
  padding: 0.4rem 0.7rem;
  display: grid;
  gap: 0.25rem;
}

.split-person-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #2e4a5a;
}

.split-person-item-total {
  font-weight: 600;
}

.split-person-empty {
  font-size: 0.76rem;
  color: #a0b4c0;
  text-align: center;
  padding: 0.3rem;
}

.split-person-footer {
  padding: 0.4rem 0.7rem;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
}

.split-print-btn {
  background: transparent;
  border: 1px solid #015a72;
  color: #015a72;
  border-radius: 8px;
  padding: 0.28rem 0.7rem;
  font-size: 0.76rem;
  cursor: pointer;
  font-family: inherit;
}

.split-print-btn:hover {
  background: #015a72;
  color: #fff;
}

.split-print-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.split-print-area {
  position: absolute;
  inset: 0;
  background: rgb(0 0 0 / 0.45);
  display: grid;
  place-items: center;
  padding: 1rem;
  z-index: 10;
}

.split-print-receipt {
  background: #fff;
  border-radius: 16px;
  padding: 1.2rem 1.5rem;
  min-width: 280px;
  max-width: 420px;
  width: 100%;
  box-shadow: 0 12px 40px rgb(0 0 0 / 0.2);
}

.receipt-header {
  text-align: center;
  margin-bottom: 0.8rem;
  border-bottom: 1px dashed #cdd7e0;
  padding-bottom: 0.6rem;
}

.receipt-header h4 {
  margin: 0 0 0.2rem;
  font-size: 0.95rem;
}

.receipt-header p {
  margin: 0;
  font-size: 0.8rem;
  color: #4a6378;
}

.receipt-items {
  list-style: none;
  margin: 0 0 0.8rem;
  padding: 0;
  display: grid;
  gap: 0.3rem;
}

.receipt-items li {
  display: flex;
  justify-content: space-between;
  font-size: 0.82rem;
  color: #1e3545;
}

.receipt-total {
  display: flex;
  justify-content: space-between;
  padding: 0.6rem 0;
  border-top: 2px solid #0f3146;
  font-size: 0.9rem;
  margin-bottom: 0.8rem;
}

.receipt-print-actions {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

@media (max-width: 720px) {
  .split-body {
    grid-template-columns: 1fr;
    overflow-y: auto;
  }

  .split-items-panel,
  .split-persons-panel {
    overflow: visible;
    border: none;
    border-top: 1px solid #e5eaef;
  }

  .split-items-list,
  .split-persons-list {
    overflow: visible;
  }
}

@media print {
  .split-backdrop {
    display: none;
  }

  .split-print-area {
    position: fixed;
    inset: 0;
    background: #fff;
    padding: 1.5cm;
  }

  .split-print-receipt {
    box-shadow: none;
    border-radius: 0;
    max-width: 100%;
  }

  .receipt-print-actions {
    display: none;
  }
}
</style>
