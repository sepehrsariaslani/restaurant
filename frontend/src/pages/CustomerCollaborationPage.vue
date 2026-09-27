<template>
  <div class="collaboration-page customer-page" dir="rtl">
    <CustomerPageHeader
      eyebrow="همکاری با ما"
      title="غذای خوب، برای جمع‌های بزرگ‌تر"
      subtitle="برای محل کار، باشگاه یا شاگردانتان یک برنامهٔ غذایی متناسب بچینیم."
      hero-class="collaboration-hero"
      fallback-href="/customer/dashboard"
    >
      <template #eyebrow-icon><Handshake :size="15" aria-hidden="true" /></template>
      <div class="collaboration-hero__pills" aria-label="مناسب برای">
        <span><Building2 :size="15" /> محل کار</span>
        <span><Dumbbell :size="15" /> باشگاه</span>
        <span><UsersRound :size="15" /> مربی و شاگردان</span>
      </div>
    </CustomerPageHeader>

    <main class="collaboration-body">
      <section class="collaboration-rules" aria-labelledby="collaboration-rules-title">
        <div class="collaboration-section-heading">
          <span class="collaboration-step">۱</span>
          <div><h2 id="collaboration-rules-title">قواعد همکاری</h2><p>قبل از ثبت درخواست، این چند نکته را ببینید.</p></div>
        </div>
        <div class="rule-grid">
          <article class="rule-card"><span class="rule-number">01</span><div><h3>اول بررسی، بعد توافق</h3><p>درخواست شما بررسی می‌شود؛ قیمت، تخفیف، محدودهٔ ارسال و شروع کار پس از تأیید دوطرفه مشخص خواهد شد.</p></div></article>
          <article class="rule-card"><span class="rule-number">02</span><div><h3>برنامهٔ غذایی قابل تنظیم</h3><p>تعداد وعده، روزهای تحویل و بازهٔ زمانی پیشنهادی را اعلام کنید تا برنامهٔ مناسب مجموعه‌تان را بچینیم.</p></div></article>
          <article class="rule-card"><span class="rule-number">03</span><div><h3>شفافیت در هزینه</h3><p>ثبت درخواست هزینه‌ای ندارد و به‌تنهایی سفارش یا تعهد پرداخت ایجاد نمی‌کند. شرایط نهایی در قرارداد تأیید می‌شود.</p></div></article>
        </div>
      </section>

      <section v-if="!success" class="collaboration-form-card" aria-labelledby="application-title">
        <div class="collaboration-section-heading">
          <span class="collaboration-step collaboration-step--accent">۲</span>
          <div><h2 id="application-title">معرفی مجموعهٔ شما</h2><p>اطلاعات را یک‌بار ثبت کنید تا برای هماهنگی با شما تماس بگیریم.</p></div>
        </div>

        <div class="collaboration-kind-grid" role="group" aria-label="نوع همکاری">
          <button v-for="option in types" :key="option.value" type="button" class="kind-option" :class="{ selected: form.collaboration_type === option.value }" :aria-pressed="form.collaboration_type === option.value" @click="form.collaboration_type = option.value">
            <component :is="option.icon" :size="21" aria-hidden="true" /><span><strong>{{ option.title }}</strong><small>{{ option.description }}</small></span>
            <CheckCircle2 v-if="form.collaboration_type === option.value" class="kind-option__check" :size="19" aria-hidden="true" />
          </button>
        </div>

        <form class="collaboration-form" @submit.prevent="submitRequest">
          <div class="form-section-label"><span>مشخصات مجموعه</span><i></i></div>
          <div class="collaboration-fields">
            <label class="collab-field"><span>نام مجموعه <b>*</b></span><input v-model.trim="form.organization_name" class="input" required maxlength="180" placeholder="مثلاً شرکت آفتاب یا باشگاه تندرست" /></label>
            <label class="collab-field"><span>نام و نام خانوادگی رابط <b>*</b></span><input v-model.trim="form.contact_name" class="input" required maxlength="140" autocomplete="name" /></label>
            <label class="collab-field"><span>شماره تماس <b>*</b></span><input v-model.trim="form.mobile" class="input" type="tel" inputmode="tel" autocomplete="tel" required placeholder="09xxxxxxxxx" dir="ltr" /></label>
            <label class="collab-field"><span>ایمیل <small>اختیاری</small></span><input v-model.trim="form.email" class="input" type="email" autocomplete="email" placeholder="name@example.com" dir="ltr" /></label>
            <label class="collab-field collab-field--wide"><span>نشانی محل فعالیت <b>*</b></span><textarea v-model.trim="form.address" class="input" rows="3" required maxlength="700" placeholder="شهر، خیابان، کوچه و نشانی دقیق محل تحویل" /></label>
            <label class="collab-field"><span>تعداد کارکنان / اعضا</span><input v-model.number="form.expected_members" class="input" type="number" min="1" max="100000" inputmode="numeric" placeholder="مثلاً ۲۰" /></label>
            <label class="collab-field"><span>وعدهٔ تقریبی در هر نوبت</span><input v-model.number="form.meal_count" class="input" type="number" min="1" max="10000" inputmode="numeric" placeholder="مثلاً ۱۵" /></label>
          </div>

          <div class="form-section-label"><span>برنامهٔ غذایی پیشنهادی</span><i></i></div>
          <div class="collaboration-fields">
            <label class="collab-field"><span>تناوب موردنظر</span><select v-model="form.frequency" class="input"><option value="">فعلاً مشخص نیست</option><option>روزانه</option><option>هفتگی</option><option>ماهانه</option><option>بر اساس قرارداد</option></select></label>
            <label class="collab-field"><span>زمان تقریبی تحویل</span><input v-model="form.delivery_time" class="input" type="time" dir="ltr" /></label>
            <fieldset v-if="form.frequency === 'هفتگی'" class="collab-field collab-field--wide weekday-field">
              <legend>روزهای موردنظر <b>*</b></legend>
              <div class="weekday-list"><label v-for="day in weekdays" :key="day" class="weekday-chip" :class="{ checked: form.weekdays.includes(day) }"><input v-model="form.weekdays" type="checkbox" :value="day" /><span>{{ day }}</span></label></div>
            </fieldset>
            <label class="collab-field collab-field--wide"><span>چه غذایی یا چه شرایطی برایتان مهم است؟</span><textarea v-model.trim="form.details" class="input" rows="3" maxlength="1000" placeholder="مثلاً غذای روزانهٔ پرسنل، منوی رژیمی، تنوع هفتگی یا محدودیت غذایی" /></label>
          </div>

          <label class="collab-consent"><input v-model="form.accepted_terms" type="checkbox" required /><span>قوانین همکاری را خواندم و می‌دانم ثبت این فرم فقط درخواست بررسی است و تا زمان توافق نهایی، سفارش یا پرداختی ثبت نمی‌شود.</span></label>
          <p v-if="error" class="collab-feedback collab-feedback--error" role="alert">{{ error }}</p>
          <button class="collab-submit" type="submit" :disabled="submitting || !canSubmit"><span>{{ submitting ? 'در حال ثبت درخواست…' : 'ثبت درخواست همکاری' }}</span><ArrowLeft :size="18" aria-hidden="true" /></button>
          <p class="collab-privacy">شمارهٔ شما فقط برای پیگیری همین درخواست استفاده می‌شود.</p>
        </form>
      </section>

      <section v-else class="collaboration-success" role="status" aria-live="polite">
        <span class="success-icon"><CheckCircle2 :size="32" /></span>
        <p class="success-eyebrow">درخواست ثبت شد</p>
        <h2>از آشنایی با مجموعه‌تان خوشحالیم.</h2>
        <p>درخواست شما با کد <strong dir="ltr">{{ success.request_id }}</strong> برای بررسی ارسال شد. همکاران ما برای هماهنگی با شما تماس می‌گیرند.</p>
        <a href="/menu" class="collab-back-link">دیدن منوی رستوران <ArrowLeft :size="16" /></a>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ArrowLeft, Building2, CheckCircle2, Dumbbell, Handshake, UsersRound } from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import { submitPublicCollaborationRequest } from '@/utils/api'

const types = [
  { value: 'سازمان و محل کار', title: 'سازمان و محل کار', description: 'وعدهٔ غذایی روزانه برای کارکنان', icon: Building2 },
  { value: 'باشگاه ورزشی', title: 'باشگاه ورزشی', description: 'غذای سالم و رژیمی برای اعضا', icon: Dumbbell },
  { value: 'مربی و شاگردان', title: 'مربی و شاگردان', description: 'همکاری ویژه برای مربی‌ها و شاگردان', icon: UsersRound },
]
const weekdays = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه']
const form = reactive({
  collaboration_type: types[0].value,
  organization_name: '', contact_name: '', mobile: '', email: '', address: '',
  expected_members: null, meal_count: null, frequency: '', weekdays: [], delivery_time: '', details: '', accepted_terms: false,
})
const submitting = ref(false)
const error = ref('')
const success = ref(null)
const canSubmit = computed(() => form.organization_name && form.contact_name && form.mobile && form.address && form.accepted_terms && (form.frequency !== 'هفتگی' || form.weekdays.length))

async function submitRequest() {
  if (submitting.value || !canSubmit.value) return
  submitting.value = true
  error.value = ''
  try {
    success.value = await submitPublicCollaborationRequest({ ...form })
  } catch (err) {
    error.value = err?.message || 'ثبت درخواست انجام نشد؛ لطفاً اطلاعات را بررسی و دوباره تلاش کنید.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.collaboration-page { min-height: 100vh; padding-bottom: calc(6rem + env(safe-area-inset-bottom)); background: var(--ds-color-bg-page); color: var(--ds-color-text-primary); }
.collaboration-hero { padding-bottom: 1.6rem; background: radial-gradient(ellipse at 12% 0%, color-mix(in srgb, var(--ds-color-action-accent) 12%, transparent), transparent 43%), var(--ds-color-surface-raised); border-bottom: 1px solid var(--ds-color-border); }
.collaboration-hero__pills { display: flex; flex-wrap: wrap; justify-content: center; gap: .5rem; padding: 0 1rem; }
.collaboration-hero__pills span { display: inline-flex; align-items: center; gap: .4rem; min-height: 34px; padding: .35rem .7rem; border: 1px solid var(--ds-color-border); border-radius: 999px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font-size: .79rem; font-weight: 700; }
.collaboration-body { width: min(920px, calc(100% - 1.5rem)); margin: 1.4rem auto 2.5rem; display: grid; gap: 1rem; }
.collaboration-rules, .collaboration-form-card, .collaboration-success { padding: clamp(1rem, 3.5vw, 1.6rem); border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-lg); background: var(--ds-color-surface-raised); box-shadow: var(--ds-shadow-sm); }
.collaboration-section-heading { display: flex; align-items: flex-start; gap: .75rem; margin-bottom: 1rem; }
.collaboration-step { flex: none; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; background: color-mix(in srgb, var(--ds-color-action-primary) 11%, var(--ds-color-surface-raised)); color: var(--ds-color-action-primary); font-size: .86rem; font-weight: 900; }
.collaboration-step--accent { background: color-mix(in srgb, var(--ds-color-action-accent) 15%, var(--ds-color-surface-raised)); color: var(--ds-color-action-accent); }
.collaboration-section-heading h2 { margin: 0; font-size: 1.1rem; font-weight: 900; }
.collaboration-section-heading p { margin: .25rem 0 0; color: var(--ds-color-text-secondary); font-size: .83rem; line-height: 1.8; }
.rule-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .65rem; }
.rule-card { display: flex; align-items: flex-start; gap: .6rem; min-height: 126px; padding: .8rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); }
.rule-number { color: var(--ds-color-action-accent); font-size: .73rem; font-weight: 900; }
.rule-card h3 { margin: 0 0 .3rem; font-size: .84rem; }
.rule-card p { margin: 0; color: var(--ds-color-text-secondary); font-size: .75rem; line-height: 1.8; }
.collaboration-kind-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .65rem; margin-bottom: 1.35rem; }
.kind-option { position: relative; display: flex; align-items: center; gap: .65rem; min-height: 72px; padding: .75rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); color: var(--ds-color-text-primary); text-align: right; cursor: pointer; }
.kind-option > svg:first-child { flex: none; color: var(--ds-color-action-primary); }
.kind-option span { display: grid; gap: .2rem; }
.kind-option strong { font-size: .81rem; }
.kind-option small { color: var(--ds-color-text-secondary); font-size: .7rem; line-height: 1.6; }
.kind-option.selected { border-color: var(--ds-color-action-primary); background: color-mix(in srgb, var(--ds-color-action-primary) 6%, var(--ds-color-surface-raised)); box-shadow: 0 0 0 2px color-mix(in srgb, var(--ds-color-action-primary) 12%, transparent); }
.kind-option__check { position: absolute; top: .45rem; left: .45rem; color: var(--ds-color-action-primary); }
.collaboration-form { display: grid; gap: .9rem; }
.form-section-label { display: flex; align-items: center; gap: .75rem; margin-top: .3rem; color: var(--ds-color-text-primary); font-size: .82rem; font-weight: 900; }
.form-section-label i { flex: 1; height: 1px; background: var(--ds-color-border); }
.collaboration-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .75rem; }
.collab-field { display: grid; gap: .38rem; min-width: 0; color: var(--ds-color-text-secondary); font-size: .78rem; font-weight: 700; }
.collab-field > span b, .weekday-field legend b { color: var(--ds-color-action-accent); }
.collab-field > span small { color: var(--ds-color-text-muted); font-weight: 500; }
.collab-field .input { width: 100%; min-height: 46px; padding: .65rem .75rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-sm); background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; }
.collab-field textarea.input { resize: vertical; line-height: 1.8; }
.collab-field .input:focus-visible, .collab-consent input:focus-visible, .weekday-chip input:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
.collab-field--wide { grid-column: 1 / -1; }
.weekday-field { margin: 0; padding: 0; border: 0; }
.weekday-field legend { margin-bottom: .5rem; color: var(--ds-color-text-secondary); font-size: .78rem; font-weight: 700; }
.weekday-list { display: flex; flex-wrap: wrap; gap: .45rem; }
.weekday-chip input { position: absolute; opacity: 0; pointer-events: none; }
.weekday-chip span { display: grid; place-items: center; min-height: 40px; padding: .4rem .7rem; border: 1px solid var(--ds-color-border); border-radius: 999px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); cursor: pointer; font-size: .75rem; }
.weekday-chip.checked span { border-color: var(--ds-color-action-primary); background: color-mix(in srgb, var(--ds-color-action-primary) 9%, var(--ds-color-surface-raised)); color: var(--ds-color-action-primary); font-weight: 800; }
.collab-consent { display: flex; align-items: flex-start; gap: .6rem; padding: .85rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font-size: .76rem; line-height: 1.8; cursor: pointer; }
.collab-consent input { flex: none; width: 18px; height: 18px; margin-top: .1rem; accent-color: var(--ds-color-action-primary); }
.collab-feedback { margin: 0; font-size: .82rem; line-height: 1.7; }
.collab-feedback--error { color: var(--ds-color-status-danger); }
.collab-submit { display: flex; align-items: center; justify-content: center; gap: .5rem; min-height: 50px; border: 0; border-radius: var(--ds-radius-md); background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); font: inherit; font-weight: 900; cursor: pointer; }
.collab-submit:disabled { opacity: .5; cursor: not-allowed; }
.collab-submit:focus-visible, .kind-option:focus-visible, .collab-back-link:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 3px; }
.collab-privacy { margin: -.35rem 0 0; color: var(--ds-color-text-muted); font-size: .71rem; text-align: center; }
.collaboration-success { display: grid; justify-items: center; gap: .7rem; padding: 3rem 1.5rem; text-align: center; }
.success-icon { display: grid; place-items: center; width: 62px; height: 62px; border-radius: 50%; background: color-mix(in srgb, var(--ds-color-status-success) 13%, var(--ds-color-surface-raised)); color: var(--ds-color-status-success); }
.success-eyebrow { margin: 0; color: var(--ds-color-action-primary); font-size: .78rem; font-weight: 900; }
.collaboration-success h2 { margin: 0; font-size: 1.25rem; }
.collaboration-success > p:not(.success-eyebrow) { max-width: 34rem; margin: 0; color: var(--ds-color-text-secondary); font-size: .87rem; line-height: 1.9; }
.collab-back-link { display: inline-flex; align-items: center; justify-content: center; gap: .5rem; min-height: 44px; padding: .6rem .9rem; border-radius: var(--ds-radius-md); color: var(--ds-color-action-primary); font-weight: 800; text-decoration: none; }
@media (max-width: 720px) { .rule-grid { grid-template-columns: 1fr; } .rule-card { min-height: 0; } .collaboration-kind-grid { grid-template-columns: 1fr; } .kind-option { min-height: 64px; } }
@media (max-width: 520px) { .collaboration-fields { grid-template-columns: 1fr; } .collab-field--wide { grid-column: auto; } .collaboration-body { width: min(100% - 1rem, 920px); margin-top: .8rem; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; } }
</style>
