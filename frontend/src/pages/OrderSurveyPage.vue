<template>
  <div class="customer-page survey-page" dir="rtl">
    <CustomerPageHeader
      eyebrow="تجربهٔ شما"
      :title="editMode ? 'ویرایش نظرهای شما' : 'نظرتان برای ما مهم است'"
      :subtitle="editMode ? 'امتیازها و توضیحات قبلی را اصلاح کنید؛ نظرهای ویرایش‌شده دوباره بررسی می‌شوند.' : 'با چند امتیاز کوتاه کمک می‌کنید کیفیت غذا و پذیرایی بهتر شود.'"
      hero-class="survey-hero"
      fallback-href="/customer/orders"
    >
      <template #eyebrow-icon><MessageCircle :size="15" aria-hidden="true" /></template>
      <template #action>
        <a v-if="!hasToken && !hasInvitation" class="survey-account-link" href="/customer/dashboard">حساب من</a>
        <span v-else class="customer-page-header__spacer" aria-hidden="true"></span>
      </template>
      <div v-if="survey && (!survey.answered || editMode)" class="survey-order-line">
        <span class="survey-order-icon"><ReceiptText :size="17" aria-hidden="true" /></span>
        <span>سفارش <strong>{{ survey.order_code }}</strong><small v-if="survey.customer_name">{{ survey.customer_name }}</small></span>
      </div>
      <div v-if="survey && (!survey.answered || editMode) && survey.items?.length" class="survey-progress" aria-live="polite">
        <div class="survey-progress__meta">
          <span>پیشرفت ثبت نظر</span>
          <strong>{{ formatNumber(completedItems) }} از {{ formatNumber(survey.items.length) }} غذا</strong>
        </div>
        <div class="survey-progress__track" role="progressbar" :aria-valuenow="completedItems" :aria-valuemin="0" :aria-valuemax="survey.items.length" aria-label="پیشرفت ثبت نظر غذاها">
          <span :style="{ width: progressPercent + '%' }"></span>
        </div>
      </div>
    </CustomerPageHeader>

    <main class="customer-page__body survey-body">
      <section v-if="loading" class="customer-glass-card survey-state" role="status">
        <span class="survey-spinner" aria-hidden="true"></span>
        <p>در حال آماده‌سازی نظرسنجی…</p>
      </section>

      <section v-else-if="loadError" class="customer-glass-card survey-state survey-state--error" role="alert">
        <span class="survey-state__icon"><CircleAlert :size="24" /></span>
        <h2>{{ loadTitle }}</h2>
        <p>{{ loadError }}</p>
        <a v-if="hasInvitation && !hasCustomerSession" :href="loginHref" class="survey-primary-link">ورود به حساب برای ثبت نظر</a>
        <a v-else href="/customer/orders" class="survey-secondary-link">رفتن به سفارش‌های من</a>
      </section>

      <section v-else-if="(survey?.answered && !editMode) || submitted" class="customer-glass-card survey-state survey-state--success" role="status">
        <span class="survey-state__icon"><CheckCircle2 :size="28" /></span>
        <p class="survey-success-eyebrow">{{ editMode ? 'تغییرات ذخیره شد' : 'ثبت شد' }}</p>
        <h2>{{ editMode ? 'نظرهای شما به‌روزرسانی شد' : 'ممنون که تجربه‌تان را با ما به اشتراک گذاشتید' }}</h2>
        <p>{{ editMode ? 'تغییرات برای بررسی دوباره به تیم ویدرخت رسید.' : 'نظر شما ثبت شد و امتیاز غذاها پس از بررسی در صفحهٔ محصولات نمایش داده می‌شود.' }}</p>
        <a href="/customer/orders" class="survey-primary-link">بازگشت به سفارش‌ها</a>
      </section>

      <form v-else-if="survey" class="survey-form" @submit.prevent="submitSurvey">
        <section v-if="survey.order_questions?.length" class="customer-glass-card survey-section">
          <div class="survey-section__heading">
            <span class="survey-section__icon"><ClipboardList :size="19" /></span>
            <div><h2>تجربهٔ کلی سفارش</h2><p>پاسخ به این پرسش‌ها اختیاری است.</p></div>
          </div>
          <CustomerSurveyQuestion
            v-for="question in survey.order_questions"
            :key="question.name"
            v-model="answers[answerKey(question)]"
            :question="question"
            :group-name="answerKey(question)"
            :feature-choices="surveyFeatureChoices(serviceRating)"
          />
        </section>

        <section v-if="survey.items?.length" class="survey-section survey-products">
          <div class="survey-section__heading survey-products__heading">
            <span class="survey-section__icon"><Utensils :size="19" /></span>
            <div><h2>غذاهای سفارش</h2><p>برای هر غذا امتیاز بدهید یا موردی را که نچشیده‌اید رد کنید.</p></div>
          </div>

          <article v-for="(item, index) in survey.items" :key="item.order_item" class="customer-glass-card survey-item" :class="{ 'survey-item--skipped': feedback[item.order_item]?.skipped }">
            <div class="survey-item__top">
              <span class="survey-item__index">{{ formatNumber(index + 1) }}</span>
              <img v-if="item.image" class="survey-item__image" :src="item.image" :alt="item.title" loading="lazy" />
              <span v-else class="survey-item__image survey-item__image--empty"><Utensils :size="23" aria-hidden="true" /></span>
              <div class="survey-item__identity">
                <h3>{{ item.title }}</h3>
                <p>تعداد {{ formatNumber(item.qty) }}</p>
              </div>
              <span v-if="feedback[item.order_item]?.score" class="survey-item__score-pill">{{ formatNumber(feedback[item.order_item].score) }} از ۱۰</span>
              <span v-else-if="feedback[item.order_item]?.skipped" class="survey-item__skipped-pill">نچشیده‌ام</span>
            </div>

            <div v-if="!feedback[item.order_item]?.skipped" class="survey-item__content">
              <fieldset class="survey-rating">
                <legend>از این غذا چقدر راضی بودید؟ <span>امتیاز ۱ یعنی خیلی ضعیف و ۱۰ یعنی عالی</span></legend>
                <div class="survey-rating__scale" role="radiogroup" :aria-label="'امتیاز ' + item.title">
                  <label v-for="score in 10" :key="score" class="survey-rating__option" :class="{ selected: Number(feedback[item.order_item]?.score) === score, 'is-low': score <= 3, 'is-mid': score >= 4 && score <= 6, 'is-high': score >= 7 }">
                    <input
                      type="radio"
                      :name="'item-score-' + item.order_item"
                      :value="score"
                      :checked="Number(feedback[item.order_item]?.score) === score"
                      @change="setScore(item, score)"
                    />
                    <span>{{ formatNumber(score) }}</span>
                  </label>
                </div>
                <div class="survey-rating__labels"><span>نیاز به بهبود</span><span>عالی</span></div>
              </fieldset>

              <div v-if="feedback[item.order_item]?.score" class="survey-item__details">
                <CustomerSurveyQuestion
                  v-for="question in item.questions || []"
                  :key="question.name"
                  v-model="answers[answerKey(question, item)]"
                  :question="question"
                  :group-name="answerKey(question, item)"
                  :feature-choices="surveyFeatureChoices(feedback[item.order_item].score)"
                />
                <label class="survey-comment">
                  <span>اگر توضیحی دارید، برایمان بنویسید <small>اختیاری</small></span>
                  <textarea v-model.trim="feedback[item.order_item].comment" rows="3" maxlength="2000" :aria-label="'توضیح دربارهٔ ' + item.title" placeholder="چه چیزی را دوست داشتید یا چه چیزی بهتر می‌شود؟"></textarea>
                </label>
              </div>
              <button v-if="!feedback[item.order_item]?.score && !feedback[item.order_item]?.savedReview" type="button" class="survey-skip" @click="skipItem(item)">
                این غذا را نچشیده‌ام
                <ChevronLeft :size="16" aria-hidden="true" />
              </button>
            </div>
            <button v-else type="button" class="survey-unskip" @click="unskipItem(item)">می‌خواهم برای این غذا نظر بدهم</button>
          </article>
        </section>

        <section class="customer-glass-card survey-section survey-service">
          <div class="survey-section__heading">
            <span class="survey-section__icon survey-section__icon--warm"><HeartHandshake :size="19" /></span>
            <div><h2>تجربهٔ پذیرایی و خدمات</h2><p>امتیاز دادن اختیاری است؛ اگر دوست داشتید برای تیم ما هم بنویسید.</p></div>
          </div>
          <fieldset class="survey-rating survey-rating--service">
            <legend>خدمات این سفارش را چطور ارزیابی می‌کنید؟ <span>از ۱ تا ۱۰</span></legend>
            <div class="survey-rating__scale" role="radiogroup" aria-label="امتیاز خدمت‌رسانی">
              <label v-for="score in 10" :key="score" class="survey-rating__option" :class="{ selected: Number(serviceRating) === score, 'is-low': score <= 3, 'is-mid': score >= 4 && score <= 6, 'is-high': score >= 7 }">
                <input type="radio" name="service-score" :value="score" :checked="Number(serviceRating) === score" @change="setServiceRating(score)" />
                <span>{{ formatNumber(score) }}</span>
              </label>
            </div>
            <div class="survey-rating__labels"><span>ضعیف</span><span>عالی</span></div>
          </fieldset>
          <label class="survey-comment survey-comment--general">
            <span>پیام یا توضیح کلی <small>اختیاری</small></span>
            <textarea v-model.trim="generalComment" rows="3" maxlength="2000" placeholder="هر نکته‌ای که به بهترشدن تجربه کمک می‌کند…"></textarea>
          </label>
        </section>

        <p v-if="submitError" class="survey-form-error" role="alert"><CircleAlert :size="17" />{{ submitError }}</p>
        <div class="survey-submit-row">
          <p>با ثبت نظر، پاسخ‌ها برای بررسی تیم ویدرخت ارسال می‌شوند.</p>
          <button type="submit" class="survey-submit" :disabled="submitting || !hasAnyRating">
            {{ submitting ? 'در حال ثبت…' : 'ثبت نظرها' }}
            <Send :size="17" aria-hidden="true" />
          </button>
          <span v-if="!hasAnyRating" class="survey-submit-hint">برای ثبت، دست‌کم به یک غذا یا خدمات امتیاز بدهید.</span>
        </div>
      </form>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  CheckCircle2, ChevronLeft, CircleAlert, ClipboardList, HeartHandshake,
  MessageCircle, ReceiptText, Send, Utensils,
} from 'lucide-vue-next'
import CustomerPageHeader from '@/components/customer/CustomerPageHeader.vue'
import CustomerSurveyQuestion from '@/components/customer/CustomerSurveyQuestion.vue'
import { getMyOrderSurvey, getPublicSurvey, submitPublicSurvey } from '@/utils/api'
import { hasCustomerSession as hasCustomerSessionAuth } from '@/utils/customerAuth'
import { buildCustomerSurveySubmission, hasCustomerSurveyRating, surveyFeatureChoices } from '@/utils/customerSurvey'

const params = new URLSearchParams(window.location.search)
const token = String(params.get('token') || '').trim()
const invitation = String(params.get('invitation') || '').trim()
const hasToken = Boolean(token)
const hasInvitation = Boolean(invitation)
const editMode = params.get('edit') === '1' && hasInvitation && !hasToken
const loading = ref(true)
const submitting = ref(false)
const submitted = ref(false)
const loadError = ref('')
const loadTitle = ref('نظرسنجی در دسترس نیست')
const submitError = ref('')
const survey = ref(null)
const answers = reactive({})
const feedback = reactive({})
const serviceRating = ref(0)
const generalComment = ref('')
const hasAnyRating = computed(() => hasCustomerSurveyRating(serviceRating.value, feedback, answers, survey.value?.order_questions || []))
const completedItems = computed(() => (survey.value?.items || []).filter((item) => feedback[item.order_item]?.skipped || Number(feedback[item.order_item]?.score)).length)
const progressPercent = computed(() => survey.value?.items?.length ? Math.round((completedItems.value / survey.value.items.length) * 100) : 0)
const hasCustomerSession = computed(() => hasCustomerSessionAuth())
const loginHref = computed(() => '/customer/login?redirect=' + encodeURIComponent(window.location.pathname + window.location.search))

function formatNumber(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}
function answerKey(question, item = null) {
  return String(question.name) + (item ? '|' + item.order_item : '')
}
function setScore(item, score) {
  const current = feedback[item.order_item] || { score: 0, comment: '', skipped: false }
  feedback[item.order_item] = { ...current, score, skipped: false }
  for (const question of item.questions || []) {
    if (question.answer_type !== 'ویژگی خوب/بد') continue
    const key = answerKey(question, item)
    if (score >= 7 && answers[key] === 'نیاز به بهبود') delete answers[key]
    if (score <= 3 && answers[key] === 'نقطه قوت') delete answers[key]
  }
}
function setServiceRating(score) {
  serviceRating.value = score
  for (const question of survey.value?.order_questions || []) {
    if (question.answer_type !== 'ویژگی خوب/بد') continue
    const key = answerKey(question)
    if (score >= 7 && answers[key] === 'نیاز به بهبود') delete answers[key]
    if (score <= 3 && answers[key] === 'نقطه قوت') delete answers[key]
  }
}
function skipItem(item) {
  feedback[item.order_item] = { score: 0, comment: '', skipped: true }
  for (const question of item.questions || []) delete answers[answerKey(question, item)]
}
function unskipItem(item) {
  feedback[item.order_item] = { score: 0, comment: '', skipped: false }
}
function normalizeSurvey(payload) {
  survey.value = payload || null
  if (payload?.answered && !editMode) return
  for (const item of payload?.items || []) {
    const saved = item.saved_review || null
    feedback[item.order_item] = {
      score: Number(saved?.score_10 || 0),
      comment: saved?.comment || '',
      skipped: false,
      savedReview: Boolean(saved),
    }
  }
  for (const answer of payload?.answers || []) {
    const key = String(answer.question_id || '') + (answer.order_item ? '|' + answer.order_item : '')
    if (key) answers[key] = answer.value
  }
  serviceRating.value = Number(payload?.service_rating || 0)
  generalComment.value = payload?.comment || ''
}
async function loadSurvey() {
  loading.value = true
  loadError.value = ''
  if (!hasToken && !hasInvitation) {
    loadError.value = 'این صفحه فقط با پیوند دعوت معتبر یا از حساب مشتری باز می‌شود.'
    loading.value = false
    return
  }
  if (hasInvitation && !hasToken && !hasCustomerSession.value) {
    loadTitle.value = 'برای ثبت نظر وارد حساب شوید'
    loadError.value = 'دعوت حساب مشتری به سفارش واقعی شما متصل است. برای حفظ حریم خصوصی، ابتدا وارد حساب شوید.'
    loading.value = false
    return
  }
  try {
    const payload = hasToken ? await getPublicSurvey(token) : await getMyOrderSurvey(invitation, { edit: editMode })
    if (!payload?.valid) {
      loadTitle.value = payload?.expired ? 'مهلت نظرسنجی تمام شده است' : 'نظرسنجی در دسترس نیست'
      loadError.value = payload?.message || 'این سفارش فعلاً امکان ثبت نظر ندارد.'
    } else normalizeSurvey(payload)
  } catch (error) {
    loadTitle.value = hasInvitation && !hasCustomerSession.value ? 'برای ثبت نظر وارد حساب شوید' : 'دریافت نظرسنجی ناموفق بود'
    loadError.value = error?.message || 'لطفاً چند لحظه دیگر دوباره تلاش کنید.'
  } finally {
    loading.value = false
  }
}
async function submitSurvey() {
  if (submitting.value || !hasAnyRating.value || !survey.value) return
  submitting.value = true
  submitError.value = ''
  try {
    const payload = buildCustomerSurveySubmission({
      survey: survey.value,
      answers,
      feedback,
      serviceRating: serviceRating.value,
      generalComment: generalComment.value,
      token: hasToken ? token : '',
      invitation: hasToken ? '' : invitation,
      edit: editMode,
    })
    await submitPublicSurvey(payload)
    submitted.value = true
  } catch (error) {
    submitError.value = error?.message || 'ثبت نظرسنجی انجام نشد؛ پاسخ‌هایتان را بررسی کنید و دوباره تلاش کنید.'
  } finally {
    submitting.value = false
  }
}

onMounted(loadSurvey)
</script>

<style scoped>
.survey-page { min-height: 100dvh; padding-bottom: max(1.5rem, env(safe-area-inset-bottom)); background: var(--ds-color-bg-page); color: var(--ds-color-text-primary); }
.survey-hero { padding-bottom: 1rem; }
.survey-account-link, .survey-secondary-link { min-height: 44px; display: inline-flex; align-items: center; justify-content: center; padding: .55rem .85rem; border: 1px solid var(--ds-color-border); border-radius: 999px; color: var(--ds-color-action-primary); text-decoration: none; font-size: .8rem; font-weight: 750; background: var(--ds-color-surface); }
.survey-order-line { display: flex; align-items: center; gap: .65rem; margin: .2rem 1rem .9rem; padding: .75rem .85rem; border: 1px solid color-mix(in srgb, var(--ds-color-action-primary) 15%, var(--ds-color-border)); border-radius: 16px; background: var(--ds-color-surface); }
.survey-order-icon { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 12px; background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); }
.survey-order-line > span:last-child { display: grid; gap: .15rem; color: var(--ds-color-text-muted); font-size: .78rem; }
.survey-order-line strong { color: var(--ds-color-text-primary); direction: ltr; }
.survey-order-line small { font-size: .74rem; }
.survey-progress { margin: 0 1rem; padding: .7rem .85rem; border-radius: 14px; background: var(--ds-color-action-accent-soft); }
.survey-progress__meta { display: flex; justify-content: space-between; gap: .5rem; margin-bottom: .45rem; color: var(--ds-color-text-secondary); font-size: .76rem; }
.survey-progress__meta strong { color: var(--ds-color-text-primary); }
.survey-progress__track { height: 6px; overflow: hidden; border-radius: 999px; background: color-mix(in srgb, var(--ds-color-action-accent) 20%, white); }
.survey-progress__track span { display: block; height: 100%; border-radius: inherit; background: var(--ds-color-action-accent); transition: width var(--ds-motion-normal) var(--ds-motion-ease); }
.survey-body { display: grid; gap: .9rem; padding-top: .25rem; }
.survey-state { display: grid; justify-items: center; gap: .55rem; padding: 2rem 1.2rem; text-align: center; }
.survey-state h2, .survey-state p { margin: 0; }
.survey-state p { max-width: 520px; color: var(--ds-color-text-muted); font-size: .88rem; line-height: 1.9; }
.survey-state h2 { font-size: 1.15rem; }
.survey-state__icon { display: grid; width: 58px; height: 58px; margin-bottom: .25rem; place-items: center; border-radius: 20px; background: var(--ds-color-status-danger-soft); color: var(--ds-color-status-danger); }
.survey-state--success .survey-state__icon { background: var(--ds-color-status-success-soft); color: var(--ds-color-status-success); }
.survey-success-eyebrow { color: var(--ds-color-status-success) !important; font-weight: 800; }
.survey-primary-link, .survey-submit { min-height: 48px; display: inline-flex; align-items: center; justify-content: center; gap: .55rem; margin-top: .45rem; padding: .7rem 1rem; border: 0; border-radius: 14px; background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); text-decoration: none; font: inherit; font-weight: 800; cursor: pointer; }
.survey-form { display: grid; gap: .85rem; }
.survey-section { display: grid; gap: .8rem; padding: 1rem; }
.survey-section__heading { display: flex; align-items: flex-start; gap: .7rem; }
.survey-section__icon { display: grid; flex: 0 0 40px; width: 40px; height: 40px; place-items: center; border-radius: 13px; background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); }
.survey-section__icon--warm { background: var(--ds-color-action-accent-soft); color: var(--ds-color-action-accent-foreground); }
.survey-section__heading h2 { margin: 0; font-size: .98rem; }
.survey-section__heading p { margin: .2rem 0 0; color: var(--ds-color-text-muted); font-size: .78rem; line-height: 1.7; }
.survey-products { display: grid; gap: .7rem; }
.survey-products__heading { padding: .2rem .15rem; }
.survey-item { overflow: hidden; padding: .95rem; transition: opacity var(--ds-motion-fast) ease, border-color var(--ds-motion-fast) ease; }
.survey-item--skipped { opacity: .78; }
.survey-item__top { display: flex; align-items: center; gap: .65rem; min-width: 0; }
.survey-item__index { display: grid; flex: 0 0 28px; width: 28px; height: 28px; place-items: center; border-radius: 9px; background: var(--ds-color-surface-muted); color: var(--ds-color-text-muted); font-size: .72rem; font-weight: 800; }
.survey-item__image { flex: 0 0 62px; width: 62px; height: 62px; border-radius: 16px; object-fit: cover; background: var(--ds-color-surface-muted); }
.survey-item__image--empty { display: grid; place-items: center; color: var(--ds-color-action-primary); }
.survey-item__identity { flex: 1; min-width: 0; }
.survey-item__identity h3 { overflow: hidden; margin: 0; text-overflow: ellipsis; white-space: nowrap; font-size: .94rem; }
.survey-item__identity p { margin: .25rem 0 0; color: var(--ds-color-text-muted); font-size: .75rem; }
.survey-item__score-pill, .survey-item__skipped-pill { flex: 0 0 auto; padding: .35rem .55rem; border-radius: 999px; background: var(--ds-color-action-accent-soft); color: var(--ds-color-text-primary); font-size: .72rem; font-weight: 800; }
.survey-item__skipped-pill { background: var(--ds-color-surface-muted); color: var(--ds-color-text-muted); }
.survey-item__content { display: grid; gap: .5rem; margin-top: .9rem; }
.survey-rating { min-width: 0; margin: 0; padding: 0; border: 0; }
.survey-rating legend { display: grid; gap: .2rem; margin-bottom: .65rem; font-size: .84rem; font-weight: 800; }
.survey-rating legend span { color: var(--ds-color-text-muted); font-size: .73rem; font-weight: 500; }
.survey-rating__scale { display: grid; grid-template-columns: repeat(10, minmax(0, 1fr)); gap: .35rem; }
.survey-rating__option { position: relative; display: grid; min-height: 42px; place-items: center; border: 1px solid var(--ds-color-border); border-radius: 11px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font-size: .78rem; font-weight: 800; cursor: pointer; transition: border-color var(--ds-motion-fast), background var(--ds-motion-fast), transform var(--ds-motion-fast); }
.survey-rating__option input { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0; cursor: pointer; }
.survey-rating__option:has(input:focus-visible) { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; z-index: 1; }
.survey-rating__option.selected { border-color: var(--ds-color-action-accent); background: var(--ds-color-action-accent-soft); color: var(--ds-color-text-primary); transform: translateY(-2px); }
.survey-rating__labels { display: flex; justify-content: space-between; margin-top: .4rem; color: var(--ds-color-text-muted); font-size: .69rem; }
.survey-item__details { display: grid; gap: .7rem; margin-top: .3rem; }
.survey-comment { display: grid; gap: .45rem; padding-top: .75rem; border-top: 1px solid var(--ds-color-border); color: var(--ds-color-text-secondary); font-size: .82rem; font-weight: 750; }
.survey-comment small { margin-inline-start: .25rem; color: var(--ds-color-text-muted); font-weight: 500; }
.survey-comment textarea { width: 100%; box-sizing: border-box; resize: vertical; border: 1px solid var(--ds-color-border); border-radius: 13px; padding: .75rem; background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; font-size: .85rem; line-height: 1.8; }
.survey-comment textarea:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
.survey-comment--general { border-top: 0; padding-top: .2rem; }
.survey-skip, .survey-unskip { display: inline-flex; align-items: center; justify-self: start; gap: .35rem; min-height: 44px; padding: .45rem .2rem; border: 0; background: none; color: var(--ds-color-text-muted); font: inherit; font-size: .77rem; cursor: pointer; }
.survey-skip:hover, .survey-unskip { color: var(--ds-color-action-primary); }
.survey-unskip { margin-top: .4rem; font-weight: 750; }
.survey-submit-row { position: sticky; z-index: var(--ds-z-sticky); bottom: 0; display: grid; grid-template-columns: 1fr auto; align-items: center; gap: .4rem .85rem; margin: 0 -.1rem; padding: .75rem; padding-bottom: max(.75rem, env(safe-area-inset-bottom)); border: 1px solid var(--ds-color-border); border-radius: 18px 18px 0 0; background: color-mix(in srgb, var(--ds-color-surface) 94%, transparent); box-shadow: var(--ds-shadow-md); backdrop-filter: blur(16px); }
.survey-submit-row p { margin: 0; color: var(--ds-color-text-muted); font-size: .72rem; line-height: 1.65; }
.survey-submit { grid-row: span 2; min-width: 150px; margin: 0; }
.survey-submit:disabled { opacity: .52; cursor: not-allowed; }
.survey-submit-hint { color: var(--ds-color-status-warning); font-size: .72rem; }
.survey-form-error { display: flex; align-items: center; gap: .5rem; margin: 0; color: var(--ds-color-status-danger); font-size: .83rem; }
.survey-spinner { width: 27px; height: 27px; border: 3px solid var(--ds-color-border); border-top-color: var(--ds-color-action-accent); border-radius: 50%; animation: survey-spin .8s linear infinite; }
@keyframes survey-spin { to { transform: rotate(360deg); } }
@media (min-width: 800px) {
  .survey-page { max-width: 900px; margin: 0 auto; }
  .survey-section, .survey-item { padding: 1.15rem 1.25rem; }
  .survey-item__image { width: 72px; height: 72px; }
}
@media (max-width: 480px) {
  .survey-rating__scale { gap: .2rem; }
  .survey-rating__option { min-height: 38px; border-radius: 9px; font-size: .7rem; }
  .survey-submit-row { grid-template-columns: 1fr; }
  .survey-submit { grid-row: auto; width: 100%; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: .01ms !important; }
}
</style>
