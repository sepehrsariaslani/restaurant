<template>
  <div class="customer-page" dir="rtl">
    <CustomerPageHeader eyebrow="حساب من" title="خودروهای من" subtitle="برای تحویل درب ماشین، مشخصات خودرو را یک بار ذخیره کنید." fallback-href="/customer/dashboard" />
    <main class="customer-page__body">
      <section class="customer-glass-card vehicle-account-card">
        <CustomerVehiclePicker :key="reloadKey" v-model="vehicle" :mobile="mobile" :customer-name="customerName" signed-in />
        <p v-if="error" class="vehicle-error" role="alert">{{ error }}</p>
        <p v-if="message" role="status">{{ message }}</p>
        <div class="vehicle-account-actions">
          <button type="button" class="order-flow-primary" :disabled="!vehicleComplete(vehicle) || saving" @click="save">{{ saving ? 'در حال ذخیره…' : 'ذخیره خودرو' }}</button>
          <button v-if="vehicleComplete(vehicle)" type="button" class="order-flow-secondary" @click="orderWithVehicle">سفارش درب ماشین</button>
        </div>
      </section>
    </main>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import CustomerVehiclePicker from '@/components/customer/CustomerVehiclePicker.vue'
import { saveCustomerVehicle } from '@/utils/api'
import { vehicleComplete } from '@/utils/customerOrderValidation'
import { saveOrderContext } from '@/stores/cartStore'
import './orderFlow.css'
let auth = {}
try { auth = JSON.parse(localStorage.getItem('restaurant-customer-auth-v1') || '{}') } catch {}
const mobile = auth.mobile || '', customerName = auth.customer_name || localStorage.getItem('customer_name') || 'مشتری'
const vehicle = ref({}), saving = ref(false), error = ref(''), message = ref(''), reloadKey = ref(0)
async function save() {
  if (!vehicleComplete(vehicle.value) || saving.value) return
  saving.value = true; error.value = ''; message.value = ''
  try {
    const result = await saveCustomerVehicle({ customer_info: { name: customerName, mobile }, vehicle_info: vehicle.value })
    if (!result?.vehicle?.id) throw new Error('خودرو ذخیره نشد؛ دوباره تلاش کنید.')
    vehicle.value = result.vehicle; reloadKey.value++; message.value = 'خودرو در حساب شما ذخیره شد.'
  } catch (err) { error.value = err.message || 'ذخیره خودرو انجام نشد.' }
  finally { saving.value = false }
}
function orderWithVehicle() { saveOrderContext({ order_type: 'pickup', pickup_method: 'car', pickup_vehicle: { ...vehicle.value }, delivery_fee: 0, address: null }); window.location.href = '/order/pickup?method=car' }
onMounted(() => { if (!mobile) window.location.replace('/customer/login?redirect=%2Fcustomer%2Fvehicles') })
</script>
<style scoped>
.vehicle-account-card { padding: 1.25rem; max-width: 640px; margin-inline: auto; }
.vehicle-account-actions { display: flex; gap: .7rem; flex-wrap: wrap; margin-top: 1.5rem; }
.vehicle-error { color: var(--ds-color-status-danger); }
</style>
