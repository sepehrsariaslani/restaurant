<template>
  <InventorySectionShell :title="isNew ? 'درخواست مواد جدید' : request?.name || 'جزئیات درخواست مواد'" subtitle="ثبت نیاز مواد، بررسی وضعیت و انتقال به خرید">
    <template #actions><button type="button" class="secondary-btn" @click="goBack">بازگشت به لیست</button><button v-if="request && request.docstatus === 0" type="button" class="secondary-btn" @click="edit">ویرایش</button></template>
    <p v-if="error" class="error">{{ error }}</p><p v-if="message" class="success">{{ message }}</p>
    <ManagementSurfaceCard v-if="isNew || editing" title="فرم درخواست مواد" subtitle="واحد ماده بعد از انتخاب، خودکار از ERPNext خوانده می‌شود.">
      <div class="form-grid"><label>تاریخ درخواست<PersianDateInput v-model="form.transaction_date" /></label><label>تاریخ نیاز<PersianDateInput v-model="form.schedule_date" /></label><label>انبار مقصد<select class="input" v-model="form.set_warehouse"><option value="">انتخاب انبار</option><option v-for="warehouse in boot?.leaf_warehouses || []" :key="warehouse" :value="warehouse">{{ warehouse }}</option></select></label><label class="full">یادداشت<textarea class="input" rows="2" v-model.trim="form.note"></textarea></label></div>
      <div class="request-lines"><header><strong>اقلام درخواست</strong><button type="button" class="secondary-btn" @click="addLine">+ افزودن قلم</button></header><div v-for="(line,index) in form.items" :key="index" class="request-line"><SearchableDropdown v-model="line.item_code" :options="materialOptions" placeholder="انتخاب ماده..." search-placeholder="جستجو..." @update:model-value="syncLine(line,$event)" /><input class="input" type="number" min="0.001" step="0.001" v-model.number="line.qty" placeholder="مقدار" /><div class="uom"><small>واحد</small><strong>{{ line.uom || 'خودکار' }}</strong></div><button type="button" class="tertiary-btn danger" @click="removeLine(index)" :disabled="form.items.length===1">حذف</button></div></div>
      <footer class="actions"><button type="button" class="secondary-btn" @click="save(false)" :disabled="saving">ذخیره پیش‌نویس</button><button type="button" class="primary-btn" @click="save(true)" :disabled="saving">{{ saving ? 'در حال ثبت...' : 'ثبت نهایی درخواست' }}</button></footer>
    </ManagementSurfaceCard>

    <template v-else-if="request">
      <ManagementSurfaceCard title="خلاصه درخواست" subtitle="جزئیات ثبت‌شده و مسیر تأمین">
        <div class="detail-meta"><div><small>وضعیت</small><strong :class="statusClass(request.status)">{{ request.status_label }}</strong></div><div><small>تاریخ درخواست</small><strong>{{ request.transaction_date }}</strong></div><div><small>تاریخ نیاز</small><strong>{{ request.schedule_date || '—' }}</strong></div><div><small>انبار مقصد</small><strong>{{ request.set_warehouse || '—' }}</strong></div><div><small>مجموع</small><strong>{{ qty(request.total_qty) }}</strong></div></div>
        <div class="detail-lines"><article v-for="line in request.items" :key="line.idx + line.item_code" class="detail-line"><div><strong>{{ line.item_name }}</strong><small>{{ line.item_code }}</small></div><strong class="line-qty">{{ qty(line.qty) }} {{ line.uom || line.stock_uom }}</strong></article></div>
        <p v-if="request.note" class="note">{{ request.note }}</p>
        <div v-if="purchases.length" class="linked-purchases"><strong>سفارش‌های خرید مرتبط</strong><button v-for="purchase in purchases" :key="purchase.name" type="button" @click="openPurchase(purchase.name)">{{ purchase.name }} • {{ purchase.status }}</button></div>
        <footer class="actions"><button v-if="request.docstatus===0" type="button" class="primary-btn" @click="changeStatus('submit')">ثبت نهایی</button><button v-if="request.docstatus===1" type="button" class="primary-btn" @click="createPurchase" :disabled="purchaseSaving">{{ purchaseSaving ? 'در حال ساخت...' : 'ایجاد پیش‌نویس خرید' }}</button><button v-if="request.docstatus===1" type="button" class="tertiary-btn danger" @click="changeStatus('cancel')">لغو درخواست</button><button type="button" class="secondary-btn" @click="printRequest">چاپ فیش</button></footer>
      </ManagementSurfaceCard>
    </template>
  </InventorySectionShell>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import InventorySectionShell from '@/components/management/inventory/InventorySectionShell.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import PersianDateInput from '@/components/PersianDateInput.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import { createManagementPurchaseFromMaterialRequest, getManagementInventoryBoot, getManagementMaterialRequest, getManagementMaterialRequestPrint, listManagementRawMaterials, saveManagementMaterialRequest, updateManagementMaterialRequestStatus } from '@/utils/api'

const params = new URLSearchParams(window.location.search)
const requestName = params.get('name') || ''
const isNew = params.get('new') === '1' || !requestName
const request = ref(null)
const purchases = ref([])
const boot = ref(null)
const editing = ref(isNew)
const loading = ref(false)
const saving = ref(false)
const purchaseSaving = ref(false)
const error = ref('')
const message = ref('')
const form = reactive({ name: '', transaction_date: today(), schedule_date: today(), set_warehouse: '', note: '', items: [{ item_code: '', qty: 1, uom: '', stock_uom: '', conversion_factor: 1 }] })
const materialOptions = computed(() => (boot.value?.materials || []).map((item) => ({ value: item.name, label: `${item.item_name || item.name} (${item.name})` })))
function today() { return new Date().toISOString().slice(0,10) }
function qty(value) { return Number(value||0).toLocaleString('fa-IR',{maximumFractionDigits:3}) }
function statusClass(status) { return ['ordered','partially ordered'].includes(String(status||'').toLowerCase()) ? 'success' : ['cancelled','stopped'].includes(String(status||'').toLowerCase()) ? 'danger' : 'primary' }
function goBack() { window.location.href='/management/inventory/requests' }
function openPurchase(name) { window.location.href=`/management/inventory/purchases/detail?name=${encodeURIComponent(name)}` }
function addLine() { form.items.push({ item_code:'',qty:1,uom:'',stock_uom:'',conversion_factor:1 }) }
function removeLine(index) { if(form.items.length>1) form.items.splice(index,1) }
function syncLine(line, code=line.item_code) { line.item_code=code; const meta=(boot.value?.materials||[]).find((item)=>item.name===code); if(meta){line.uom=meta.stock_uom||'Nos';line.stock_uom=meta.stock_uom||line.uom;line.conversion_factor=1} }
function applyRequest(value, linked=[]) { request.value=value; purchases.value=linked; editing.value=false; Object.assign(form,{name:value.name,transaction_date:value.transaction_date||today(),schedule_date:value.schedule_date||value.transaction_date||today(),set_warehouse:value.set_warehouse||'',note:value.note||'',items:(value.items||[]).map((line)=>({...line,conversion_factor:Number(line.conversion_factor||1)}))}) }
async function load(){loading.value=true;error.value='';try{const [bootPayload, materialsPayload]=await Promise.all([getManagementInventoryBoot(),listManagementRawMaterials({limit:500, include_all_stock: 1})]);boot.value={...bootPayload,materials:materialsPayload.items||[]};if(!isNew){const payload=await getManagementMaterialRequest(requestName);applyRequest(payload.request,payload.purchase_orders||[])}}catch(err){error.value=err.message||'دریافت درخواست ناموفق بود.'}finally{loading.value=false}}
function edit(){ if(request.value?.docstatus===0){editing.value=true} }
async function save(submit){saving.value=true;error.value='';try{const items=form.items.filter((line)=>line.item_code&&Number(line.qty)>0);if(!items.length)throw new Error('حداقل یک قلم معتبر لازم است.');const result=await saveManagementMaterialRequest({...form,items,submit:submit?1:0});message.value=submit?'درخواست نهایی ثبت شد.':'پیش‌نویس ذخیره شد.';if(isNew){window.location.href=`/management/inventory/requests/detail?name=${encodeURIComponent(result.request.name)}`}else{const payload=await getManagementMaterialRequest(result.request.name);applyRequest(payload.request,payload.purchase_orders||[])}}catch(err){error.value=err.message||'ذخیره درخواست ناموفق بود.'}finally{saving.value=false}}
async function changeStatus(action){try{const result=await updateManagementMaterialRequestStatus({name:request.value.name,action});request.value=result.request;editing.value=false;message.value=action==='submit'?'درخواست ثبت نهایی شد.':'درخواست لغو شد.'}catch(err){error.value=err.message||'تغییر وضعیت ناموفق بود.'}}
async function createPurchase(){purchaseSaving.value=true;error.value='';try{const result=await createManagementPurchaseFromMaterialRequest({name:request.value.name,target_warehouse:request.value.set_warehouse||'',items:request.value.items.map((line)=>({item_code:line.item_code,qty:line.qty,uom:line.uom||line.stock_uom,rate:line.rate||0}))});window.location.href=`/management/inventory/purchases/detail?name=${encodeURIComponent(result.purchase.name)}`}catch(err){error.value=err.message||'ساخت خرید ناموفق بود.'}finally{purchaseSaving.value=false}}
async function printRequest(){try{const payload=await getManagementMaterialRequestPrint(request.value.name);const printWindow=window.open('','_blank','width=420,height=760');if(!printWindow)throw new Error('پنجره چاپ باز نشد.');printWindow.document.write(`<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>${payload.name}</title></head><body>${payload.html}</body></html>`);printWindow.document.close();printWindow.focus();window.setTimeout(()=>printWindow.print(),300)}catch(err){error.value=err.message||'چاپ ناموفق بود.'}}
onMounted(load)
</script>

<style scoped>
.form-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.65rem}.form-grid label{display:grid;gap:.25rem;color:var(--mg-text-main);font-size:.78rem}.full{grid-column:1/-1}.request-lines{display:grid;gap:.55rem;margin-top:1rem;padding:.8rem;border:1px dashed var(--mg-border);border-radius:15px}.request-lines header{display:flex;align-items:center;justify-content:space-between;gap:.5rem}.request-line{display:grid;grid-template-columns:minmax(0,3fr) minmax(90px,1fr) 90px auto;gap:.45rem;align-items:center}.uom{min-height:38px;display:grid;align-content:center;gap:.1rem;padding:.25rem .45rem;border:1px solid var(--mg-border-light);border-radius:9px}.uom small,.detail-line small,.detail-meta small{color:var(--mg-text-muted);font-size:.67rem}.actions{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:.5rem;margin-top:1rem;padding-top:.7rem;border-top:1px solid var(--mg-border-light)}.detail-meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.55rem}.detail-meta>div{display:grid;gap:.18rem;padding:.6rem;border-radius:12px;background:var(--mg-bg-page)}.detail-meta strong{font-size:.8rem}.success{color:var(--mg-success)}.danger,.error{color:var(--mg-danger)}.primary{color:var(--mg-primary)}.detail-lines{display:grid;gap:.45rem;margin-top:1rem}.detail-line{display:flex;justify-content:space-between;align-items:center;gap:.6rem;padding:.65rem .7rem;border:1px solid var(--mg-border-light);border-radius:12px}.detail-line>div{min-width:0;display:grid;gap:.1rem}.detail-line strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.detail-line small{display:block}.line-qty{color:var(--mg-success);white-space:nowrap}.note,.linked-purchases{margin-top:.8rem;padding:.65rem;border-radius:12px;background:var(--mg-bg-page);white-space:pre-line}.linked-purchases{display:grid;gap:.35rem}.linked-purchases button{width:fit-content;border:0;background:transparent;color:var(--mg-primary);font:inherit;cursor:pointer}@media(max-width:650px){.request-line{grid-template-columns:1fr 1fr}.request-line .uom,.request-line .tertiary-btn{min-height:38px}.request-line :deep(.search-dropdown){grid-column:1/-1}.actions>*{flex:1 1 100%}.detail-meta{grid-template-columns:1fr 1fr}}@media(max-width:390px){.detail-meta{grid-template-columns:1fr}}
</style>
