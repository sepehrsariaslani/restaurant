<template>
  <ManagementPageScaffold title="نظرسنجی هوشمند" subtitle="نظرسنجی به ازای هر سفارش، سوالات اختصاصی و هشدار لحظه‌ای نارضایتی">
    <template #actions>
      <button type="button" class="secondary-btn" @click="reload" :disabled="loadingAny">
        {{ loadingAny ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
      </button>
    </template>

    <div class="totals-grid boot-kpis">
      <div class="total-box"><small>پاسخ‌های این بازه</small><strong>{{ formatQty(responses.length) }}</strong></div>
      <div class="total-box"><small>میانگین امتیاز</small><strong :class="avgRating && avgRating <= 6 ? 'warn-text' : 'ok-text'">{{ avgRating ? formatQty(avgRating) + ' / ۱۰' : '—' }}</strong></div>
      <div class="total-box" :class="{ 'warn-border': dissatisfiedCount > 0 }">
        <small>نارضایتی (≤ آستانه هشدار)</small><strong :class="dissatisfiedCount > 0 ? 'warn-text' : 'ok-text'">{{ formatQty(dissatisfiedCount) }}</strong>
      </div>
      <div class="total-box"><small>سوالات فعال</small><strong>{{ formatQty(activeQuestionsCount) }}</strong></div>
    </div>

    <ManagementSurfaceCard title="سوالات نظرسنجی" subtitle="این سوالات در صفحه عمومی نظرسنجی سفارش از مشتری پرسیده می‌شوند">
      <p class="muted hint-line">دعوت اختصاصی پس از تحویل سفارش ساخته می‌شود. پرسش‌های سفارش، گروه غذا و محصول بر اساس اقلام واقعی همان سفارش نمایش داده می‌شوند.</p>
      <div class="toolbar">
        <button type="button" class="primary-btn" @click="openQuestionForm()">سوال جدید</button>
        <label class="check-row"><input type="checkbox" v-model="showInactive" @change="loadQuestions" /> نمایش غیرفعال‌ها</label>
      </div>
      <p class="muted" v-if="questionsLoading">در حال دریافت سوالات...</p>
      <ManagementListView
        v-else
        :columns="questionColumns"
        :rows="questions"
        row-key="name"
        :row-clickable="true"
        @row-click="openQuestionForm"
      >
        <template #cell-question="{ row }"><strong>{{ row.question }}</strong></template>
        <template #cell-answer_type="{ value }"><span class="pill">{{ value }}</span></template>
        <template #cell-sort_order="{ value }">{{ formatQty(value) }}</template>
        <template #cell-is_active="{ row }"><span class="pill" :class="{ ok: row.is_active, warn: !row.is_active }">{{ row.is_active ? 'فعال' : 'غیرفعال' }}</span></template>
        <template #cell-actions="{ row }">
          <span class="row-actions">
            <button type="button" class="tertiary-btn" @click="openQuestionForm(row)">ویرایش</button>
            <button type="button" class="tertiary-btn danger" @click="removeQuestion(row)">حذف</button>
          </span>
        </template>
        <template #empty>هنوز سوالی تعریف نشده است؛ با «سوال جدید» شروع کنید.</template>
      </ManagementListView>
      <p class="error" v-if="questionsError">{{ questionsError }}</p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="پاسخ‌های نظرسنجی" subtitle="نظرات ثبت‌شده مشتریان؛ نارضایتی‌ها بلافاصله به مدیران هشدار داده می‌شوند">
      <div class="toolbar">
        <label class="date-label">از تاریخ<input class="input" type="date" v-model="responseFilters.date_from" @change="loadResponses" /></label>
        <label class="date-label">تا تاریخ<input class="input" type="date" v-model="responseFilters.date_to" @change="loadResponses" /></label>
        <input class="input survey-search" v-model.trim="responseFilters.search" placeholder="جستجو: نام، موبایل، کد سفارش، متن نظر..." @keyup.enter="loadResponses" />
        <select class="input rating-select" v-model="responseFilters.min_rating" @change="loadResponses">
          <option :value="0">از هر امتیازی</option>
          <option v-for="n in 10" :key="`min-${n}`" :value="n">{{ formatQty(n) }} به بالا</option>
        </select>
        <select class="input rating-select" v-model="responseFilters.max_rating" @change="loadResponses">
          <option :value="0">تا هر امتیازی</option>
          <option v-for="n in 10" :key="`max-${n}`" :value="n">تا {{ formatQty(n) }}</option>
        </select>
        <label class="check-row"><input type="checkbox" v-model="onlyDissatisfied" /> فقط ناراضی‌ها</label>
        <button type="button" class="secondary-btn" @click="loadResponses" :disabled="responsesLoading">{{ responsesLoading ? '...' : 'جستجو' }}</button>
      </div>
      <p class="muted" v-if="responsesLoading">در حال دریافت پاسخ‌ها...</p>
      <ManagementListView
        v-else
        :columns="responseColumns"
        :rows="filteredResponses"
        row-key="name"
      >
        <template #cell-order="{ row }"><strong>{{ row.sales_order || row.order_code }}</strong></template>
        <template #cell-customer="{ row }">{{ row.customer_name || '—' }}<br><small class="muted">{{ row.mobile }}</small></template>
        <template #cell-overall_rating="{ row }">
          <span class="pill" :class="{ ok: row.overall_rating >= 7, warn: row.overall_rating <= 3 }">{{ formatQty(row.overall_rating) }} / ۱۰</span>
          <span v-if="row.dissatisfaction_alerted" class="pill warn">هشدار شد</span>
        </template>
        <template #cell-answers="{ row }">
          <span v-if="!row.answers || !row.answers.length" class="muted">—</span>
          <span v-else class="answers-cell">
            <span v-for="(a, j) in row.answers" :key="j" class="answer-line"><small class="muted">{{ a.question }}:</small> <strong>{{ a.value }}</strong></span>
          </span>
        </template>
        <template #cell-comment="{ value }"><span class="answers-cell">{{ value || '—' }}</span></template>
        <template #cell-entry_date="{ value }"><small class="muted">{{ (value || '').slice(0, 16) }}</small></template>
        <template #empty>پاسخی در این بازه ثبت نشده است.</template>
      </ManagementListView>
      <p class="error" v-if="responsesError">{{ responsesError }}</p>
      <p class="muted hint-line">
        پاسخ‌های اینجا میانگین امتیاز اقلام و خدمت‌رسانی را در مقیاس ۱۰ نشان می‌دهند.
        <a href="/management/reports">رفتن به مرکز گزارش‌ها ←</a>
      </p>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="نظرهای غذا و پاسخ مدیر" subtitle="فقط نظرهای تأییدشده در صفحهٔ محصول دیده می‌شوند؛ پاسخ مدیر در حساب مشتری می‌ماند.">
      <div class="toolbar">
        <select class="input rating-select" v-model="reviewStatusFilter" @change="loadReviews">
          <option value="">همهٔ وضعیت‌ها</option>
          <option value="در انتظار بررسی">در انتظار بررسی</option>
          <option value="تأییدشده">تأییدشده</option>
          <option value="ردشده">ردشده</option>
        </select>
        <input class="input survey-search" v-model.trim="reviewSearch" placeholder="جستجوی مشتری، محصول یا نظر" @keyup.enter="loadReviews" />
        <button type="button" class="secondary-btn" @click="loadReviews" :disabled="reviewsLoading">{{ reviewsLoading ? '...' : 'جستجو' }}</button>
      </div>
      <p class="muted" v-if="reviewsLoading">در حال دریافت نظرها...</p>
      <ManagementListView v-else :columns="reviewColumns" :rows="reviews" row-key="name">
        <template #cell-item_title="{ row }">
          <span class="product-cell">
            <img v-if="row.image" :src="row.image" :alt="row.item_title" loading="lazy" />
            <strong>{{ row.item_title }}</strong>
          </span>
        </template>
        <template #cell-customer="{ row }">{{ row.customer_name }}<br /><small class="muted">{{ row.mobile }}</small><br /><small class="muted">{{ row.order_code }}</small></template>
        <template #cell-score_10="{ row }"><span class="pill" :class="{ ok: row.score_10 >= 7, warn: row.score_10 <= 3 }">{{ formatQty(row.score_10) }} / ۱۰</span></template>
        <template #cell-moderation_status="{ value }"><span class="pill" :class="statusClass(value)">{{ value }}</span></template>
        <template #cell-comment="{ row }">
          <span class="answers-cell">{{ row.comment || '—' }}</span>
          <div v-if="row.strengths_json?.length || row.weaknesses_json?.length" class="review-tags">
            <span v-for="tag in row.strengths_json || []" :key="`g-${tag}`" class="pill ok">{{ tag }}</span>
            <span v-for="tag in row.weaknesses_json || []" :key="`w-${tag}`" class="pill warn">{{ tag }}</span>
          </div>
          <small v-if="row.manager_reply" class="reply-preview">پاسخ: {{ row.manager_reply }}</small>
        </template>
        <template #cell-actions="{ row }">
          <span class="row-actions">
            <button v-if="row.moderation_status !== 'تأییدشده'" type="button" class="tertiary-btn" @click="openReviewEditor(row, 'تأییدشده')">تأیید</button>
            <button v-if="row.moderation_status !== 'ردشده'" type="button" class="tertiary-btn danger" @click="openReviewEditor(row, 'ردشده')">رد</button>
            <button type="button" class="tertiary-btn" @click="openReviewEditor(row)">{{ row.manager_reply ? 'ویرایش پاسخ' : 'پاسخ' }}</button>
          </span>
        </template>
        <template #empty>هنوز نظری ثبت نشده است.</template>
      </ManagementListView>
      <p class="error" v-if="reviewsError">{{ reviewsError }}</p>
      <div v-if="reviewEditor" class="popup-backdrop" @click.self="reviewEditor = null">
        <div class="popup" role="dialog" aria-modal="true" aria-labelledby="review-editor-title">
          <h3 id="review-editor-title">بررسی نظر {{ reviewEditor.review.item_title }}</h3>
          <p class="muted">{{ reviewEditor.review.customer_name }} · سفارش {{ reviewEditor.review.order_code }} · {{ formatQty(reviewEditor.review.score_10) }} از ۱۰</p>
          <p class="review-editor-comment">{{ reviewEditor.review.comment || 'بدون توضیح' }}</p>
          <label>وضعیت نمایش
            <select class="input" v-model="reviewEditor.moderation_status">
              <option v-for="state in reviewStates" :key="state" :value="state">{{ state }}</option>
            </select>
          </label>
          <label class="reply-field">پاسخ مدیر (برای مشتری در حسابش نمایش داده می‌شود)
            <textarea class="input" v-model.trim="reviewEditor.manager_reply" rows="4" maxlength="2000" placeholder="از بازخورد شما ممنونیم..."></textarea>
          </label>
          <p class="error" v-if="reviewEditorError">{{ reviewEditorError }}</p>
          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveReviewEditor" :disabled="reviewSaving">{{ reviewSaving ? 'در حال ذخیره...' : 'ذخیره' }}</button>
            <button type="button" class="tertiary-btn" @click="reviewEditor = null">انصراف</button>
          </div>
        </div>
      </div>
    </ManagementSurfaceCard>

    <ManagementSurfaceCard title="دعوت‌های پیامکی" subtitle="دعوت پس از تحویل زمان‌بندی می‌شود؛ پیامک‌های ناموفق یا بدون درگاه را می‌توان دوباره فرستاد.">
      <ManagementListView :columns="invitationColumns" :rows="invitations" row-key="name">
        <template #cell-order="{ row }"><strong>{{ row.order_code }}</strong></template>
        <template #cell-customer="{ row }">{{ row.customer_name || '—' }}<br /><small class="muted">{{ row.mobile }}</small></template>
        <template #cell-status="{ row }"><span class="pill" :class="statusClass(row.status)">{{ row.status }}</span><small v-if="row.last_error" class="invite-error">{{ row.last_error }}</small></template>
        <template #cell-attempts="{ value }">{{ formatQty(value) }}</template>
        <template #cell-due_at="{ value }"><small class="muted">{{ (value || '').slice(0, 16) }}</small></template>
        <template #cell-actions="{ row }"><button v-if="row.can_retry" class="tertiary-btn" type="button" @click="retryInvitation(row)" :disabled="retryingInvite === row.name">{{ retryingInvite === row.name ? '...' : 'ارسال دوباره' }}</button></template>
        <template #empty>هنوز دعوتی ساخته نشده است.</template>
      </ManagementListView>
      <p class="error" v-if="invitationsError">{{ invitationsError }}</p>
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
          <label>دامنهٔ سوال
            <select class="input" v-model="questionForm.scope">
              <option v-for="scope in questionScopes" :key="scope" :value="scope">{{ scope }}</option>
            </select>
          </label>
          <label v-if="questionForm.scope === 'گروه غذا'">گروه غذا
            <select class="input" v-model="questionForm.target_item_group">
              <option value="">انتخاب گروه</option>
              <option v-for="group in targets.groups" :key="group.name" :value="group.name">{{ group.item_group_name || group.name }}</option>
            </select>
          </label>
          <label v-if="questionForm.scope === 'محصول'">محصول
            <select class="input" v-model="questionForm.target_item">
              <option value="">انتخاب محصول</option>
              <option v-for="item in targets.items" :key="item.name" :value="item.name">{{ item.item_name }} · {{ item.name }}</option>
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
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import {
  listManagementSurveyQuestions,
  saveManagementSurveyQuestion,
  deleteManagementSurveyQuestion,
  listManagementSurveyResponses,
  listManagementSurveyTargets,
  listManagementCustomerReviews,
  reviewManagementCustomerReview,
  listManagementSurveyInvitations,
  retryManagementSurveyInvitation,
} from '@/utils/api'

const answerTypes = ['امتیاز ۱ تا ۱۰', 'بله/خیر', 'متن آزاد', 'ویژگی خوب/بد']
const questionScopes = ['سفارش', 'گروه غذا', 'محصول']
const reviewStates = ['در انتظار بررسی', 'تأییدشده', 'ردشده']
const targets = ref({ groups: [], items: [] })

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
const reviews = ref([])
const reviewsLoading = ref(false)
const reviewsError = ref('')
const reviewSearch = ref('')
const reviewStatusFilter = ref('')
const reviewEditor = ref(null)
const reviewEditorError = ref('')
const reviewSaving = ref(false)
const invitations = ref([])
const invitationsError = ref('')
const retryingInvite = ref('')
const questionColumns = [
  { key: 'question', label: 'سوال' },
  { key: 'answer_type', label: 'نوع پاسخ' },
  { key: 'scope', label: 'دامنه' },
  { key: 'sort_order', label: 'ترتیب' },
  { key: 'is_active', label: 'وضعیت' },
  { key: 'actions', label: 'عملیات' },
]
const responseColumns = [
  { key: 'order', label: 'سفارش' },
  { key: 'customer', label: 'مشتری' },
  { key: 'overall_rating', label: 'امتیاز کلی' },
  { key: 'answers', label: 'پاسخ‌ها' },
  { key: 'comment', label: 'توضیح' },
  { key: 'entry_date', label: 'زمان' },
]

const reviewColumns = [
  { key: 'item_title', label: 'غذا' },
  { key: 'customer', label: 'مشتری و سفارش' },
  { key: 'score_10', label: 'امتیاز' },
  { key: 'moderation_status', label: 'وضعیت' },
  { key: 'comment', label: 'نظر و ویژگی‌ها' },
  { key: 'actions', label: 'عملیات' },
]
const invitationColumns = [
  { key: 'order', label: 'سفارش' },
  { key: 'customer', label: 'مشتری' },
  { key: 'status', label: 'وضعیت پیامک' },
  { key: 'attempts', label: 'تعداد ارسال' },
  { key: 'due_at', label: 'زمان ارسال' },
  { key: 'actions', label: 'عملیات' },
]

const loadingAny = computed(() => questionsLoading.value || responsesLoading.value || reviewsLoading.value)
const activeQuestionsCount = computed(() => questions.value.filter((q) => q.is_active).length)
const avgRating = computed(() => {
  const rated = responses.value.filter((r) => Number(r.overall_rating) > 0)
  if (!rated.length) return 0
  return Math.round((rated.reduce((a, r) => a + Number(r.overall_rating), 0) / rated.length) * 10) / 10
})
const dissatisfiedCount = computed(() => responses.value.filter((r) => r.dissatisfaction_alerted).length)
const filteredResponses = computed(() =>
  onlyDissatisfied.value ? responses.value.filter((r) => r.dissatisfaction_alerted) : responses.value,
)

function formatQty(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}
function statusClass(value) {
  if (value === 'ارسال‌شده' || value === 'تأییدشده') return 'ok'
  if (value === 'ناموفق' || value === 'بدون درگاه' || value === 'ردشده' || value === 'در انتظار بررسی') return 'warn'
  return ''
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
    ? { name: q.name, question: q.question, answer_type: q.answer_type, scope: q.scope || 'سفارش', target_item_group: q.target_item_group || '', target_item: q.target_item || '', sort_order: q.sort_order || 0, is_active: !!q.is_active }
    : { name: '', question: '', answer_type: 'امتیاز ۱ تا ۱۰', scope: 'سفارش', target_item_group: '', target_item: '', sort_order: (questions.value.length + 1) * 10, is_active: true }
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

async function loadTargets() {
  try { targets.value = await listManagementSurveyTargets() } catch (_) { targets.value = { groups: [], items: [] } }
}

async function loadReviews() {
  reviewsLoading.value = true
  reviewsError.value = ''
  try {
    const payload = await listManagementCustomerReviews({ status: reviewStatusFilter.value, search: reviewSearch.value })
    reviews.value = payload?.reviews || []
  } catch (err) { reviewsError.value = err.message || 'دریافت نظرهای غذا ناموفق بود.' }
  finally { reviewsLoading.value = false }
}

async function loadInvitations() {
  invitationsError.value = ''
  try {
    const payload = await listManagementSurveyInvitations({ limit: 100 })
    invitations.value = payload?.invitations || []
  } catch (err) { invitationsError.value = err.message || 'دریافت دعوت‌ها ناموفق بود.' }
}

function openReviewEditor(review, status = review?.moderation_status || 'در انتظار بررسی') {
  reviewEditorError.value = ''
  reviewEditor.value = { review, moderation_status: status, manager_reply: review?.manager_reply || '' }
}

async function saveReviewEditor() {
  if (!reviewEditor.value || reviewSaving.value) return
  reviewSaving.value = true
  reviewEditorError.value = ''
  try {
    await reviewManagementCustomerReview({ name: reviewEditor.value.review.name, moderation_status: reviewEditor.value.moderation_status, manager_reply: reviewEditor.value.manager_reply })
    reviewEditor.value = null
    await loadReviews()
  } catch (err) { reviewEditorError.value = err.message || 'ذخیره پاسخ ناموفق بود.' }
  finally { reviewSaving.value = false }
}

async function retryInvitation(row) {
  retryingInvite.value = row.name
  try {
    await retryManagementSurveyInvitation(row.name)
    await loadInvitations()
  } catch (err) { invitationsError.value = err.message || 'ارسال دوباره انجام نشد.' }
  finally { retryingInvite.value = '' }
}

function reload() {
  loadQuestions()
  loadResponses()
  loadReviews()
  loadInvitations()
}

onMounted(() => {
  loadQuestions()
  loadResponses()
  loadTargets()
  loadReviews()
  loadInvitations()
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
.product-cell {
  display: inline-flex;
  align-items: center;
  gap: .55rem;
  min-width: 150px;
}
.product-cell img {
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  object-fit: cover;
  background: var(--ds-color-surface-muted);
}
.review-tags {
  display: flex;
  flex-wrap: wrap;
  gap: .25rem;
  margin-top: .35rem;
}
.reply-preview {
  display: block;
  max-width: 300px;
  margin-top: .35rem;
  color: var(--ds-color-action-primary);
  line-height: 1.7;
}
.invite-error {
  display: block;
  max-width: 260px;
  margin-top: .3rem;
  color: var(--ds-color-status-danger);
  line-height: 1.6;
  white-space: normal;
}
.review-editor-comment {
  margin: 0;
  padding: .75rem;
  border-radius: 12px;
  background: var(--ds-color-surface-muted);
  line-height: 1.8;
}
.reply-field {
  display: grid;
  gap: .4rem;
  color: var(--ds-color-text-secondary);
  font-size: .84rem;
}
.reply-field textarea {
  min-height: 100px;
  resize: vertical;
  font: inherit;
}
.popup :is(button, input, select, textarea):focus-visible {
  outline: 3px solid var(--ds-color-focus-ring);
  outline-offset: 2px;
}
@media (max-width: 720px) {
  .toolbar .input {
    flex: 1 1 100%;
  }
  .popup {
    align-self: end;
    max-height: min(88vh, 760px);
    border-radius: 20px 20px 8px 8px;
    padding-bottom: max(1rem, env(safe-area-inset-bottom));
  }
}
</style>
