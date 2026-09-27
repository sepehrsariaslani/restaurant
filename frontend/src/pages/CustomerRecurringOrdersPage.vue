<template>
  <div class="recurring-page customer-page" dir="rtl">
    <CustomerPageHeader eyebrow="برنامه غذایی شما" :title="nutritionScheduleSource ? 'زمان‌بندی برنامهٔ غذایی' : 'سفارش‌های تکرارشونده'" :subtitle="nutritionScheduleSource ? `برنامهٔ «${nutritionPlanTitle}» را برای روزها و ساعت دلخواه تکرار کنید؛ موجودی و قیمت هر نوبت دوباره بررسی می‌شود.` : 'یک سبد را برای روزهای بعد برنامه‌ریزی کنید؛ هر سفارش طبق روش تسویه‌ای که انتخاب می‌کنید پیش می‌رود.'" hero-class="recurring-hero" fallback-href="/customer/dashboard">
      <template #eyebrow-icon><CalendarDays :size="15" aria-hidden="true" /></template>
    </CustomerPageHeader>

    <main class="recurring-body">
      <section v-if="!signedIn" class="recurring-card sign-in-card">
        <UserRound :size="30" aria-hidden="true" /><h2>برای دیدن برنامه‌ها وارد حساب شوید</h2><p>سبد فعلی شما پس از ورود در همین مرورگر باقی می‌ماند.</p><a class="recurring-primary" href="/customer/login?redirect=%2Fcustomer%2Frecurring-orders">ورود به حساب</a>
      </section>

      <template v-else>
        <section v-if="cartState.lines.length" class="recurring-card recurring-builder">
          <div class="recurring-card-heading"><span class="recurring-icon"><ShoppingBag :size="19" /></span><div><h2>{{ nutritionScheduleSource ? `زمان‌بندی «${nutritionPlanTitle}»` : 'تکرار سبد فعلی' }}</h2><p>{{ cartState.lines.length.toLocaleString('fa-IR') }} قلم ذخیره می‌شود؛ قیمت و موجودی در هر نوبت دوباره بررسی می‌شود.</p></div></div>
          <div class="recurring-mini-items"><span v-for="line in cartState.lines.slice(0, 3)" :key="line.id">{{ line.item_title }} <b>× {{ Number(line.qty).toLocaleString('fa-IR') }}</b></span><small v-if="cartState.lines.length > 3">و {{ (cartState.lines.length - 3).toLocaleString('fa-IR') }} قلم دیگر</small></div>
          <p v-if="!cartState.orderContext?.order_type" class="recurring-alert" role="alert">برای ثبت برنامه، ابتدا روش دریافت سفارش را انتخاب کنید. <a href="/order/type">انتخاب روش دریافت</a></p>
          <form class="recurring-form" @submit.prevent="createSchedule">
            <div class="recurring-fields">
              <label><span>هر چند وقت؟</span><select v-model="form.frequency" class="input"><option value="یک‌بار">فقط یک‌بار</option><option>روزانه</option><option>هفتگی</option><option>ماهانه</option></select></label>
              <label><span>شروع از</span><input v-model="form.start_date" class="input" type="date" :min="today" required /></label>
              <label><span>ساعت دریافت</span><input v-model="form.delivery_time" class="input" type="time" required /></label>
              <label v-if="form.frequency !== 'یک‌بار'"><span>پایان برنامه <small>اختیاری</small></span><input v-model="form.end_date" class="input" type="date" :min="form.start_date || today" /></label>
            </div>
            <fieldset v-if="form.frequency === 'هفتگی'" class="recurring-weekdays"><legend>روزهای تکرار را انتخاب کنید</legend><label v-for="day in weekdays" :key="day" class="recurring-day" :class="{ active: form.weekdays.includes(day) }"><input v-model="form.weekdays" type="checkbox" :value="day" /><span>{{ day }}</span></label></fieldset>
            <p v-if="form.frequency === 'یک‌بار'" class="recurring-muted">در تاریخ انتخاب‌شده یک سفارش ساخته می‌شود و نوبت دیگری تکرار نخواهد شد.</p>
            <div class="settlement-choice">
              <label class="settlement-option" :class="{ selected: form.settlement_mode === 'تأیید هر نوبت' }"><input v-model="form.settlement_mode" type="radio" value="تأیید هر نوبت" /><span><strong>تأیید و پرداخت هر نوبت</strong><small>در موعد، سفارش برای بررسی شما آماده می‌شود؛ بعد از تأیید، از مسیر عادی پرداخت می‌کنید.</small></span></label>
              <label class="settlement-option" :class="{ selected: form.settlement_mode === 'فاکتور ماهانه سازمان', unavailable: !monthlyBillingAvailable }"><input v-model="form.settlement_mode" type="radio" value="فاکتور ماهانه سازمان" :disabled="!monthlyBillingAvailable" /><span><strong>تسویه در فاکتور ماهانهٔ سازمان</strong><small>{{ monthlyBillingAvailable ? 'سفارش در موعد به قرارداد فعال متصل می‌شود و در تسویهٔ تجمیعی می‌آید.' : 'برای این گزینه قرارداد فعال سازمانی با فاکتور ماهانه لازم است.' }}</small></span></label>
            </div>
            <label class="recurring-note"><span>یادداشت برای هر سفارش <small>اختیاری</small></span><textarea v-model.trim="form.note" class="input" rows="2" maxlength="500" placeholder="مثلاً تحویل به پذیرش یا بدون سس" /></label>
            <p v-if="createError" class="recurring-alert" role="alert">{{ createError }}</p>
            <p v-if="createMessage" class="recurring-success" role="status">{{ createMessage }}</p>
            <button class="recurring-primary" type="submit" :disabled="creating || !canCreate">{{ creating ? 'در حال ذخیره برنامه…' : 'ذخیره برنامهٔ تکرار' }}<CalendarCheck :size="18" /></button>
          </form>
        </section>
        <section v-else class="recurring-card no-cart-card"><ShoppingBag :size="27" /><h2>برای ساخت برنامه، اول یک سبد آماده کنید</h2><p>غذاها را انتخاب کنید و شعبه و روش دریافت را مشخص کنید؛ بعد از سبد، «تنظیم تکرار همین سفارش» را بزنید.</p><a class="recurring-primary" href="/menu">رفتن به منو</a></section>

        <section class="recurring-card">
          <div class="recurring-card-heading"><span class="recurring-icon"><CalendarClock :size="19" /></span><div><h2>برنامه‌های شما</h2><p>می‌توانید هر برنامه را هر زمان متوقف یا دوباره فعال کنید.</p></div><button class="recurring-refresh" type="button" :disabled="loading" @click="load">{{ loading ? '…' : 'بروزرسانی' }}</button></div>
          <p v-if="loadError" class="recurring-alert" role="alert">{{ loadError }}</p>
          <p v-else-if="loading" class="recurring-muted" role="status">در حال دریافت برنامه‌ها…</p>
          <div v-else-if="!schedules.length" class="recurring-empty">هنوز برنامهٔ تکراری ثبت نکرده‌اید.</div>
          <div v-else class="schedule-list">
            <article v-for="schedule in schedules" :key="schedule.name" class="schedule-card">
              <div class="schedule-card__top"><div><span class="schedule-frequency">{{ scheduleFrequencyLabel(schedule) }}<template v-if="schedule.weekdays?.length"> · {{ schedule.weekdays.join('، ') }}</template></span><strong>{{ schedule.delivery_time }} · {{ schedule.branch }}</strong></div><span class="schedule-status" :class="statusClass(schedule.status)">{{ schedule.status }}</span></div>
              <p>{{ schedule.items.length.toLocaleString('fa-IR') }} قلم · {{ schedule.settlement_mode }}</p>
              <p v-if="schedule.status === 'فعال'">نوبت بعدی: <strong>{{ formatDateTime(schedule.next_run_at) }}</strong></p>
              <p v-if="schedule.status === 'منتظر تأیید مشتری'" class="due-reminder">اقلام برنامه‌ریزی‌شده برای {{ formatDate(schedule.pending_date) }} آمادهٔ بررسی شماست. سفارش نهایی بعد از تسویهٔ عادی ثبت می‌شود.</p>
              <label v-if="schedule.status === 'منتظر تأیید مشتری'" class="recurring-branch-picker"><span>شعبهٔ این نوبت</span><select class="input" :value="approvalBranch(schedule)" @change="approvalBranchesByName[schedule.name] = $event.target.value"><option v-for="branch in approvalOptions(schedule)" :key="branch.id || branch.name" :value="branch.id || branch.name">{{ branch.title || branch.name }}</option></select></label>
              <p v-if="schedule.last_error" class="recurring-alert">{{ schedule.last_error }}</p>
              <div class="schedule-actions">
                <button v-if="schedule.status === 'منتظر تأیید مشتری'" type="button" class="recurring-primary recurring-primary--small" :disabled="busySchedule === schedule.name" @click="placeSchedule(schedule)">{{ busySchedule === schedule.name ? 'در حال بررسی و آماده‌سازی سبد…' : 'تأیید و افزودن به سبد' }}<ArrowLeft :size="16" /></button>
                <button v-if="schedule.status === 'منتظر تأیید مشتری'" type="button" class="recurring-secondary" :disabled="busySchedule === schedule.name" @click="skipSchedule(schedule)">ردکردن این نوبت</button>
                <button v-if="['فعال', 'متوقف'].includes(schedule.status)" type="button" class="recurring-secondary" :disabled="busySchedule === schedule.name" @click="toggleSchedule(schedule)"><component :is="schedule.status === 'فعال' ? CirclePause : CirclePlay" :size="16" />{{ schedule.status === 'فعال' ? 'توقف برنامه' : 'ادامه برنامه' }}</button>
                <span v-if="schedule.last_order" class="last-order">آخرین سفارش: {{ schedule.last_order }}</span>
              </div>
              <p v-if="rowErrors[schedule.name]" class="recurring-alert" role="alert">{{ rowErrors[schedule.name] }}</p>
            </article>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowLeft, CalendarCheck, CalendarClock, CalendarDays, CirclePause, CirclePlay, ShoppingBag, UserRound } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import { cartState, clearCart, saveOrderContext, upsertLine } from '@/stores/cartStore'
import { createMyRecurringOrder, getBranches, listMyRecurringOrders, pauseMyRecurringOrder, placeMyRecurringOrder, skipMyRecurringOrder } from '@/utils/api'
import { hasCustomerSession } from '@/utils/customerAuth'
import { isCustomerCompany } from '@/utils/orderBranches'

const weekdays = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
const localDate = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
const today = localDate(new Date())
const recurringQuery = new URLSearchParams(window.location.search)
const nutritionScheduleSource = recurringQuery.get('source') === 'nutrition'
const nutritionPlanTitle = String(recurringQuery.get('title') || 'برنامهٔ ذخیره‌شده').slice(0, 120)
const suggestedWeekdays = String(recurringQuery.get('weekdays') || '').split('|').filter((day) => weekdays.includes(day))
const signedIn = ref(hasCustomerSession())
const form = reactive({ frequency: suggestedWeekdays.length ? 'هفتگی' : 'روزانه', weekdays: suggestedWeekdays, settlement_mode: 'تأیید هر نوبت', start_date: today, end_date: '', delivery_time: '12:00', note: '' })
const schedules = ref([])
const branches = ref([])
const approvalBranchesByName = reactive({})
const monthlyBillingAvailable = ref(false)
const loading = ref(false)
const creating = ref(false)
const loadError = ref('')
const createError = ref('')
const createMessage = ref('')
const busySchedule = ref('')
const rowErrors = reactive({})
const canCreate = computed(() => cartState.lines.length && cartState.orderContext?.branch && cartState.orderContext?.order_type && form.start_date && form.delivery_time && (form.frequency !== 'هفتگی' || form.weekdays.length))

function statusClass(status) { return status === 'فعال' ? 'active' : status === 'منتظر تأیید مشتری' ? 'pending' : status === 'نیازمند بررسی' ? 'problem' : 'paused' }
function scheduleFrequencyLabel(schedule) { return schedule.frequency === 'روزانه' && schedule.start_date && schedule.end_date === schedule.start_date ? 'فقط یک‌بار' : schedule.frequency }
function approvalBranch(schedule) { return approvalBranchesByName[schedule.name] || schedule.branch }
function approvalOptions(schedule) {
  const options = [...branches.value]
  if (!options.some((branch) => (branch.id || branch.name) === schedule.branch)) options.unshift({ id: schedule.branch, name: schedule.branch, title: schedule.branch })
  return options
}
function formatDate(value) { if (!value) return '—'; const date = new Date(`${String(value).slice(0, 10)}T12:00:00`); return date.toLocaleDateString('fa-IR') }
function formatDateTime(value) { if (!value) return '—'; const date = new Date(String(value).replace(' ', 'T')); return `${date.toLocaleDateString('fa-IR')} · ${date.toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}` }

async function load() {
  if (!signedIn.value) return
  loading.value = true
  loadError.value = ''
  try {
    const [payload, branchPayload] = await Promise.all([listMyRecurringOrders(), getBranches()])
    schedules.value = payload?.schedules || []
    branches.value = (branchPayload?.branches || []).filter(isCustomerCompany)
    for (const schedule of schedules.value) approvalBranchesByName[schedule.name] ||= schedule.branch
    monthlyBillingAvailable.value = Boolean(payload?.monthly_billing_available)
  } catch (error) { loadError.value = error?.message || 'دریافت برنامه‌ها انجام نشد.' }
  finally { loading.value = false }
}

async function createSchedule() {
  if (!canCreate.value || creating.value) return
  creating.value = true
  createError.value = ''
  createMessage.value = ''
  try {
    const payload = await createMyRecurringOrder({
      ...form,
      frequency: form.frequency === 'یک‌بار' ? 'روزانه' : form.frequency,
      weekdays: form.frequency === 'یک‌بار' ? [] : form.weekdays,
      end_date: form.frequency === 'یک‌بار' ? form.start_date : form.end_date,
      items: cartState.lines.map((line) => ({ item_slug: line.item_slug, item_title: line.item_title, qty: line.qty, customization: line.customization, note: line.note || '' })),
      context: JSON.parse(JSON.stringify(cartState.orderContext)),
    })
    if (payload?.schedule) schedules.value = [payload.schedule, ...schedules.value]
    createMessage.value = form.frequency === 'یک‌بار'
      ? `سفارش برای ${formatDate(form.start_date)} در ساعت ${form.delivery_time} زمان‌بندی شد؛ پیش از آماده‌سازی، موجودی و قیمت دوباره بررسی می‌شود.`
      : 'برنامه ذخیره شد. پیش از هر نوبت، موجودی و قیمت دوباره بررسی می‌شود.'
    await load()
  } catch (error) { createError.value = error?.message || 'ذخیره برنامه انجام نشد.' }
  finally { creating.value = false }
}

async function toggleSchedule(schedule) {
  busySchedule.value = schedule.name
  rowErrors[schedule.name] = ''
  try {
    const payload = await pauseMyRecurringOrder(schedule.name)
    const index = schedules.value.findIndex((item) => item.name === schedule.name)
    if (index >= 0 && payload?.schedule) schedules.value[index] = payload.schedule
  } catch (error) { rowErrors[schedule.name] = error?.message || 'تغییر وضعیت انجام نشد.' }
  finally { busySchedule.value = '' }
}

async function placeSchedule(schedule) {
  busySchedule.value = schedule.name
  rowErrors[schedule.name] = ''
  try {
    if (cartState.lines.length && !window.confirm('سبد فعلی با اقلام این نوبت جایگزین شود؟')) return
    const payload = await placeMyRecurringOrder(schedule.name, approvalBranch(schedule))
    if (payload?.status === 'needs_review') {
      rowErrors[schedule.name] = (payload.warnings || []).map((warning) => `${warning.item_title || warning.item_slug || ''}: ${warning.reason}`).join(' ')
      return
    }
    if (!payload?.cart_items?.length) throw new Error('قلم سفارش‌پذیری در این نوبت پیدا نشد.')
    clearCart()
    for (const item of payload.cart_items) upsertLine(item)
    saveOrderContext(payload.order_context || {}, { replace: true })
    window.location.assign(cartState.orderContext.order_type ? '/cart' : '/order/type')
  } catch (error) { rowErrors[schedule.name] = error?.message || 'آماده‌سازی سبد این نوبت انجام نشد.' }
  finally { busySchedule.value = '' }
}

async function skipSchedule(schedule) {
  if (!window.confirm(`نوبت ${formatDate(schedule.pending_date)} رد شود؟ این نوبت دیگر به‌صورت معوق نمایش داده نمی‌شود.`)) return
  busySchedule.value = schedule.name
  rowErrors[schedule.name] = ''
  try {
    const payload = await skipMyRecurringOrder(schedule.name)
    const index = schedules.value.findIndex((item) => item.name === schedule.name)
    if (index >= 0 && payload?.schedule) schedules.value[index] = payload.schedule
  } catch (error) { rowErrors[schedule.name] = error?.message || 'ردکردن این نوبت انجام نشد.' }
  finally { busySchedule.value = '' }
}

onMounted(load)
</script>

<style scoped>
.recurring-page { min-height: 100vh; padding-bottom: calc(6rem + env(safe-area-inset-bottom)); background: var(--ds-color-bg-page); color: var(--ds-color-text-primary); }
.recurring-hero { background: radial-gradient(ellipse at 10% 0%, color-mix(in srgb, var(--ds-color-action-accent) 13%, transparent), transparent 45%), var(--ds-color-surface-raised); border-bottom: 1px solid var(--ds-color-border); }
.recurring-body { width: min(880px, calc(100% - 1.5rem)); margin: 1.25rem auto 2rem; display: grid; gap: 1rem; }
.recurring-card { padding: clamp(1rem, 3vw, 1.5rem); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-sm); }
.recurring-card-heading { display: flex; align-items: flex-start; gap: .7rem; margin-bottom: 1rem; }
.recurring-icon { display: grid; place-items: center; flex: none; width: 38px; height: 38px; border-radius: 12px; background: color-mix(in srgb, var(--ds-color-action-primary) 10%, var(--ds-color-surface)); color: var(--ds-color-action-primary); }
.recurring-card-heading h2, .sign-in-card h2, .no-cart-card h2 { margin: 0; font-size: 1rem; font-weight: 900; }
.recurring-card-heading p, .sign-in-card p, .no-cart-card p { margin: .22rem 0 0; color: var(--ds-color-text-secondary); font-size: .8rem; line-height: 1.8; }
.recurring-mini-items { display: flex; flex-wrap: wrap; gap: .45rem; margin: -.35rem 0 1rem; }
.recurring-mini-items span, .recurring-mini-items small { padding: .4rem .6rem; border-radius: 999px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font-size: .72rem; }
.recurring-mini-items b { color: var(--ds-color-action-primary); }
.recurring-form { display: grid; gap: 1rem; }
.recurring-fields { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .65rem; }
.recurring-fields label, .recurring-note { display: grid; gap: .38rem; color: var(--ds-color-text-secondary); font-size: .75rem; font-weight: 800; }
.recurring-fields .input, .recurring-note .input { width: 100%; min-width: 0; min-height: 44px; padding: .55rem .65rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-sm); background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; }
.recurring-note .input { resize: vertical; line-height: 1.8; }
.recurring-fields small, .recurring-note small { color: var(--ds-color-text-muted); font-weight: 500; }
.recurring-weekdays { display: flex; flex-wrap: wrap; gap: .4rem; margin: 0; padding: 0; border: 0; }
.recurring-weekdays legend { flex: 0 0 100%; margin-bottom: .15rem; color: var(--ds-color-text-secondary); font-size: .77rem; font-weight: 800; }
.recurring-day input { position: absolute; opacity: 0; pointer-events: none; }
.recurring-day span { display: grid; place-items: center; min-height: 40px; padding: .35rem .7rem; border: 1px solid var(--ds-color-border); border-radius: 999px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font-size: .73rem; cursor: pointer; }
.recurring-day.active span { border-color: var(--ds-color-action-primary); color: var(--ds-color-action-primary); font-weight: 900; }
.settlement-choice { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .65rem; }
.settlement-option { display: flex; align-items: flex-start; gap: .55rem; min-height: 92px; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); cursor: pointer; }
.settlement-option.selected { border-color: var(--ds-color-action-primary); background: color-mix(in srgb, var(--ds-color-action-primary) 5%, var(--ds-color-surface-raised)); }
.settlement-option input { flex: none; margin-top: .15rem; accent-color: var(--ds-color-action-primary); }
.settlement-option span { display: grid; gap: .3rem; }
.settlement-option strong { color: var(--ds-color-text-primary); font-size: .78rem; }
.settlement-option small { color: var(--ds-color-text-secondary); font-size: .71rem; line-height: 1.8; }
.settlement-option.unavailable { opacity: .65; cursor: not-allowed; }
.recurring-primary, .recurring-secondary, .recurring-refresh { display: inline-flex; align-items: center; justify-content: center; gap: .5rem; min-height: 44px; padding: .55rem .8rem; border-radius: var(--ds-radius-md); font: inherit; font-size: .81rem; font-weight: 900; cursor: pointer; text-decoration: none; }
.recurring-primary { border: 1px solid var(--ds-color-action-primary); background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); }
.recurring-primary:disabled, .recurring-secondary:disabled, .recurring-refresh:disabled { opacity: .55; cursor: wait; }
.recurring-primary--small { min-height: 40px; font-size: .76rem; }
.recurring-secondary, .recurring-refresh { border: 1px solid var(--ds-color-border); background: var(--ds-color-surface); color: var(--ds-color-text-primary); }
.recurring-refresh { min-height: 36px; margin-inline-start: auto; font-size: .72rem; }
.recurring-alert { margin: 0; color: var(--ds-color-status-danger); font-size: .79rem; line-height: 1.7; }
.recurring-success { margin: 0; color: var(--ds-color-status-success); font-size: .79rem; }
.recurring-muted { color: var(--ds-color-text-muted); font-size: .8rem; }
.recurring-empty { padding: 1.4rem; border: 1px dashed var(--ds-color-border); border-radius: var(--ds-radius-md); color: var(--ds-color-text-muted); text-align: center; font-size: .82rem; }
.schedule-list { display: grid; gap: .65rem; }
.schedule-card { padding: .85rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); }
.schedule-card__top { display: flex; justify-content: space-between; align-items: flex-start; gap: .7rem; }
.schedule-card__top > div { display: grid; gap: .28rem; }
.schedule-frequency { color: var(--ds-color-action-primary); font-size: .72rem; font-weight: 900; }
.schedule-card strong { font-size: .82rem; }
.schedule-card > p { margin: .35rem 0 0; color: var(--ds-color-text-secondary); font-size: .74rem; line-height: 1.7; }
.schedule-status { flex: none; padding: .32rem .55rem; border-radius: 999px; background: var(--ds-color-surface-muted); color: var(--ds-color-text-secondary); font-size: .69rem; font-weight: 900; }
.schedule-status.active { background: var(--ds-color-status-success-soft); color: var(--ds-color-status-success); }
.schedule-status.pending { background: var(--ds-color-action-accent-soft, var(--ds-color-surface-muted)); color: var(--ds-color-action-accent); }
.schedule-status.problem { background: var(--ds-color-status-danger-soft); color: var(--ds-color-status-danger); }
.due-reminder { color: var(--ds-color-action-accent) !important; font-weight: 800; }
.recurring-branch-picker { display: grid; grid-template-columns: 9rem minmax(0,1fr); align-items: center; gap: .45rem; margin-top: .55rem; color: var(--ds-color-text-secondary); font-size: .72rem; font-weight: 800; }
.recurring-branch-picker .input { min-height: 40px; padding: .4rem .6rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-sm); background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; }
.schedule-actions { display: flex; align-items: center; flex-wrap: wrap; gap: .45rem; margin-top: .65rem; }
.last-order { color: var(--ds-color-text-muted); font-size: .69rem; }
.sign-in-card, .no-cart-card { display: grid; justify-items: center; gap: .55rem; padding: 2.5rem 1rem; text-align: center; }
.sign-in-card > svg, .no-cart-card > svg { color: var(--ds-color-action-primary); }
.recurring-page :focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 3px; }
@media (max-width: 700px) { .recurring-fields { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 520px) { .recurring-body { width: calc(100% - 1rem); margin-top: .8rem; } .settlement-choice { grid-template-columns: 1fr; } .recurring-card-heading { flex-wrap: wrap; } .recurring-refresh { margin-inline-start: 0; }.recurring-branch-picker { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; } }
</style>
