<template>
  <ManagementPageScaffold title="مربیان و شاگردان" subtitle="مشتری‌های موجود را به مربی تبدیل کنید، درصد گروه را تنظیم کنید و اتصال شاگردها را مدیریت کنید.">
    <template #actions>
      <a class="secondary-btn" href="/management/cooperation-requests">درخواست‌های همکاری</a>
      <button type="button" class="secondary-btn" :disabled="loading" @click="load">{{ loading ? 'در حال بروزرسانی…' : 'بروزرسانی' }}</button>
    </template>

    <div class="coach-kpis">
      <article class="total-box"><small>مربی‌های فعال</small><strong>{{ coaches.length.toLocaleString('fa-IR') }}</strong></article>
      <article class="total-box"><small>شاگردهای متصل</small><strong>{{ totalStudents.toLocaleString('fa-IR') }}</strong></article>
      <article class="total-box"><small>دعوت‌های در انتظار</small><strong>{{ invitations.length.toLocaleString('fa-IR') }}</strong></article>
    </div>

    <div class="coach-workbench-grid">
      <ManagementSurfaceCard title="درصد پیش‌فرض گروه مشتری" subtitle="مقدار روی Customer Group بومی ذخیره می‌شود و به Pricing Rule فروش ERPNext همگام است.">
        <form class="coach-form" @submit.prevent="saveGroupDiscount">
          <label>گروه نهایی مشتری<select v-model="groupForm.customer_group" class="input" required @change="syncGroupPercent"><option value="">انتخاب گروه</option><option v-for="group in groups" :key="group.name" :value="group.name">{{ group.customer_group_name || group.name }}</option></select></label>
          <label>تخفیف پیش‌فرض (%)<input v-model.number="groupForm.discount_percent" class="input" type="number" min="0" max="50" step="0.5" required /></label>
          <button class="primary-btn" type="submit" :disabled="savingGroup || !groupForm.customer_group">{{ savingGroup ? 'در حال ذخیره…' : 'ذخیرهٔ قانون گروه' }}</button>
        </form>
        <p class="helper-note">نمونهٔ آغازین برای گروه مربی ۱۰٪ است. درصد قابل تنظیم است؛ اگر مشتری در چند قانون واجد شرایط باشد، فقط بیشترین تخفیف معتبر اعمال می‌شود.</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="تأیید یا ویرایش مربی" subtitle="هر مشتری موجود با Customer Group بومی و نرخ‌های جداگانه ثبت می‌شود؛ customer_type دست‌نخورده می‌ماند.">
        <form class="coach-form" @submit.prevent="saveCoach">
          <label class="coach-search-field">جستجوی مشتری با نام، شماره یا شناسه
            <div class="coach-search-row"><input v-model.trim="searchText" class="input" placeholder="نام یا 09…" @keydown.enter.prevent="searchCustomers" /><button type="button" class="secondary-btn" :disabled="searching || searchText.length < 2" @click="searchCustomers">{{ searching ? '…' : 'جستجو' }}</button></div>
          </label>
          <div v-if="candidates.length" class="candidate-list" role="listbox" aria-label="مشتری‌های پیدا‌شده">
            <button v-for="candidate in candidates" :key="candidate.name" type="button" class="candidate-row" :class="{ selected: coachForm.coach === candidate.name }" @click="selectCandidate(candidate)">
              <span><strong>{{ candidate.customer_name || candidate.name }}</strong><small dir="ltr">{{ candidate.mobile_no || 'بدون موبایل' }} · {{ candidate.name }}</small></span>
              <small>{{ candidate.restaurant_coach_invites_enabled ? 'مربی فعال' : candidate.customer_group || 'مشتری' }}</small>
            </button>
          </div>
          <p v-if="coachForm.coach" class="selected-customer">مشتری انتخاب‌شده: <strong>{{ coachForm.customer_label || coachForm.coach }}</strong></p>
          <label>گروه مشتری<select v-model="coachForm.customer_group" class="input" required><option value="">انتخاب گروه</option><option v-for="group in groups" :key="group.name" :value="group.name">{{ group.customer_group_name || group.name }}<template v-if="Number(group.restaurant_default_discount_percent || 0)"> · {{ Number(group.restaurant_default_discount_percent).toLocaleString('fa-IR') }}٪</template></option></select></label>
          <div class="coach-rate-grid"><label>تخفیف شاگرد (%)<input v-model.number="coachForm.discount_percent" class="input" type="number" min="0" max="50" step="0.5" /></label><label>سهم مربی (%)<input v-model.number="coachForm.commission_percent" class="input" type="number" min="0" max="50" step="0.5" /></label></div>
          <button class="primary-btn" type="submit" :disabled="savingCoach || !coachForm.coach || !coachForm.customer_group">{{ savingCoach ? 'در حال ذخیره…' : 'تأیید / ذخیره مربی' }}</button>
        </form>
        <p class="helper-note">سهم نمونهٔ ۵٪ پس از تحویل و تسویه به کش‌بک قابل خرج و غیرقابل‌برداشت می‌رود؛ از مبلغ اقلام پس از تخفیف منتخب محاسبه می‌شود.</p>
      </ManagementSurfaceCard>
    </div>

    <ManagementSurfaceCard title="افزودن یا انتقال شاگرد" subtitle="شمارهٔ ثبت‌شده، مشتری را به‌صورت دستی پیدا می‌کند. برای فرد ثبت‌نام‌نکرده ایمیل هم لازم است و اتصال تا تأیید ایمیل انجام نمی‌شود.">
      <form class="student-form" @submit.prevent="assignStudent">
        <label>مربی<select v-model="studentForm.coach" class="input" required><option value="">انتخاب مربی</option><option v-for="coach in coaches" :key="coach.name" :value="coach.name">{{ coach.customer_name }} · {{ coach.name }}</option></select></label>
        <label>شماره همراه شاگرد<input v-model.trim="studentForm.mobile" class="input" dir="ltr" inputmode="tel" placeholder="09…" required /></label>
        <label>ایمیل ثبت‌نام <small>برای دعوت فرد جدید</small><input v-model.trim="studentForm.email" class="input" type="email" dir="ltr" placeholder="name@example.com" /></label>
        <label class="reason-field">دلیل اتصال یا انتقال<input v-model.trim="studentForm.reason" class="input" maxlength="1000" placeholder="مثلاً درخواست مشتری یا انتقال از مربی قبلی" required /></label>
        <button class="primary-btn" type="submit" :disabled="assigning || !studentForm.coach || !studentForm.mobile || !studentForm.reason">{{ assigning ? 'در حال ثبت…' : 'اتصال شاگرد' }}</button>
      </form>
      <div v-if="inviteLink" class="invite-link-box"><div><strong>دعوت در انتظار ثبت‌نام ساخته شد</strong><small>اتصال فقط بعد از تأیید ایمیل انجام می‌شود. پیوند را برای شاگرد بفرستید.</small></div><input :value="inviteLink" readonly dir="ltr" /><button type="button" class="secondary-btn" @click="copyInvite">{{ inviteCopied ? 'کپی شد' : 'کپی پیوند دعوت' }}</button></div>
      <p class="helper-note">انتقال مربی فقط از همین ابزار مدیریتی انجام می‌شود و دلیل آن در سابقهٔ Customer ثبت می‌شود. سفارش‌های گذشته تغییر نمی‌کنند.</p>
    </ManagementSurfaceCard>

    <div class="coach-lists-grid">
      <ManagementSurfaceCard title="مربیان فعال" subtitle="کلیک روی هر مربی فرم نرخ و Customer Group را برای ویرایش پر می‌کند.">
        <ManagementListView :columns="coachColumns" :rows="coaches" row-key="name" :row-clickable="true" @row-click="selectCoach">
          <template #cell-customer_name="{ row }"><strong>{{ row.customer_name }}</strong><small class="d-block muted">{{ row.name }} · {{ row.customer_group }}</small></template>
          <template #cell-rates="{ row }">شاگرد {{ Number(row.restaurant_coach_discount_percent || 0).toLocaleString('fa-IR') }}٪ · سهم {{ Number(row.restaurant_coach_commission_percent || 0).toLocaleString('fa-IR') }}٪</template>
          <template #cell-students="{ row }">{{ (row.students || []).length.toLocaleString('fa-IR') }}</template>
          <template #empty>هنوز مربی تأییدشده‌ای ثبت نشده است.</template>
        </ManagementListView>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="دعوت‌های در انتظار" subtitle="کد دعوت به‌تنهایی اتصال ایجاد نمی‌کند؛ ایمیل و شماره باید با حساب تأییدشده تطبیق کنند.">
        <ManagementListView :columns="invitationColumns" :rows="invitations" row-key="name">
          <template #cell-coach="{ row }">{{ coachName(row.coach) }}</template>
          <template #cell-mobile="{ row }"><span dir="ltr">{{ row.mobile }}</span><small class="d-block muted" dir="ltr">{{ row.email }}</small></template>
          <template #cell-link="{ row }"><button type="button" class="tertiary-btn" @click="copyPendingInvite(row)">{{ copiedInvitation === row.name ? 'کپی شد' : 'کپی پیوند' }}</button></template>
          <template #empty>دعوت در انتظاری وجود ندارد.</template>
        </ManagementListView>
      </ManagementSurfaceCard>
    </div>

    <p v-if="error" class="page-message error" role="alert">{{ error }}</p>
    <p v-if="message" class="page-message success" role="status">{{ message }}</p>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import { assignManagementCoachStudent, getManagementCoachWorkbench, listManagementCustomerGroups, saveManagementCoachProfile, saveManagementCustomerGroupDiscount, searchManagementCoachCustomers } from '@/utils/api'

const coachColumns = [{ key: 'customer_name', label: 'مربی' }, { key: 'rates', label: 'نرخ‌ها' }, { key: 'students', label: 'شاگرد' }]
const invitationColumns = [{ key: 'coach', label: 'مربی' }, { key: 'mobile', label: 'شماره / ایمیل' }, { key: 'link', label: 'دعوت' }]
const loading = ref(false), searching = ref(false), savingCoach = ref(false), savingGroup = ref(false), assigning = ref(false)
const error = ref(''), message = ref(''), searchText = ref(''), candidates = ref([]), coaches = ref([]), invitations = ref([]), groups = ref([])
const inviteLink = ref(''), inviteCopied = ref(false), copiedInvitation = ref('')
const totalStudents = computed(() => coaches.value.reduce((sum, coach) => sum + (coach.students || []).length, 0))
const coachForm = reactive({ coach: '', customer_label: '', customer_group: '', discount_percent: 5, commission_percent: 5 })
const groupForm = reactive({ customer_group: '', discount_percent: 0 })
const studentForm = reactive({ coach: '', mobile: '', email: '', reason: '' })

function coachName(name) { return coaches.value.find((coach) => coach.name === name)?.customer_name || name }
function syncGroupPercent() { groupForm.discount_percent = Number(groups.value.find((group) => group.name === groupForm.customer_group)?.restaurant_default_discount_percent || 0) }
function selectCandidate(row) {
  coachForm.coach = row.name; coachForm.customer_label = row.customer_name || row.name
  coachForm.customer_group = row.customer_group || ''
  coachForm.discount_percent = Number(row.restaurant_coach_discount_percent || 5)
  coachForm.commission_percent = Number(row.restaurant_coach_commission_percent || 5)
}
function selectCoach(row) {
  coachForm.coach = row.name; coachForm.customer_label = row.customer_name
  coachForm.customer_group = row.customer_group || ''
  coachForm.discount_percent = Number(row.restaurant_coach_discount_percent || 5)
  coachForm.commission_percent = Number(row.restaurant_coach_commission_percent || 5)
}

async function load() {
  loading.value = true; error.value = ''
  try {
    const [workbench, groupPayload] = await Promise.all([getManagementCoachWorkbench(), listManagementCustomerGroups()])
    coaches.value = workbench?.coaches || []; invitations.value = workbench?.pending_invites || []; groups.value = groupPayload?.groups || []
    if (!groupForm.customer_group && groups.value.length) { groupForm.customer_group = groups.value[0].name; syncGroupPercent() }
  } catch (err) { error.value = err?.message || 'دریافت اطلاعات مربی‌ها ناموفق بود.' }
  finally { loading.value = false }
}

async function searchCustomers() {
  if (searchText.value.length < 2) return
  searching.value = true; error.value = ''
  try { const data = await searchManagementCoachCustomers(searchText.value); candidates.value = data?.customers || [] }
  catch (err) { error.value = err?.message || 'جستجوی مشتری انجام نشد.' }
  finally { searching.value = false }
}

async function saveGroupDiscount() {
  savingGroup.value = true; error.value = ''; message.value = ''
  try {
    await saveManagementCustomerGroupDiscount(groupForm)
    const row = groups.value.find((group) => group.name === groupForm.customer_group)
    if (row) row.restaurant_default_discount_percent = Number(groupForm.discount_percent)
    message.value = 'درصد گروه روی Customer Group ذخیره و با Pricing Rule همگام شد.'
  } catch (err) { error.value = err?.message || 'ذخیرهٔ تخفیف گروه انجام نشد.' }
  finally { savingGroup.value = false }
}

async function saveCoach() {
  savingCoach.value = true; error.value = ''; message.value = ''
  try {
    const result = await saveManagementCoachProfile(coachForm)
    message.value = `مربی ${coachForm.customer_label || coachForm.coach} فعال شد. کد معرفی: ${result.referral_code || 'در پنل مربی نمایش داده می‌شود.'}`
    candidates.value = []
    await load()
  } catch (err) { error.value = err?.message || 'ثبت مربی انجام نشد.' }
  finally { savingCoach.value = false }
}

async function assignStudent() {
  assigning.value = true; error.value = ''; message.value = ''; inviteLink.value = ''
  try {
    const result = await assignManagementCoachStudent(studentForm)
    if (result?.pending) {
      const coach = coaches.value.find((row) => row.name === studentForm.coach)
      inviteLink.value = coach?.referral_code ? `${window.location.origin}/customer/login?ref=${encodeURIComponent(coach.referral_code)}` : ''
      message.value = 'دعوت در انتظار ثبت‌نام ساخته شد. شماره به‌تنهایی شاگرد را متصل نمی‌کند.'
    } else message.value = result?.status === 'already_linked' ? 'این مشتری از قبل به همین مربی متصل است.' : 'شاگرد به مربی متصل شد؛ این ارتباط فقط خریدهای بعدی را تغییر می‌دهد.'
    studentForm.mobile = ''; studentForm.email = ''; studentForm.reason = ''
    await load()
  } catch (err) { error.value = err?.message || 'اتصال شاگرد انجام نشد.' }
  finally { assigning.value = false }
}

async function copyInvite() {
  try { await navigator.clipboard.writeText(inviteLink.value); inviteCopied.value = true; setTimeout(() => { inviteCopied.value = false }, 1800) }
  catch { error.value = 'کپی خودکار در دسترس نیست؛ پیوند را دستی کپی کنید.' }
}
async function copyPendingInvite(row) {
  const coach = coaches.value.find((item) => item.name === row.coach)
  if (!coach?.referral_code) return
  try { await navigator.clipboard.writeText(`${window.location.origin}/customer/login?ref=${encodeURIComponent(coach.referral_code)}`); copiedInvitation.value = row.name; setTimeout(() => { copiedInvitation.value = '' }, 1800) }
  catch { error.value = 'کپی پیوند دعوت ناموفق بود.' }
}

onMounted(load)
</script>

<style scoped>
.coach-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .75rem; }
.coach-workbench-grid, .coach-lists-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; }
.coach-form, .student-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); align-items: end; gap: .7rem; }
.coach-form label, .student-form label { display: grid; gap: .35rem; min-width: 0; color: var(--mg-text-muted); font-size: .76rem; font-weight: 800; }
.coach-form .input, .student-form .input { min-height: 42px; width: 100%; border: 1px solid var(--mg-border-light); border-radius: 10px; padding: .55rem .7rem; color: var(--mg-text-main); background: var(--mg-bg-surface); font: inherit; font-weight: 500; }
.coach-form .primary-btn, .student-form .primary-btn { min-height: 42px; }
.coach-search-field, .reason-field { grid-column: 1 / -1; }
.coach-search-row { display: flex; gap: .45rem; }
.coach-search-row .input { flex: 1; }
.coach-rate-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .55rem; }
.candidate-list { grid-column: 1 / -1; display: grid; max-height: 230px; overflow: auto; border: 1px solid var(--mg-border-light); border-radius: 12px; }
.candidate-row { display: flex; align-items: center; justify-content: space-between; gap: .6rem; width: 100%; padding: .65rem .75rem; border: 0; border-bottom: 1px solid var(--mg-border-light); background: var(--mg-bg-surface); color: var(--mg-text-main); text-align: start; font: inherit; cursor: pointer; }
.candidate-row:last-child { border-bottom: 0; }
.candidate-row.selected { background: color-mix(in srgb, var(--mg-primary) 9%, var(--mg-bg-surface)); }
.candidate-row > span { display: grid; gap: .15rem; }
.candidate-row strong { font-size: .79rem; }
.candidate-row small, .selected-customer, .helper-note { color: var(--mg-text-muted); font-size: .72rem; line-height: 1.8; }
.selected-customer { grid-column: 1 / -1; margin: 0; }
.helper-note { margin: .75rem 0 0; }
.invite-link-box { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: .5rem; margin-top: .8rem; padding: .75rem; border: 1px solid var(--mg-border-light); border-radius: 12px; background: var(--mg-bg-surface); }
.invite-link-box > div { display: grid; gap: .2rem; }
.invite-link-box strong { color: var(--mg-text-main); font-size: .8rem; }
.invite-link-box small { color: var(--mg-text-muted); font-size: .7rem; }
.invite-link-box input { grid-column: 1 / -1; min-height: 38px; width: 100%; border: 1px solid var(--mg-border-light); border-radius: 9px; padding: .4rem .6rem; background: var(--mg-bg-page); }
.page-message { margin: 0; padding: .75rem 1rem; border-radius: 12px; font-size: .8rem; }
.page-message.error { color: var(--mg-danger, #bd3b32); background: color-mix(in srgb, var(--mg-danger, #bd3b32) 8%, var(--mg-bg-page)); }
.page-message.success { color: var(--mg-success, #2f7656); background: color-mix(in srgb, var(--mg-success, #2f7656) 10%, var(--mg-bg-page)); }
@media (max-width: 860px) { .coach-workbench-grid, .coach-lists-grid { grid-template-columns: 1fr; } }
@media (max-width: 560px) { .coach-kpis { grid-template-columns: 1fr; } .coach-form, .student-form { grid-template-columns: 1fr; } .coach-search-field, .reason-field, .selected-customer, .candidate-list { grid-column: auto; } .invite-link-box { grid-template-columns: 1fr; } .invite-link-box input { grid-column: auto; } }
</style>
