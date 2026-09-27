<template>
  <div class="customer-page referral-page" dir="rtl">
    <CustomerPageHeader eyebrow="حساب من" title="معرفی و باشگاه مربیان" subtitle="کد شما برای دوستان و اعضای گروه قابل اشتراک است." fallback-href="/customer/dashboard">
      <template #eyebrow-icon><Share2 :size="16" /></template>
      <template #action><a class="customer-page__action" href="/customer/dashboard">حساب من</a></template>
    </CustomerPageHeader>

    <main class="customer-page__body referral-body">
      <p v-if="loading" class="referral-status" role="status">در حال دریافت کد معرفی…</p>
      <p v-if="error" class="referral-alert" role="alert">{{ error }} <a href="/customer/login?redirect=/customer/referrals">ورود به حساب</a></p>
      <p v-if="message" class="referral-success" role="status">{{ message }}</p>

      <section v-if="profile" class="customer-glass-card referral-code-card">
        <div class="referral-card-heading"><span class="referral-icon"><TicketCheck :size="21" /></span><div><p>کد اختصاصی شما</p><h2 dir="ltr">{{ profile.referral_code }}</h2></div></div>
        <p class="referral-explainer">این پیوند را برای دوستان بفرستید. اگر کد متعلق به مربی تأییدشده باشد، عضویت و تخفیف شاگرد بعد از تأیید ایمیل فعال می‌شود.</p>
        <label class="referral-link-label" for="referral-share-link">پیوند ثبت‌نام</label>
        <div class="referral-link-row"><input id="referral-share-link" :value="referralUrl" readonly dir="ltr" /><button type="button" class="referral-primary referral-copy" @click="shareLink"><Share2 :size="16" />{{ shareLabel }}</button></div>
        <p v-if="profile.old_code" class="referral-old-code">کد قبلی {{ profile.old_code }} هم همچنان معتبر است.</p>
      </section>

      <section v-if="profile?.can_customize_code" class="customer-glass-card referral-customize">
        <div><h2>یک بار کد دلخواهت را انتخاب کن</h2><p>کد ۴ تا ۲۰ حرف یا عدد انگلیسی؛ بعد از ذخیره دیگر قابل تغییر نیست.</p></div>
        <form class="referral-customize-form" @submit.prevent="saveCode"><label class="customer-field" for="new-referral-code">کد دلخواه<input id="new-referral-code" v-model.trim="newCode" class="customer-input" dir="ltr" minlength="4" maxlength="20" autocomplete="off" placeholder="مثلاً SEPEHR20" /></label><button class="referral-primary" type="submit" :disabled="saving || !validCode">{{ saving ? 'در حال ذخیره…' : 'ثبت یک‌بارهٔ کد' }}</button></form>
      </section>

      <section v-if="profile?.is_coach" class="customer-glass-card coach-summary">
        <div class="coach-summary__head"><span class="referral-icon referral-icon--coach"><UsersRound :size="21" /></span><div><h2>باشگاه مربی‌گری شما</h2><p>اعتبار سهم خرید شاگردها پس از تحویل سفارش و تسویه واریز می‌شود.</p></div></div>
        <div class="coach-summary__stats"><article><small>تخفیف هر شاگرد</small><strong>{{ Number(profile.coach_discount_percent || 0).toLocaleString('fa-IR') }}٪</strong></article><article><small>سهم مربی از خرید خالص</small><strong>{{ Number(profile.coach_commission_percent || 0).toLocaleString('fa-IR') }}٪</strong></article><article><small>اعتبار خرید شما</small><strong>{{ Number(profile.cashback_balance || 0).toLocaleString('fa-IR') }} <small>{{ currencyLabel }}</small></strong></article></div>
        <p class="coach-cashback-note">این سهم در بخش کش‌بک می‌نشیند؛ برای خرید قابل استفاده است و قابل برداشت بانکی نیست.</p>
        <div v-if="profile.students?.length" class="coach-students"><h3>شاگردهای متصل‌شده <span>{{ profile.students.length.toLocaleString('fa-IR') }}</span></h3><article v-for="(student, index) in profile.students" :key="`${student.customer_name}-${index}`"><span class="student-avatar">{{ String(student.customer_name || 'ش').slice(0, 1) }}</span><div><strong>{{ student.customer_name || 'عضو گروه' }}</strong><small>{{ student.restaurant_coach_since ? `عضویت از ${formatDate(student.restaurant_coach_since)}` : 'عضو گروه مربی' }}</small></div><span class="student-active">فعال</span></article></div>
        <p v-else class="referral-empty">هنوز شاگردی به گروه شما متصل نشده است.</p>
      </section>

      <section v-else-if="profile" class="customer-glass-card referral-relationship">
        <span class="referral-icon"><UsersRound :size="20" /></span><div><h2>{{ profile.coach_name ? `عضو گروه ${profile.coach_name}` : 'برنامهٔ معرفی دوستان' }}</h2><p>{{ profile.referral_relation === 'مربی' ? 'تخفیف گروه مربی در سفارش بعدی شما بررسی می‌شود.' : 'کد شما برای معرفی عادی دوستان قابل استفاده است.' }}</p></div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Share2, TicketCheck, UsersRound } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import { getMenuBoot, getMyReferralProfile, setMyReferralCode } from '@/utils/api'
import { hasCustomerSession } from '@/utils/customerAuth'

const profile = ref(null)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const message = ref('')
const newCode = ref('')
const shareLabel = ref('کپی پیوند')
const currency = ref('IRR')
const validCode = computed(() => /^[A-Za-z0-9]{4,20}$/.test(newCode.value))
const referralUrl = computed(() => profile.value?.referral_code ? `${window.location.origin}/customer/login?ref=${encodeURIComponent(profile.value.referral_code)}` : '')
const currencyLabel = computed(() => ['TOMAN', 'IRT'].includes(currency.value) ? 'تومان' : 'ریال')

function formatDate(value) { return value ? new Date(`${String(value).slice(0, 10)}T12:00:00`).toLocaleDateString('fa-IR') : '—' }

async function load() {
  if (!hasCustomerSession()) { error.value = 'برای دیدن کد معرفی، ابتدا وارد حساب مشتری شوید.'; return }
  loading.value = true; error.value = ''
  try {
    const [data, boot] = await Promise.all([getMyReferralProfile(), getMenuBoot()])
    profile.value = data || null
    currency.value = boot?.currency || 'IRR'
  } catch (err) { error.value = err?.message || 'کد معرفی دریافت نشد.' }
  finally { loading.value = false }
}

async function shareLink() {
  if (!referralUrl.value) return
  try {
    if (navigator.share) await navigator.share({ title: 'دعوت به سفارش از وی‌درخت', url: referralUrl.value })
    else { await navigator.clipboard.writeText(referralUrl.value); shareLabel.value = 'پیوند کپی شد'; setTimeout(() => { shareLabel.value = 'کپی پیوند' }, 2000) }
  } catch (err) {
    if (err?.name === 'AbortError') return
    try { await navigator.clipboard.writeText(referralUrl.value); shareLabel.value = 'پیوند کپی شد'; setTimeout(() => { shareLabel.value = 'کپی پیوند' }, 2000) }
    catch { error.value = 'اشتراک‌گذاری خودکار در دسترس نیست؛ پیوند را دستی کپی کنید.' }
  }
}

async function saveCode() {
  if (!validCode.value || saving.value) return
  saving.value = true; error.value = ''; message.value = ''
  try {
    const result = await setMyReferralCode(newCode.value)
    profile.value = { ...profile.value, referral_code: result.referral_code, old_code: result.old_code, can_customize_code: false }
    newCode.value = ''
    message.value = 'کد دلخواه ثبت شد؛ پیوندهای کد قبلی هم معتبر مانده‌اند.'
  } catch (err) { error.value = err?.message || 'ذخیرهٔ کد انجام نشد.' }
  finally { saving.value = false }
}

onMounted(load)
</script>

<style scoped>
.referral-body { display: grid; gap: 1rem; }
.referral-status, .referral-alert, .referral-success { margin: 0; padding: .8rem 1rem; border-radius: 14px; font-size: .84rem; line-height: 1.8; }
.referral-alert { color: var(--ds-color-danger, #a13a2b); background: color-mix(in srgb, var(--ds-color-danger, #a13a2b) 8%, var(--ds-color-surface)); }
.referral-success { color: var(--ds-color-text-primary); background: var(--ds-color-action-accent-soft); }
.referral-alert a { color: inherit; font-weight: 900; }
.referral-code-card, .referral-customize, .coach-summary, .referral-relationship { padding: clamp(1rem, 3vw, 1.4rem); border-radius: 24px; }
.referral-card-heading, .coach-summary__head, .referral-relationship { display: flex; align-items: center; gap: .85rem; }
.referral-icon { display: grid; place-items: center; width: 44px; height: 44px; flex: none; border-radius: 15px; color: var(--ds-color-action-primary); background: var(--ds-color-action-accent-soft); }
.referral-icon--coach { color: var(--ds-color-action-accent); }
.referral-card-heading p { margin: 0 0 .15rem; color: var(--ds-color-text-secondary); font-size: .75rem; }
.referral-card-heading h2 { margin: 0; color: var(--ds-color-text-primary); font-size: 1.45rem; letter-spacing: .06em; }
.referral-explainer, .referral-customize p, .coach-summary__head p, .referral-relationship p { margin: .7rem 0 1rem; color: var(--ds-color-text-secondary); font-size: .82rem; line-height: 1.85; }
.referral-link-label { display: block; margin-bottom: .35rem; color: var(--ds-color-text-secondary); font-size: .74rem; font-weight: 800; }
.referral-link-row { display: flex; gap: .55rem; }
.referral-link-row input { min-width: 0; flex: 1; min-height: 44px; border: 1px solid var(--ds-color-border); border-radius: 13px; padding: .5rem .7rem; color: var(--ds-color-text-primary); background: var(--ds-color-surface); }
.referral-primary { display: inline-flex; align-items: center; justify-content: center; gap: .4rem; min-height: 44px; border: 0; border-radius: 13px; padding: .6rem .9rem; color: var(--ds-color-text-on-primary, white); background: var(--ds-color-action-primary); font: inherit; font-size: .8rem; font-weight: 900; cursor: pointer; }
.referral-primary:disabled { opacity: .55; cursor: wait; }
.referral-old-code, .coach-cashback-note { margin: .7rem 0 0; color: var(--ds-color-text-secondary); font-size: .75rem; line-height: 1.8; }
.referral-customize { display: grid; gap: .8rem; }
.referral-customize h2, .coach-summary h2, .referral-relationship h2 { margin: 0; color: var(--ds-color-text-primary); font-size: 1rem; }
.referral-customize p { margin: .3rem 0 0; }
.referral-customize-form { display: flex; align-items: flex-end; gap: .6rem; }
.referral-customize-form .customer-field { flex: 1; }
.referral-customize-form .customer-field { display: grid; gap: .4rem; color: var(--ds-color-text-secondary); font-size: .76rem; font-weight: 800; }
.referral-customize-form .customer-input { min-height: 44px; width: 100%; border: 1px solid var(--ds-color-border); border-radius: 13px; padding: .5rem .7rem; color: var(--ds-color-text-primary); background: var(--ds-color-surface); font: inherit; }
.coach-summary__head p, .referral-relationship p { margin: .25rem 0 0; }
.coach-summary__stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .65rem; margin-top: 1rem; }
.coach-summary__stats article { display: grid; gap: .35rem; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: 16px; background: var(--ds-color-surface); }
.coach-summary__stats small { color: var(--ds-color-text-secondary); font-size: .72rem; }
.coach-summary__stats strong { color: var(--ds-color-text-primary); font-size: 1.05rem; }
.coach-summary__stats strong small { font-size: .7rem; }
.coach-students { margin-top: 1.2rem; }
.coach-students h3 { display: flex; align-items: center; gap: .5rem; margin: 0 0 .55rem; color: var(--ds-color-text-primary); font-size: .9rem; }
.coach-students h3 span { padding: .1rem .45rem; border-radius: 99px; background: var(--ds-color-action-accent-soft); }
.coach-students article { display: flex; align-items: center; gap: .65rem; padding: .65rem 0; border-top: 1px solid var(--ds-color-border); }
.student-avatar { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 50%; color: var(--ds-color-action-primary); background: var(--ds-color-action-accent-soft); font-weight: 900; }
.coach-students article div { display: grid; gap: .15rem; flex: 1; }
.coach-students article strong { color: var(--ds-color-text-primary); font-size: .82rem; }
.coach-students article small, .student-active, .referral-empty { color: var(--ds-color-text-secondary); font-size: .72rem; }
.referral-empty { margin: 1rem 0 0; }
@media (max-width: 560px) { .referral-link-row, .referral-customize-form { align-items: stretch; flex-direction: column; } .coach-summary__stats { grid-template-columns: 1fr; } }
</style>
