<template>
  <ManagementPageScaffold title="مرکز تماس و کالر آیدی" subtitle="پاپ‌آپ مشخصات مشتری هنگام تماس، پیشنهاد نزدیک‌ترین شعبه و ثبت سفارش توسط اپراتور">
    <template #actions>
      <button type="button" class="secondary-btn" @click="reload">{{ loading ? '...' : 'بروزرسانی' }}</button>
    </template>

    <div class="totals-grid" v-if="boot.counts">
      <div class="total-box" :class="{ 'warn-border': (boot.counts['جدید'] || 0) > 0 }"><small>تماس‌های جدید</small><strong :class="{ 'warn-text': (boot.counts['جدید'] || 0) > 0 }">{{ formatQty(boot.counts['جدید'] || 0) }}</strong></div>
      <div class="total-box"><small>در حال پاسخ</small><strong>{{ formatQty(boot.counts['در حال پاسخ'] || 0) }}</strong></div>
      <div class="total-box"><small>پاسخ‌داده‌شده</small><strong>{{ formatQty(boot.counts['پاسخ‌داده‌شده'] || 0) }}</strong></div>
    </div>

    <ManagementSurfaceCard title="اتصال به تلفن (VOIP / کالر آیدی)" subtitle="آدرس وب‌هوک برای نمایش پاپ‌آپ و باز شدن خودکار پروفایل مشتری هنگام زنگ">
      <div class="webhook-box">
        <p class="muted">سیستم تلفنی (استریسک/ویپ) را طوری تنظیم کنید که هنگام تماس ورودی این آدرس را فراخوانی کند:</p>
        <code class="link-code">{{ boot.webhook_url }}?mobile=CALLER_NUMBER&amp;token=TOKEN&amp;exten=EXTEN</code>
        <p class="muted">
          وضعیت توکن امنیتی: <span class="pill" :class="{ ok: boot.token_set, warn: !boot.token_set }">{{ boot.token_set ? 'تنظیم شده' : 'تنظیم نشده (بدون توکن پذیرفته می‌شود)' }}</span>
          <span class="pill" :class="{ ok: boot.enabled, warn: !boot.enabled }">{{ boot.enabled ? 'مرکز تماس فعال' : 'غیرفعال' }}</span>
        </p>
        <p class="muted">نمایش شماره‌های موازی: هر تماس با داخلی (exten) خودش ثبت می‌شود و این صفحه هر ۱۵ ثانیه به‌روز می‌شود.</p>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="تماس‌های اخیر" subtitle="با «پاسخ» تماس را می‌گیرید؛ پروفایل مشتری از باشگاه باز می‌شود">
      <p class="muted" v-if="loadingCalls">در حال دریافت تماس‌ها...</p>
      <p class="error" v-if="error">{{ error }}</p>
      <p class="success-msg" v-if="message">{{ message }}</p>
      <div v-if="!loadingCalls && calls.length" class="table-wrap">
        <table class="data-table">
          <thead><tr><th>شماره</th><th>مشتری</th><th>داخلی</th><th>زمان</th><th>وضعیت</th><th>اپراتور</th><th></th></tr></thead>
          <tbody>
            <tr v-for="c in calls" :key="c.name" :class="{ 'row-new': c.status === 'جدید' }">
              <td><strong>{{ c.caller_mobile }}</strong></td>
              <td>{{ c.customer_name || 'مهمان جدید' }}</td>
              <td>{{ c.exten || '—' }}</td>
              <td><small class="muted">{{ c.entry_date }}</small></td>
              <td><span class="pill" :class="{ warn: c.status === 'جدید', ok: c.status === 'پاسخ‌داده‌شده' }">{{ c.status }}</span></td>
              <td><small class="muted">{{ c.agent || '—' }}</small></td>
              <td class="row-actions">
                <button type="button" class="secondary-btn" @click="answerCall(c)">پاسخ</button>
                <button type="button" class="tertiary-btn" @click="closeCall(c)">پایان</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted" v-else-if="!loadingCalls">تماسی ثبت نشده است.</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="جستجوی دستی مشتری" subtitle="ثبت سفارش در مرکز تماس — پروفایل کامل باشگاه مشتریان با موبایل">
      <div class="toolbar">
        <input class="input" v-model.trim="searchMobile" placeholder="شماره موبایل..." inputmode="tel" @keyup.enter="lookupCustomer(searchMobile)" />
        <button type="button" class="primary-btn" @click="lookupCustomer(searchMobile)" :disabled="profileLoading">{{ profileLoading ? '...' : 'جستجو' }}</button>
      </div>

      <div v-if="profile" class="profile-box">
        <template v-if="profile.found">
          <div class="profile-head">
            <div>
              <h3>{{ profile.customer_name }} <small class="muted">{{ profile.mobile }}</small></h3>
              <span v-if="profile.tier" class="pill" :class="{ ok: profile.tier === 'VIP' }">{{ profile.tier }}</span>
              <span v-if="profile.segment" class="pill">{{ profile.segment }}</span>
              <span v-if="profile.alerts?.is_vip" class="pill ok">⭐ VIP</span>
              <span v-if="profile.alerts?.dissatisfied" class="pill warn">⚠️ ناراضی اخیر</span>
              <span v-if="profile.alerts?.debtor_amount" class="pill warn">💳 بدهکار: {{ formatMoneyValue(profile.alerts.debtor_amount) }}</span>
            </div>
            <div class="profile-actions">
              <a class="primary-btn" href="/management/pos" target="_blank" rel="noopener">ثبت سفارش (صندوق)</a>
              <button type="button" class="secondary-btn" @click="openNoteForm">یادداشت به صندوق</button>
            </div>
          </div>
          <div class="totals-grid">
            <div class="total-box"><small>تعداد سفارش</small><strong>{{ formatQty(profile.stats?.orders_count) }}</strong></div>
            <div class="total-box"><small>مجموع خرید</small><strong>{{ formatMoneyValue(profile.stats?.total_spent) }}</strong></div>
            <div class="total-box"><small>میانگین سبد</small><strong>{{ formatMoneyValue(profile.stats?.avg_order) }}</strong></div>
            <div class="total-box"><small>آخرین سفارش</small><strong>{{ profile.stats?.last_order || '—' }}</strong></div>
            <div class="total-box"><small>کیف پول</small><strong>{{ formatMoneyValue(profile.wallet_balance) }}</strong></div>
            <div class="total-box" v-if="profile.suggested_branch"><small>شعبه پیشنهادی (نزدیک‌ترین فعال)</small><strong>{{ profile.suggested_branch }}</strong></div>
          </div>
          <div class="profile-cols">
            <div>
              <h4>آدرس‌ها</h4>
              <ul class="mini-list">
                <li v-for="(a, i) in profile.addresses || []" :key="i">{{ a.title || a.address_line || a }} <small class="muted" v-if="a.plaque">پلاک {{ a.plaque }}</small></li>
                <li v-if="!(profile.addresses || []).length" class="muted">آدرسی ثبت نشده.</li>
              </ul>
            </div>
            <div>
              <h4>سفارش‌های اخیر</h4>
              <ul class="mini-list">
                <li v-for="o in (profile.orders || []).slice(0, 8)" :key="o.name">{{ o.name }} — {{ formatMoneyValue(o.grand_total) }} <span class="pill">{{ o.status }}</span></li>
                <li v-if="!(profile.orders || []).length" class="muted">سفارشی ثبت نشده.</li>
              </ul>
              <p class="muted" v-if="profile.membership_code">کد اشتراک: {{ profile.membership_code }} · کد معرف: {{ profile.referral_code || '—' }}</p>
            </div>
          </div>
        </template>
        <p v-else class="muted">مشتری‌ای با این شماره یافت نشد — در هنگام ثبت سفارش، مشتری جدید به‌صورت خودکار ساخته می‌شود.</p>
      </div>
    </ManagementSurfaceCard>

    <div v-if="noteForm" class="popup-backdrop" @click.self="noteForm = null">
      <div class="popup">
        <h3>یادداشت به صندوق</h3>
        <div class="form-grid">
          <label>کد سفارش (اختیاری)<input class="input" v-model.trim="noteForm.order_name" placeholder="SO-..." /></label>
          <label>شعبه مقصد<input class="input" v-model.trim="noteForm.branch" :placeholder="profile?.suggested_branch || '—'" /></label>
          <label class="full-row">متن یادداشت <span class="req">*</span><textarea class="input" rows="3" v-model="noteForm.note" placeholder="مثلاً مشتری تماس گرفت؛ سفارش بدون پیاز باشد."></textarea></label>
        </div>
        <p class="error" v-if="noteError">{{ noteError }}</p>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="sendNote" :disabled="noteBusy">{{ noteBusy ? '...' : 'ارسال یادداشت' }}</button>
          <button type="button" class="tertiary-btn" @click="noteForm = null">انصراف</button>
        </div>
      </div>
    </div>
  </ManagementPageScaffold>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  getManagementCallCenterBoot,
  listManagementCallLogs,
  claimManagementCallLog,
  resolveManagementCallLog,
  getCallCenterCustomer,
  sendCallCenterNote,
} from '@/utils/api'
import { formatMoney as formatMoneyUtil } from '@/utils/format'

const boot = ref({ counts: {}, statuses: [], webhook_url: '', token_set: false, enabled: true })
const calls = ref([])
const loading = ref(false)
const loadingCalls = ref(false)
const error = ref('')
const message = ref('')
const searchMobile = ref('')
const profile = ref(null)
const profileLoading = ref(false)
const noteForm = ref(null)
const noteError = ref('')
const noteBusy = ref(false)
let pollTimer = null

function formatQty(v) { return Number(v || 0).toLocaleString('fa-IR') }
function formatMoneyValue(v) { return formatMoneyUtil(Number(v || 0)) }

async function reload() {
  loading.value = true
  await Promise.all([loadCalls(), loadBoot()])
  loading.value = false
}
async function loadBoot() {
  try { boot.value = await getManagementCallCenterBoot() } catch (err) { /* ignore */ }
}
async function loadCalls() {
  loadingCalls.value = true
  try {
    const payload = await listManagementCallLogs({ limit: 30 })
    calls.value = payload.calls || []
  } catch (err) {
    error.value = err.message || 'دریافت تماس‌ها ناموفق بود.'
  } finally { loadingCalls.value = false }
}

async function answerCall(c) {
  try {
    await claimManagementCallLog(c.name)
    await Promise.all([loadCalls(), loadBoot()])
    await lookupCustomer(c.caller_mobile)
  } catch (err) { error.value = err.message || '' }
}
async function closeCall(c) {
  try {
    await resolveManagementCallLog({ name: c.name })
    await Promise.all([loadCalls(), loadBoot()])
  } catch (err) { error.value = err.message || '' }
}

async function lookupCustomer(mobile) {
  if (!mobile) return
  profileLoading.value = true
  try {
    profile.value = await getCallCenterCustomer(mobile)
  } catch (err) {
    profile.value = null
    error.value = err.message || 'دریافت پروفایل ناموفق بود.'
  } finally { profileLoading.value = false }
}

function openNoteForm() {
  noteError.value = ''
  noteForm.value = { note: '', order_name: '', branch: profile.value?.suggested_branch || '' }
}
async function sendNote() {
  if (!noteForm.value) return
  noteBusy.value = true
  noteError.value = ''
  try {
    const payload = await sendCallCenterNote({ ...noteForm.value })
    noteForm.value = null
    message.value = `یادداشت برای ${formatQty(payload.notified)} کاربر صندوق ارسال شد.`
  } catch (err) {
    noteError.value = err.message || 'ارسال یادداشت ناموفق بود.'
  } finally { noteBusy.value = false }
}

onMounted(async () => {
  await reload()
  pollTimer = setInterval(async () => { await Promise.all([loadCalls(), loadBoot()]) }, 15000)
})
onBeforeUnmount(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<style scoped>
.toolbar { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; margin-bottom: 0.75rem; }
.toolbar .input { min-width: 180px; }
.webhook-box { display: grid; gap: 0.5rem; }
.link-code { direction: ltr; display: inline-block; background: rgba(90, 74, 58, 0.08); border-radius: 8px; padding: 0.45rem 0.7rem; font-size: 0.78rem; word-break: break-all; }
.row-new { background: rgba(164, 68, 55, 0.05); }
.warn-border { border-color: rgba(164, 68, 55, 0.4); }
.profile-box { border: 1px solid rgba(90, 74, 58, 0.15); border-radius: 14px; padding: 0.9rem; display: grid; gap: 0.8rem; }
.profile-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.8rem; flex-wrap: wrap; }
.profile-head h3 { margin: 0 0 0.3rem; }
.profile-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.primary-btn { text-decoration: none; display: inline-block; }
.profile-cols { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; }
.profile-cols h4 { margin: 0 0 0.4rem; font-size: 0.9rem; }
.mini-list { margin: 0; padding-inline-start: 1rem; display: grid; gap: 0.3rem; font-size: 0.82rem; }
.row-actions { white-space: nowrap; display: flex; gap: 0.3rem; flex-wrap: wrap; }
.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.65rem; margin-bottom: 0.7rem; }
.form-grid label { display: grid; gap: 0.3rem; font-size: 0.86rem; }
.full-row { grid-column: 1 / -1; }
</style>
