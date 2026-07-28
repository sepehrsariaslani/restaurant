<template>
  <ManagementPageScaffold title="نظرسنجی هوشمند" subtitle="نظرسنجی به ازای هر سفارش، سوالات اختصاصی و هشدار لحظه‌ای نارضایتی">
    <template #actions>
      <button type="button" class="secondary-btn" @click="reload" :disabled="loadingAny">
        {{ loadingAny ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
      </button>
    </template>

    <div class="totals-grid boot-kpis">
      <div class="total-box"><small>پاسخ‌های این بازه</small><strong>{{ formatQty(responses.length) }}</strong></div>
      <div class="total-box"><small>میانگین امتیاز</small><strong :class="avgRating && avgRating <= 3 ? 'warn-text' : 'ok-text'">{{ avgRating ? avgRating + ' / ۵' : '—' }}</strong></div>
      <div class="total-box" :class="{ 'warn-border': dissatisfiedCount > 0 }">
        <small>نارضایتی (≤ آستانه هشدار)</small><strong :class="dissatisfiedCount > 0 ? 'warn-text' : 'ok-text'">{{ formatQty(dissatisfiedCount) }}</strong>
      </div>
      <div class="total-box"><small>سوالات فعال</small><strong>{{ formatQty(activeQuestionsCount) }}</strong></div>
    </div>

    <ManagementSurfaceCard title="سوالات نظرسنجی" subtitle="این سوالات در صفحه عمومی نظرسنجی سفارش از مشتری پرسیده می‌شوند">
      <p class="muted hint-line">
        لینک عمومی نظرسنجی برای مشتریان:
        <code class="link-code">{{ surveyPublicUrl }}</code>
        — کد سفارش و موبایل مشتری به‌صورت خودکار اعتبارسنجی می‌شود؛ می‌توانید با پارامترهای <code class="link-code">?order=...&mobile=...</code> لینک اختصاصی هر سفارش را بسازید.
      </p>
      <div class="toolbar">
        <button type="button" class="primary-btn" @click="openQuestionForm()">سوال جدید</button>
        <label class="check-row"><input type="checkbox" v-model="showInactive" @change="loadQuestions" /> نمایش غیرفعال‌ها</label>
      </div>
      <p class="muted" v-if="questionsLoading">در حال دریافت سوالات...</p>
      <div v-else-if="questions.length" class="table-wrap">
        <table class="data-table">
          <thead><tr><th>#</th><th>سوال</th><th>نوع پاسخ</th><th>ترتیب</th><th>وضعیت</th><th></th></tr></thead>
          <tbody>
            <tr v-for="(q, i) in questions" :key="q.name" :class="{ inactive: !q.is_active }">
              <td>{{ formatQty(i + 1) }}</td>
              <td><strong>{{ q.question }}</strong></td>
              <td><span class="pill">{{ q.answer_type }}</span></td>
              <td>{{ formatQty(q.sort_order) }}</td>
              <td><span class="pill" :class="{ ok: q.is_active, warn: !q.is_active }">{{ q.is_active ? 'فعال' : 'غیرفعال' }}</span></td>
              <td class="row-actions">
                <button type="button" class="tertiary-btn" @click="openQuestionForm(q)">ویرایش</button>
                <button type="button" class="tertiary-btn danger" @click="removeQuestion(q)">حذف</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted" v-else-if="!questionsLoading">هنوز سوالی تعریف نشده است؛ با «سوال جدید» شروع کنید.</p>
      <p class="error" v-if="questionsError">{{ questionsError }}</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="پاسخ‌های نظرسنجی" subtitle="نظرات ثبت‌شده مشتریان؛ نارضایتی‌ها بلافاصله به مدیران هشدار داده می‌شوند">
      <div class="toolbar">
        <label class="date-label">از تاریخ<input class="input" type="date" v-model="responseFilters.date_from" @change="loadResponses" /></label>
        <label class="date-label">تا تاریخ<input class="input" type="date" v-model="responseFilters.date_to" @change="loadResponses" /></label>
        <input class="input survey-search" v-model.trim="responseFilters.search" placeholder="جستجو: نام، موبایل، کد سفارش، متن نظر..." @keyup.enter="loadResponses" />
        <select class="input rating-select" v-model="responseFilters.min_rating" @change="loadResponses">
          <option :value="0">از هر امتیازی</option>
          <option :value="1">۱ به بالا</option>
          <option :value="2">۲ به بالا</option>
          <option :value="3">۳ به بالا</option>
          <option :value="4">۴ به بالا</option>
          <option :value="5">فقط ۵</option>
        </select>
        <select class="input rating-select" v-model="responseFilters.max_rating" @change="loadResponses">
          <option :value="0">تا ۵</option>
          <option :value="5">تا ۵</option>
          <option :value="4">تا ۴</option>
          <option :value="3">تا ۳</option>
          <option :value="2">تا ۲</option>
          <option :value="1">تا ۱ (فقط ناراضی)</option>
        </select>
        <label class="check-row"><input type="checkbox" v-model="onlyDissatisfied" /> فقط ناراضی‌ها</label>
        <button type="button" class="secondary-btn" @click="loadResponses" :disabled="responsesLoading">{{ responsesLoading ? '...' : 'جستجو' }}</button>
      </div>
      <p class="muted" v-if="responsesLoading">در حال دریافت پاسخ‌ها...</p>
      <div v-else-if="filteredResponses.length" class="table-wrap">
        <table class="data-table">
          <thead><tr><th>سفارش</th><th>مشتری</th><th>امتیاز کلی</th><th>پاسخ‌ها</th><th>توضیح</th><th>زمان</th></tr></thead>
          <tbody>
            <tr v-for="r in filteredResponses" :key="r.name" :class="{ 'alert-row': r.dissatisfaction_alerted }">
              <td><strong>{{ r.sales_order || r.order_code }}</strong></td>
              <td>{{ r.customer_name || '—' }}<br><small class="muted">{{ r.mobile }}</small></td>
              <td>
                <span class="stars-mini">{{ starString(r.overall_rating) }}</span>
                <span class="pill" :class="{ ok: r.overall_rating >= 4, warn: r.overall_rating <= 2 }">{{ formatQty(r.overall_rating) }}</span>
                <span v-if="r.dissatisfaction_alerted" class="pill warn">هشدار شد</span>
              </td>
              <td class="answers-cell">
                <template v-if="r.answers && r.answers.length">
                  <div v-for="(a, j) in r.answers" :key="j" class="answer-line">
                    <small class="muted">{{ a.question }}:</small> <strong>{{ a.value }}</strong>
                  </div>
                </template>
                <span v-else class="muted">—</span>
              </td>
              <td class="answers-cell">{{ r.comment || '—' }}</td>
              <td><small class="muted">{{ (r.entry_date || '').slice(0, 16) }}</small></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p class="muted" v-else-if="!responsesLoading">پاسخی در این بازه ثبت نشده است.</p>
      <p class="error" v-if="responsesError">{{ responsesError }}</p>
      <p class="muted hint-line">
        برای تحلیل عمیق‌تر، گزارش‌های «تحلیل نظرسنجی» و «نظرات سایت» را در مرکز گزارش‌ها ببینید؛ نظرات محصولات سایت از همان بخش دیدگاه‌های فروشگاه جمع‌آوری می‌شود.
        <a href="/management/reports">رفتن به مرکز گزارش‌ها ←</a>
      </p>
    </ManagementSurfaceCard>

    <div v-if="questionForm" class="popup-backdrop" @click.self="questionForm = null">
      <div class="popup">
        <h3>{{ questionForm.name ? 'ویرایش سوال' : 'سوال جدید' }}</h3>
        <div class="form-grid">
          <label class="full-row">متن سوال <span class="req">*</span><input class="input" v-model.trim="questionForm.question" /></label>
          <label>نوع پاسخ
            <select class="input" v-model="questionForm.answer_type">
              <option v-for="t in answerTypes" :key="t" :value="t">{{ t }}</option>
            </select>
          </label>
          <label>ترتیب نمایش<input class="input" type="number" min="0" v-model.number="questionForm.sort_order" /></label>
          <label class="check-row full-row"><input type="checkbox" v-model="questionForm.is_active" /> فعال</label>
        </div>
        <p class="error" v-if="questionFormError">{{ questionFormError }}</p>
        <div class="btn-row">
          <button type="button" class="primary-btn" @click="saveQuestion" :disabled="questionSaving">{{ questionSaving ? '...' : 'ذخیره سوال' }}</button>
          <button type="button" class="tertiary-btn" @click="questionForm = null">انصراف</button>
        </div>
      </div>
    </div>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  listManagementSurveyQuestions,
  saveManagementSurveyQuestion,
  deleteManagementSurveyQuestion,
  listManagementSurveyResponses,
} from '@/utils/api'

const answerTypes = ['امتیاز ۱ تا ۵', 'بله/خیر', 'متن آزاد']
const surveyPublicUrl = `${window.location.origin}/survey`

const questions = ref([])
const questionsLoading = ref(false)
const questionsError = ref('')
const showInactive = ref(true)
const questionForm = ref(null)
const questionFormError = ref('')
const questionSaving = ref(false)

const responses = ref([])
const responsesLoading = ref(false)
const responsesError = ref('')
const responseFilters = reactive({ date_from: '', date_to: '', search: '', min_rating: 0, max_rating: 0 })
const onlyDissatisfied = ref(false)

const loadingAny = computed(() => questionsLoading.value || responsesLoading.value)
const activeQuestionsCount = computed(() => questions.value.filter((q) => q.is_active).length)
const avgRating = computed(() => {
  const rated = responses.value.filter((r) => Number(r.overall_rating) > 0)
  if (!rated.length) return 0
  return Math.round((rated.reduce((a, r) => a + Number(r.overall_rating), 0) / rated.length) * 10) / 10
})
const dissatisfiedCount = computed(() => responses.value.filter((r) => r.dissatisfaction_alerted).length)
const filteredResponses = computed(() =>
  onlyDissatisfied.value ? responses.value.filter((r) => r.dissatisfaction_alerted || Number(r.overall_rating) <= 2) : responses.value,
)

function formatQty(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}
function starString(rating) {
  const n = Math.max(0, Math.min(5, Number(rating) || 0))
  return '★'.repeat(n) + '☆'.repeat(5 - n)
}

async function loadQuestions() {
  questionsLoading.value = true
  questionsError.value = ''
  try {
    const payload = await listManagementSurveyQuestions({ include_inactive: showInactive.value ? 1 : 0 })
    questions.value = payload?.questions || []
  } catch (err) {
    questionsError.value = err.message || 'دریافت سوالات ناموفق بود.'
  } finally {
    questionsLoading.value = false
  }
}

function openQuestionForm(q = null) {
  questionFormError.value = ''
  questionForm.value = q
    ? { name: q.name, question: q.question, answer_type: q.answer_type, sort_order: q.sort_order || 0, is_active: !!q.is_active }
    : { name: '', question: '', answer_type: 'امتیاز ۱ تا ۵', sort_order: (questions.value.length + 1) * 10, is_active: true }
}

async function saveQuestion() {
  questionSaving.value = true
  questionFormError.value = ''
  try {
    await saveManagementSurveyQuestion({ ...questionForm.value, is_active: questionForm.value.is_active ? 1 : 0 })
    questionForm.value = null
    await loadQuestions()
  } catch (err) {
    questionFormError.value = err.message || 'ذخیره سوال ناموفق بود.'
  } finally {
    questionSaving.value = false
  }
}

async function removeQuestion(q) {
  if (!window.confirm(`سوال «${q.question}» حذف شود؟`)) return
  try {
    await deleteManagementSurveyQuestion(q.name)
    await loadQuestions()
  } catch (err) {
    questionsError.value = err.message || 'حذف سوال ناموفق بود.'
  }
}

async function loadResponses() {
  responsesLoading.value = true
  responsesError.value = ''
  try {
    const payload = await listManagementSurveyResponses({ ...responseFilters })
    responses.value = payload?.responses || []
  } catch (err) {
    responsesError.value = err.message || 'دریافت پاسخ‌ها ناموفق بود.'
  } finally {
    responsesLoading.value = false
  }
}

function reload() {
  loadQuestions()
  loadResponses()
}

onMounted(() => {
  loadQuestions()
  loadResponses()
})
</script>

<style scoped>
.boot-kpis {
  margin-bottom: 0.9rem;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.date-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.84rem;
}
.survey-search {
  min-width: 240px;
  flex: 1;
}
.rating-select {
  min-width: 110px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.65rem;
  margin-bottom: 0.7rem;
}
.form-grid label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.86rem;
}
.full-row {
  grid-column: 1 / -1;
}
.input {
  width: 100%;
  box-sizing: border-box;
}
.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.6rem;
}
.table-wrap {
  overflow-x: auto;
  margin-top: 0.7rem;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.86rem;
}
.data-table th,
.data-table td {
  text-align: right;
  padding: 0.45rem 0.55rem;
  border-bottom: 1px solid var(--border-color, #e5dfd2);
  vertical-align: top;
}
.data-table th {
  color: var(--text-muted, #6b7a72);
  font-weight: 600;
  white-space: nowrap;
}
.data-table tr.inactive td {
  opacity: 0.55;
}
.data-table tr.alert-row td {
  background: rgba(184, 79, 79, 0.05);
}
.row-actions {
  white-space: nowrap;
}
.answers-cell {
  max-width: 300px;
}
.answer-line {
  line-height: 1.5;
}
.stars-mini {
  color: #e3a72f;
  letter-spacing: 1px;
}
.pill {
  display: inline-block;
  border-radius: 999px;
  padding: 0.12rem 0.6rem;
  font-size: 0.76rem;
  background: var(--surface-soft, #f0ede4);
  margin-inline-end: 0.25rem;
  white-space: nowrap;
}
.pill.ok {
  background: rgba(47, 111, 92, 0.14);
  color: var(--accent-green, #2f6f5c);
}
.pill.warn {
  background: rgba(184, 79, 79, 0.14);
  color: #b84f4f;
}
.check-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.88rem;
}
.link-code {
  direction: ltr;
  display: inline-block;
  background: var(--surface-soft, #f0ede4);
  border-radius: 6px;
  padding: 0.1rem 0.4rem;
  font-size: 0.78rem;
}
.popup-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(20, 24, 22, 0.45);
  display: grid;
  place-items: center;
  z-index: 60;
  padding: 1rem;
}
.popup {
  background: var(--surface-bg, #fff);
  border-radius: 16px;
  padding: 1rem 1.1rem;
  width: min(620px, 100%);
  max-height: 88vh;
  overflow-y: auto;
  display: grid;
  gap: 0.65rem;
}
.popup h3 {
  margin: 0;
}
.muted {
  color: var(--text-muted, #6b7a72);
}
.error {
  color: #b84f4f;
}
.ok-text {
  color: var(--accent-green, #2f6f5c);
}
.warn-text {
  color: #b84f4f;
}
.tertiary-btn.danger {
  color: #b84f4f;
}
.req {
  color: #b84f4f;
}
.hint-line {
  font-size: 0.78rem;
  margin-top: 0.5rem;
}
.hint-line a {
  color: var(--accent-color, #2f6f5c);
}
@media (max-width: 720px) {
  .toolbar .input {
    flex: 1 1 100%;
  }
}
</style>
