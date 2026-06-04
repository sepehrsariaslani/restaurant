<template>
  <header class="pos-header">
    <button type="button" class="close-btn" @click="$emit('close')">بستن</button>

    <div class="customer-block">
      <small class="meta">مدیریت مشتری</small>
      <div class="customer-row">
        <div class="customer-search-wrap">
          <input
            ref="customerSearchRef"
            class="input dark-input"
            :value="customerQuery"
            @input="$emit('update:customerQuery', $event.target.value)"
            @focus="openCustomerDropdown"
            @click="openCustomerDropdown"
            @blur="onCustomerBlur"
            @keydown.down.prevent="moveCustomerActive(1)"
            @keydown.up.prevent="moveCustomerActive(-1)"
            @keydown.enter.prevent="selectActiveCustomer"
            placeholder="نام مشتری، شماره اشتراک، شماره موبایل"
          />

          <div v-if="isCustomerDropdownOpen" class="customer-dropdown">
            <button
              v-for="(customer, index) in customerDropdownOptions"
              :key="customer.key || `${customer.mobile}-${index}`"
              type="button"
              class="customer-option"
              :class="{ active: index === activeCustomerIndex }"
              @mousedown.prevent="selectCustomer(customer)"
            >
              <span class="customer-option-main">{{ customer.label }}</span>
              <span class="customer-option-meta">
                <span v-if="customer.is_new">مشتری جدید</span>
                <template v-else>
                  <span v-if="customer.mobile">{{ customer.mobile }}</span>
                  <span>{{ customer.orders_count }} خرید</span>
                </template>
              </span>
            </button>
            <div v-if="!customerDropdownOptions.length" class="customer-empty">مشتری‌ای پیدا نشد.</div>
          </div>
        </div>
        <button type="button" class="add-btn" @click="$emit('add-customer')">+</button>
      </div>
    </div>

    <label class="field">
      <span>نوع مشتری</span>
      <SearchableDropdown
        :model-value="customerType"
        :options="customerTypeOptions"
        placeholder="انتخاب نوع مشتری"
        search-placeholder="جستجوی نوع مشتری..."
        tone="dark"
        @update:model-value="$emit('update:customerType', $event)"
      />
    </label>

    <div class="guest-counter">
      <span>تعداد مهمان</span>
      <div class="counter-row">
        <button type="button" @click="setGuests(guestCount - 1)">-</button>
        <input
          class="guest-input"
          type="number"
          min="1"
          :value="guestCount"
          @input="setGuests($event.target.value)"
        />
        <button type="button" @click="setGuests(guestCount + 1)">+</button>
      </div>
    </div>

    <div class="status-box">
      <small>{{ dateLabel }}</small>
      <div class="chips">
        <span class="chip" :class="hardwareStatus?.connected ? 'ok' : 'warn'">
          {{ hardwareStatus?.connected ? 'نود متصل' : 'نود قطع' }}
        </span>
        <span class="chip" :class="isOffline ? 'warn' : 'ok'">
          {{ isOffline ? 'آفلاین' : 'آنلاین' }}
        </span>
      </div>
      <button type="button" class="refresh-btn" @click="$emit('refresh-hardware')" :disabled="hardwareLoading">
        {{ hardwareLoading ? 'در حال بررسی...' : 'بررسی اتصال' }}
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'

const props = defineProps({
  customerQuery: {
    type: String,
    default: '',
  },
  customerType: {
    type: String,
    default: 'normal',
  },
  customerOptions: {
    type: Array,
    default: () => [],
  },
  guestCount: {
    type: Number,
    default: 1,
  },
  dateLabel: {
    type: String,
    default: '',
  },
  hardwareStatus: {
    type: Object,
    default: () => ({ connected: false }),
  },
  hardwareLoading: {
    type: Boolean,
    default: false,
  },
  isOffline: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'close',
  'add-customer',
  'select-customer',
  'create-customer',
  'update:customerQuery',
  'update:customerType',
  'update:guestCount',
  'refresh-hardware',
])

const customerSearchRef = ref(null)
const activeCustomerIndex = ref(-1)
const customerDropdownOpen = ref(false)

const customerTypeOptions = [
  { value: 'normal', label: 'عادی' },
  { value: 'vip', label: 'VIP' },
  { value: 'corporate', label: 'شرکتی' },
]

const filteredCustomerOptions = computed(() => {
  const allOptions = Array.isArray(props.customerOptions) ? props.customerOptions : []
  const query = String(props.customerQuery || '')
    .trim()
    .toLowerCase()
  if (!query) {
    return allOptions.slice(0, 12)
  }

  const normalizedDigits = query.replace(/\D/g, '')
  return allOptions
    .filter((row) => {
      const label = String(row.label || '').toLowerCase()
      const mobile = String(row.mobile || '')
      if (label.includes(query)) {
        return true
      }
      if (normalizedDigits && mobile.replace(/\D/g, '').includes(normalizedDigits)) {
        return true
      }
      return false
    })
    .slice(0, 12)
})

const createCustomerOption = computed(() => {
  const query = String(props.customerQuery || '').trim()
  if (!query) {
    return null
  }
  const normalizedQuery = query.toLowerCase()
  const queryDigits = normalizedQuery.replace(/\D/g, '')
  const hasExact = filteredCustomerOptions.value.some((row) => {
    const label = String(row.label || '').trim().toLowerCase()
    const mobileDigits = String(row.mobile || '').replace(/\D/g, '')
    if (label === normalizedQuery) {
      return true
    }
    if (queryDigits && mobileDigits && mobileDigits === queryDigits) {
      return true
    }
    return false
  })
  if (hasExact) {
    return null
  }
  return {
    key: `create-${query}`,
    label: `ایجاد مشتری جدید: ${query}`,
    mobile: '',
    orders_count: 0,
    is_new: true,
    raw_query: query,
  }
})

const customerDropdownOptions = computed(() => {
  const options = [...filteredCustomerOptions.value]
  if (createCustomerOption.value) {
    options.unshift(createCustomerOption.value)
  }
  return options
})

const isCustomerDropdownOpen = computed(() => customerDropdownOpen.value)

function setGuests(value) {
  const next = Math.max(Number(value || 1), 1)
  emit('update:guestCount', Math.round(next))
}

function openCustomerDropdown() {
  customerDropdownOpen.value = true
  activeCustomerIndex.value = customerDropdownOptions.value.length ? 0 : -1
}

function onCustomerBlur() {
  window.setTimeout(() => {
    customerDropdownOpen.value = false
    activeCustomerIndex.value = -1
  }, 120)
}

function moveCustomerActive(step) {
  if (!customerDropdownOptions.value.length) {
    return
  }
  if (!customerDropdownOpen.value) {
    openCustomerDropdown()
    return
  }
  const length = customerDropdownOptions.value.length
  const current = activeCustomerIndex.value < 0 ? 0 : activeCustomerIndex.value
  activeCustomerIndex.value = (current + step + length) % length
}

function selectActiveCustomer() {
  if (!customerDropdownOpen.value || !customerDropdownOptions.value.length) {
    return
  }
  const index = activeCustomerIndex.value < 0 ? 0 : activeCustomerIndex.value
  const selected = customerDropdownOptions.value[index]
  if (selected) {
    selectCustomer(selected)
  }
}

function selectCustomer(customer) {
  if (customer?.is_new) {
    emit('create-customer', customer)
  } else {
    emit('select-customer', customer)
  }
  customerDropdownOpen.value = false
  activeCustomerIndex.value = -1
}

function focusCustomerSearch() {
  if (typeof customerSearchRef.value?.focus === 'function') {
    try {
      customerSearchRef.value.focus({ preventScroll: true })
    } catch (focusErr) {
      customerSearchRef.value.focus()
    }
  }
  customerSearchRef.value?.select?.()
}

defineExpose({
  focusCustomerSearch,
})
</script>

<style scoped>
.pos-header {
  display: grid;
  grid-template-columns: auto minmax(280px, 1fr) 160px 180px minmax(180px, 220px);
  gap: 0.65rem;
  align-items: center;
  border-radius: 20px;
  background: var(--pos-white);
  border: 1px solid var(--pos-border);
  padding: 0.7rem;
  color: var(--pos-text);
}

.close-btn,
.refresh-btn,
.add-btn,
.guest-counter button {
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-primary);
  border-radius: 10px;
  cursor: pointer;
}

.close-btn,
.refresh-btn {
  padding: 0.45rem 0.8rem;
}

.customer-block {
  display: grid;
  gap: 0.3rem;
}

.meta {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
  font-size: 0.72rem;
}

.customer-row {
  display: grid;
  grid-template-columns: 1fr 42px;
  gap: 0.4rem;
  align-items: start;
}

.customer-search-wrap {
  position: relative;
}

.customer-dropdown {
  position: absolute;
  top: calc(100% + 0.3rem);
  inset-inline: 0;
  border-radius: 12px;
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  box-shadow: 0 14px 24px rgb(var(--pos-primary-rgb, 1 90 114) / 0.16);
  max-height: 250px;
  overflow-y: auto;
  z-index: 40;
}

.customer-option {
  width: 100%;
  border: 0;
  border-bottom: 1px solid rgb(var(--pos-primary-rgb, 1 90 114) / 0.12);
  background: transparent;
  color: var(--pos-text);
  padding: 0.42rem 0.55rem;
  display: grid;
  gap: 0.12rem;
  text-align: right;
  cursor: pointer;
}

.customer-option:last-of-type {
  border-bottom: 0;
}

.customer-option.active,
.customer-option:hover {
  background: var(--pos-soft);
}

.customer-option-main {
  font-size: 0.8rem;
  font-weight: 600;
}

.customer-option-meta {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
  font-size: 0.7rem;
}

.customer-empty {
  padding: 0.55rem;
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
  font-size: 0.74rem;
  text-align: center;
}

.add-btn {
  font-size: 1.3rem;
  line-height: 1;
  background: var(--pos-accent);
  border-color: var(--pos-accent);
  color: var(--pos-white);
}

.field {
  display: grid;
  gap: 0.25rem;
  font-size: 0.76rem;
}

.guest-counter {
  display: grid;
  gap: 0.25rem;
  font-size: 0.76rem;
}

.counter-row {
  display: grid;
  grid-template-columns: 30px 1fr 30px;
  gap: 0.3rem;
  align-items: center;
}

.guest-input {
  width: 100%;
  border-radius: 8px;
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-text);
  text-align: center;
  padding: 0.35rem 0.2rem;
}

.status-box {
  display: grid;
  gap: 0.35rem;
  justify-items: end;
}

.status-box small {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.72);
}

.chips {
  display: inline-flex;
  gap: 0.35rem;
}

.chip {
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  font-size: 0.72rem;
}

.chip.ok {
  background: var(--pos-soft);
  color: var(--pos-primary);
  border: 1px solid var(--pos-border);
}

.chip.warn {
  background: var(--pos-accent-soft);
  color: var(--pos-primary);
  border: 1px solid rgb(var(--pos-accent-rgb, 255 152 54) / 0.35);
}

.dark-input {
  border: 1px solid var(--pos-border);
  background: var(--pos-white);
  color: var(--pos-text);
}

.dark-input::placeholder {
  color: rgb(var(--pos-primary-rgb, 1 90 114) / 0.55);
}

.refresh-btn {
  background: var(--pos-primary);
  color: var(--pos-white);
  border-color: var(--pos-primary);
}

@media (max-width: 1180px) {
  .pos-header {
    grid-template-columns: 1fr 1fr;
  }

  .status-box {
    justify-items: start;
  }
}

@media (max-width: 780px) {
  .pos-header {
    grid-template-columns: 1fr;
  }
}
</style>
