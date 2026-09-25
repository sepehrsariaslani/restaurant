<template>
  <section class="vehicle-picker" aria-label="مشخصات خودرو">
    <div v-if="loading" role="status" class="vehicle-hint">در حال دریافت خودروهای شما…</div>
    <p v-if="error" class="vehicle-error" role="alert">{{ error }} <button type="button" @click="loadVehicles">تلاش دوباره</button></p>
    <div v-if="vehicles.length" class="vehicle-options" role="group" aria-label="خودروهای ذخیره‌شده">
      <button v-for="vehicle in vehicles" :key="vehicle.id" type="button" :class="{ active: modelValue.id === vehicle.id }" :aria-pressed="modelValue.id === vehicle.id" @click="selectVehicle(vehicle)">
        <CarFront :size="22" aria-hidden="true" /><span><strong>{{ vehicle.type }} · {{ vehicle.color }}</strong><small>پلاک {{ vehicle.plate }}</small></span><Check v-if="modelValue.id === vehicle.id" :size="18" />
      </button>
      <button type="button" :class="{ active: !modelValue.id }" @click="selectVehicle({})"><Plus :size="20" />خودروی دیگر</button>
    </div>
    <button v-if="modelValue.id && !editing" class="vehicle-edit" type="button" @click="editing = true">ویرایش مشخصات این خودرو</button>
    <div v-if="!modelValue.id || editing" class="vehicle-fields">
      <label class="order-flow-field"><span>مدل خودرو</span><input class="order-flow-input" :value="modelValue.type" @input="update('type', $event.target.value)" placeholder="مثلاً پژو ۲۰۷" autocomplete="off" /></label>
      <label class="order-flow-field"><span>رنگ خودرو</span><input class="order-flow-input" :value="modelValue.color" @input="update('color', $event.target.value)" placeholder="مثلاً سفید" autocomplete="off" /></label>
      <label class="order-flow-field vehicle-plate"><span>پلاک خودرو</span><input class="order-flow-input" :value="modelValue.plate" @input="update('plate', $event.target.value)" placeholder="مثلاً ۱۲ ب ۳۴۵ ایران ۶۷" autocomplete="off" /></label>
    </div>
    <p class="vehicle-hint"><Phone :size="16" aria-hidden="true" /> هنگام رسیدن نزدیک شعبه، از شماره تماس روی سفارش با شما هماهنگ می‌کنیم.</p>
    <label v-if="signedIn && !modelValue.id" class="vehicle-save"><input type="checkbox" :checked="modelValue.save_for_future" @change="update('save_for_future', $event.target.checked)" />ذخیره این خودرو برای سفارش‌های بعدی</label>
  </section>
</template>
<script setup>
import { onMounted, ref, watch } from 'vue'
import { CarFront, Check, Phone, Plus } from 'lucide-vue-next'
import { getCustomerVehicles } from '@/utils/api'
const props = defineProps({ modelValue: { type: Object, default: () => ({}) }, mobile: { type: String, default: '' }, customerName: { type: String, default: '' }, signedIn: Boolean })
const emit = defineEmits(['update:modelValue'])
const editing = ref(false)
const vehicles = ref([]), loading = ref(false), error = ref('')
let requestId = 0
function update(key, value) { emit('update:modelValue', { ...props.modelValue, [key]: value }) }
function selectVehicle(vehicle) { editing.value = false; emit('update:modelValue', { id: '', type: '', color: '', plate: '', save_for_future: false, ...vehicle }) }
async function loadVehicles() {
  const id = ++requestId
  vehicles.value = []; error.value = ''; loading.value = false
  if (!props.signedIn || !props.mobile) return
  loading.value = true
  try { const data = await getCustomerVehicles({ mobile: props.mobile, customer_name: props.customerName }); if (id === requestId) vehicles.value = data?.vehicles || [] }
  catch (err) { if (id === requestId) error.value = err.message || 'دریافت خودروها انجام نشد.' }
  finally { if (id === requestId) loading.value = false }
}
watch(() => [props.mobile, props.signedIn], loadVehicles)
onMounted(loadVehicles)
</script>
<style scoped>
.vehicle-edit { min-height: 44px; font: inherit; color: var(--ds-color-action-primary); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-sm); background: var(--ds-color-surface-raised); cursor: pointer; }
.vehicle-picker { display: grid; gap: 1rem; }
.vehicle-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .85rem; }
.vehicle-plate { grid-column: 1 / -1; }
.vehicle-options { display: grid; gap: .65rem; }
.vehicle-options button { min-height: 56px; display: flex; align-items: center; gap: .7rem; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); color: var(--ds-color-text-primary); font: inherit; text-align: start; cursor: pointer; }
.vehicle-options button.active { border-color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); }
.vehicle-options span { display: grid; gap: .25rem; flex: 1; }
.vehicle-options small, .vehicle-hint { color: var(--ds-color-text-muted); }
.vehicle-hint { margin: 0; display: flex; gap: .4rem; font-size: .82rem; line-height: 1.8; align-items: center; }
.vehicle-hint svg { flex-shrink: 0; }
.vehicle-save { display: flex; align-items: center; gap: .5rem; min-height: 44px; font-size: .9rem; }
.vehicle-save input { width: 20px; height: 20px; }
.vehicle-error { color: var(--ds-color-status-danger); }
.vehicle-error button { min-height: 44px; font: inherit; background: transparent; border: 0; color: inherit; text-decoration: underline; }
</style>
