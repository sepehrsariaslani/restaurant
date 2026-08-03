<template>
  <ManagementPageScaffold title="صندوق و ابزارهای فروش" subtitle="تسویه و بستن صندوق، شیفت‌های کاری، بسته‌بندی، کمبوها و فونت چاپ">
    <template #actions>
      <button type="button" class="secondary-btn" @click="reloadActiveTab" :disabled="loadingAny">
        {{ loadingAny ? 'در حال بروزرسانی...' : 'بروزرسانی' }}
      </button>
    </template>

    <nav class="tabs-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="setActiveTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </nav>

    <!-- ======================= تسویه و بستن صندوق ======================= -->
    <section v-if="activeTab === 'closing'" class="tab-body">
      <p class="error" v-if="closingError">{{ closingError }}</p>
      <p class="success-msg" v-if="closingMessage">{{ closingMessage }}</p>

      <ManagementSurfaceCard title="وضعیت صندوق باز" subtitle="جمع‌آوری زنده فروش‌های شیفت جاری شما">
        <p class="muted" v-if="closingLoading">در حال دریافت وضعیت صندوق...</p>
        <template v-else-if="closingSummary">
          <div class="meta-grid">
            <div>
              <small class="muted">شروع بازه</small>
              <strong>{{ formatDateTime(closingSummary.period_start) }}</strong>
            </div>
            <div>
              <small class="muted">پایان بازه</small>
              <strong>{{ formatDateTime(closingSummary.period_end) }}</strong>
            </div>
            <div>
              <small class="muted">آخرین اختتامیه</small>
              <strong>{{ closingSummary.last_closing ? closingSummary.last_closing.name : '—' }}</strong>
            </div>
            <div>
              <small class="muted">تلرانس اختلاف</small>
              <strong>{{ formatMoneyValue(closingSummary.tolerance) }}</strong>
            </div>
          </div>

          <div class="totals-grid">
            <div class="total-box" v-for="box in closingTotalBoxes" :key="box.key">
              <small>{{ box.label }}</small>
              <strong>{{ box.value }}</strong>
            </div>
          </div>
        </template>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="بستن صندوق" subtitle="شمارش وجوه، ثبت اختتامیه و چاپ گزارش">
        <div class="form-grid">
          <label>
            موجودی اولیه صندوق
            <input class="input" type="number" min="0" v-model.number="closingForm.opening_float" />
          </label>
          <label>
            وجه شمارش‌شده (نقد)
            <input class="input" type="number" min="0" v-model.number="closingForm.counted_cash" />
          </label>
          <ManagementNoteField
            v-model="closingForm.note"
            class="full-row"
            label="یادداشت اختتامیه"
            rows="2"
            placeholder="توضیح اختیاری برای اختتامیه صندوق"
          />
        </div>

        <div class="expected-line" v-if="closingSummary">
          <span>وجه مورد انتظار در صندوق:</span>
          <strong>{{ formatMoneyValue(expectedCashPreview) }}</strong>
          <span v-if="closingForm.counted_cash !== null && closingForm.counted_cash !== ''" :class="['diff-pill', differencePreview === 0 ? 'ok' : 'warn']">
            اختلاف: {{ formatMoneyValue(differencePreview) }}
          </span>
        </div>

        <div class="btn-row">
          <button type="button" class="primary-btn" @click="submitClosing" :disabled="closingSubmitting">
            {{ closingSubmitting ? 'در حال ثبت اختتامیه...' : 'ثبت تسویه و بستن صندوق' }}
          </button>
        </div>

        <div v-if="lastClosingResult" class="receipt-block">
          <div class="receipt-head">
            <strong>رسید اختتامیه {{ lastClosingResult.closing?.name }}</strong>
            <button type="button" class="secondary-btn" @click="printReceipt(lastClosingResult.receipt_html)">چاپ رسید</button>
          </div>
          <p :class="['hint-line', lastClosingResult.within_tolerance ? 'ok-text' : 'warn-text']">
            {{ lastClosingResult.within_tolerance ? 'صندوق بدون مغایرت (در محدوده تلرانس) بسته شد.' : 'صندوق با مغایرت بسته شد. لطفاً اختلاف را بررسی کنید.' }}
          </p>
          <div class="receipt-html" v-html="lastClosingResult.receipt_html"></div>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="سوابق اختتامیه" subtitle="آخرین تسویه‌های ثبت‌شده صندوق">
        <p class="muted" v-if="!closings.length">تاکنون اختتامیه‌ای ثبت نشده است.</p>
        <div v-else class="closing-list">
          <article v-for="closing in closings" :key="closing.name" class="closing-row">
            <div class="closing-row-main">
              <strong>{{ closing.name }}</strong>
              <small class="muted">{{ formatDateTime(closing.period_end) }} • {{ closing.cashier }}</small>
            </div>
            <div class="closing-row-nums">
              <span>فروش: {{ formatMoneyValue(closing.total_sales) }}</span>
              <span :class="Number(closing.cash_difference) === 0 ? 'ok-text' : 'warn-text'">
                اختلاف: {{ formatMoneyValue(closing.cash_difference) }}
              </span>
            </div>
            <div class="closing-row-actions">
              <button type="button" class="tertiary-btn" @click="viewClosingDetail(closing)">مشاهده</button>
            </div>
            <div v-if="expandedClosing === closing.name && closingDetail" class="receipt-html detail-receipt">
              <div class="btn-row">
                <button type="button" class="secondary-btn" @click="printReceipt(closingDetail.receipt_html)">چاپ رسید</button>
              </div>
              <div v-html="closingDetail.receipt_html"></div>
            </div>
          </article>
        </div>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= شیفت‌های کاری ======================= -->
    <section v-else-if="activeTab === 'shifts'" class="tab-body">
      <p class="error" v-if="shiftsError">{{ shiftsError }}</p>
      <p class="success-msg" v-if="shiftsMessage">{{ shiftsMessage }}</p>

      <ManagementSurfaceCard title="تعریف شیفت‌های کاری" subtitle="شیفت‌ها برای گزارش «فروش بر اساس شیفت» استفاده می‌شوند">
        <p class="muted" v-if="shiftsLoading">در حال دریافت شیفت‌ها...</p>
        <template v-else>
          <div class="shift-rows">
            <div class="shift-row shift-head">
              <span>عنوان شیفت</span>
              <span>شروع</span>
              <span>پایان</span>
              <span></span>
            </div>
            <div class="shift-row" v-for="(shift, index) in shiftsForm" :key="index">
              <input class="input" type="text" v-model="shift.label" placeholder="مثلاً صبح" />
              <input class="input" type="time" v-model="shift.start" />
              <input class="input" type="time" v-model="shift.end" />
              <button type="button" class="tertiary-btn danger" @click="removeShift(index)" :disabled="shiftsForm.length <= 1">حذف</button>
            </div>
          </div>
          <div class="btn-row">
            <button type="button" class="secondary-btn" @click="addShift" :disabled="shiftsForm.length >= 8">افزودن شیفت</button>
            <button type="button" class="primary-btn" @click="saveShifts" :disabled="shiftsSaving">
              {{ shiftsSaving ? 'در حال ذخیره...' : 'ذخیره شیفت‌ها' }}
            </button>
          </div>
          <p class="hint-line">شیفت شبانه می‌تواند از یک روز به روز بعد برود (مثلاً ۱۸:۰۰ تا ۰۲:۰۰).</p>
        </template>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= بسته‌بندی ======================= -->
    <section v-else-if="activeTab === 'packaging'" class="tab-body">
      <p class="error" v-if="packagingError">{{ packagingError }}</p>
      <p class="success-msg" v-if="packagingMessage">{{ packagingMessage }}</p>

      <ManagementSurfaceCard title="هزینه بسته‌بندی" subtitle="تعریف هزینه جداگانه بسته‌بندی برای سفارش‌ها">
        <p class="muted" v-if="packagingLoading">در حال دریافت تنظیمات...</p>
        <template v-else>
          <label class="check-row">
            <input type="checkbox" v-model="packagingForm.enabled" />
            فعال بودن هزینه بسته‌بندی
          </label>

          <div class="form-grid">
            <label>
              هزینه ثابت هر سفارش
              <input class="input" type="number" min="0" v-model.number="packagingForm.flat_fee" />
            </label>
            <label>
              عنوان در فاکتور
              <input class="input" type="text" v-model="packagingForm.label" placeholder="هزینه بسته‌بندی" />
            </label>
          </div>

          <label class="check-row">
            <input type="checkbox" v-model="packagingForm.per_item" />
            محاسبه هزینه بسته‌بندی تعریف‌شده برای هر محصول (به‌علاوه هزینه ثابت)
          </label>

          <div class="mode-grid">
            <label class="check-row"><input type="checkbox" v-model="packagingForm.modes.takeaway" /> بیرون‌بر</label>
            <label class="check-row"><input type="checkbox" v-model="packagingForm.modes.delivery" /> ارسال با پیک</label>
            <label class="check-row"><input type="checkbox" v-model="packagingForm.modes.dine_in" /> حضوری (سالن)</label>
          </div>

          <div class="btn-row">
            <button type="button" class="primary-btn" @click="savePackaging" :disabled="packagingSaving">
              {{ packagingSaving ? 'در حال ذخیره...' : 'ذخیره تنظیمات بسته‌بندی' }}
            </button>
          </div>
          <p class="hint-line">
            برای تعیین هزینه بسته‌بندیِ هر محصول، در صفحه محصول مقدار «هزینه بسته بندی» را تنظیم کنید.
          </p>
        </template>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= کمبوها ======================= -->
    <section v-else-if="activeTab === 'combos'" class="tab-body">
      <p class="error" v-if="combosError">{{ combosError }}</p>
      <p class="success-msg" v-if="combosMessage">{{ combosMessage }}</p>

      <ManagementSurfaceCard title="تعریف کمبو" subtitle="ترکیب چند محصول با یک قیمت ویژه (مثلاً پیتزا + نوشابه + سیب‌زمینی)">
        <div class="form-grid">
          <label class="full-row">
            محصول کمبو (محصول والد با قیمت ویژه)
            <SearchableDropdown
              v-model="comboForm.combo_item"
              :options="productOptions"
              placeholder="انتخاب محصول والد..."
              search-placeholder="جستجوی محصول..."
            />
          </label>
        </div>

        <div class="combo-components">
          <div class="combo-component-row component-head">
            <span>محصول تشکیل‌دهنده</span>
            <span>تعداد</span>
            <span></span>
          </div>
          <div class="combo-component-row" v-for="(component, index) in comboForm.items" :key="index">
            <SearchableDropdown
              v-model="component.item_code"
              :options="productOptions"
              placeholder="انتخاب محصول..."
              search-placeholder="جستجوی محصول..."
            />
            <input class="input" type="number" min="1" step="0.5" v-model.number="component.qty" />
            <button type="button" class="tertiary-btn danger" @click="comboForm.items.splice(index, 1)" :disabled="comboForm.items.length <= 1">حذف</button>
          </div>
        </div>

        <div class="btn-row">
          <button type="button" class="secondary-btn" @click="comboForm.items.push({ item_code: '', qty: 1 })">افزودن محصول</button>
          <button type="button" class="primary-btn" @click="saveCombo" :disabled="comboSaving">
            {{ comboSaving ? 'در حال ذخیره...' : 'ذخیره کمبو' }}
          </button>
        </div>
        <p class="hint-line">قیمت کمبو همان قیمت محصول والد است؛ اجزای کمبو هنگام تحویل از انبار کم می‌شوند.</p>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard title="لیست کمبوها" subtitle="کمبوهای فعال مجموعه">
        <p class="muted" v-if="combosLoading">در حال دریافت کمبوها...</p>
        <p class="muted" v-else-if="!combos.length">هنوز کمبویی تعریف نشده است.</p>
        <div v-else class="combo-list">
          <article class="combo-card" v-for="combo in combos" :key="combo.name">
            <header>
              <strong>{{ combo.item_name }}</strong>
              <small class="muted">{{ combo.combo_item }} • {{ formatMoneyValue(combo.price) }}</small>
            </header>
            <ul>
              <li v-for="(component, idx) in combo.items" :key="idx">
                {{ component.item_name }} × {{ component.qty }}
              </li>
            </ul>
            <div class="btn-row">
              <button type="button" class="secondary-btn" @click="editCombo(combo)">ویرایش</button>
              <button type="button" class="tertiary-btn danger" @click="removeCombo(combo)" :disabled="comboDeleting === combo.name">
                {{ comboDeleting === combo.name ? 'در حال حذف...' : 'حذف' }}
              </button>
            </div>
          </article>
        </div>
      </ManagementSurfaceCard>
    </section>

    <!-- ======================= فونت چاپ ======================= -->
    <section v-else-if="activeTab === 'fonts'" class="tab-body">
      <p class="error" v-if="fontsError">{{ fontsError }}</p>
      <p class="success-msg" v-if="fontsMessage">{{ fontsMessage }}</p>

      <ManagementSurfaceCard title="فونت چاپ" subtitle="انتخاب نوع و اندازه فونت فاکتور و رسید">
        <p class="muted" v-if="fontsLoading">در حال دریافت تنظیمات...</p>
        <template v-else>
          <div class="form-grid">
            <label>
              فونت چاپ
              <SearchableDropdown
                v-model="fontsForm.font_family"
                :options="fontFamilyOptions"
                placeholder="انتخاب فونت..."
                search-placeholder="جستجوی فونت..."
              />
            </label>
            <label>
              اندازه پایه فونت (پیکسل)
              <input class="input" type="number" min="8" max="24" v-model.number="fontsForm.font_size" />
            </label>
            <label>
              مقیاس فونت فیش حرارتی
              <SearchableDropdown
                v-model="fontsForm.receipt_font_scale"
                :options="fontScaleOptions"
                placeholder="انتخاب مقیاس..."
              />
            </label>
          </div>

          <div class="btn-row">
            <button type="button" class="primary-btn" @click="saveFonts" :disabled="fontsSaving">
              {{ fontsSaving ? 'در حال ذخیره...' : 'ذخیره تنظیمات فونت' }}
            </button>
          </div>

          <div class="font-preview" :style="{ fontFamily: `${fontsForm.font_family}, Peyda, Tahoma, sans-serif`, fontSize: `${fontsForm.font_size || 11}px` }">
            <strong>پیش‌نمایش فونت چاپ</strong>
            <p>فاکتور فروش رستوران — پیتزا مخصوص × ۲ — ۲۵۰٬۰۰۰ ریال</p>
            <small>تشکر از خرید شما • {{ fontsForm.font_family }}</small>
          </div>
        </template>
      </ManagementSurfaceCard>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementNoteField from '@/components/management/ManagementNoteField.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import {
  closeManagementRegister,
  deleteManagementCombo,
  getManagementPackagingSettings,
  getManagementPrintFontSettings,
  getManagementRegisterClosingDetail,
  getManagementRegisterClosingSummary,
  getManagementWorkShifts,
  listManagementCombos,
  listManagementProducts,
  listManagementRegisterClosings,
  saveManagementCombo,
  setManagementPackagingSettings,
  setManagementPrintFontSettings,
  setManagementWorkShifts,
} from '@/utils/api'
import { formatMoney as formatMoneyUtil } from '@/utils/format'

const tabs = [
  { key: 'closing', label: 'تسویه و بستن صندوق' },
  { key: 'shifts', label: 'شیفت‌های کاری' },
  { key: 'packaging', label: 'بسته‌بندی' },
  { key: 'combos', label: 'کمبوها' },
  { key: 'fonts', label: 'فونت چاپ' },
]
const activeTab = ref('closing')
const currency = ref('IRR')

function setActiveTab(key) {
  activeTab.value = key
  if (key === 'closing') loadClosingTab()
  else if (key === 'shifts') loadShifts()
  else if (key === 'packaging') loadPackaging()
  else if (key === 'combos') loadCombosTab()
  else if (key === 'fonts') loadFonts()
}

function reloadActiveTab() {
  setActiveTab(activeTab.value)
}

function formatMoneyValue(value) {
  return formatMoneyUtil(Number(value || 0), currency.value)
}

function formatDateTime(value) {
  if (!value) return '—'
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value))
  } catch (_) {
    return String(value)
  }
}

function printReceipt(html) {
  if (!html) return
  const printWindow = window.open('', '_blank', 'width=420,height=640')
  if (!printWindow) return
  printWindow.document.write(`<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>رسید اختتامیه</title></head><body>${html}</body></html>`)
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
}

// ------------------------- Register closing -------------------------
const closingLoading = ref(false)
const closingSubmitting = ref(false)
const closingError = ref('')
const closingMessage = ref('')
const closingSummary = ref(null)
const closings = ref([])
const closingForm = reactive({ opening_float: 0, counted_cash: null, note: '' })
const lastClosingResult = ref(null)
const expandedClosing = ref('')
const closingDetail = ref(null)

const expectedCashPreview = computed(() =>
  Number(closingForm.opening_float || 0) + Number(closingSummary.value?.totals?.cash_sales || 0),
)
const differencePreview = computed(() => Number(closingForm.counted_cash || 0) - expectedCashPreview.value)

const closingTotalBoxes = computed(() => {
  const totals = closingSummary.value?.totals || {}
  return [
    { key: 'orders', label: 'تعداد سفارش', value: Number(totals.orders || 0).toLocaleString('fa-IR') },
    { key: 'total', label: 'فروش کل', value: formatMoneyValue(totals.total_sales) },
    { key: 'cash', label: 'نقدی', value: formatMoneyValue(totals.cash_sales) },
    { key: 'card', label: 'کارتی', value: formatMoneyValue(totals.card_sales) },
    { key: 'credit', label: 'نسیه', value: formatMoneyValue(totals.credit_sales) },
    { key: 'other', label: 'سایر', value: formatMoneyValue(totals.other_sales) },
  ]
})

async function loadClosingTab() {
  closingLoading.value = true
  closingError.value = ''
  try {
    const summary = await getManagementRegisterClosingSummary()
    closingSummary.value = summary
    currency.value = summary.currency || currency.value
    closingForm.opening_float = Number(summary.suggested_opening_float || 0)
    const history = await listManagementRegisterClosings({ limit: 20 })
    closings.value = history.closings || []
  } catch (err) {
    closingError.value = err?.message || 'دریافت وضعیت صندوق ناموفق بود.'
  } finally {
    closingLoading.value = false
  }
}

async function submitClosing() {
  closingSubmitting.value = true
  closingError.value = ''
  closingMessage.value = ''
  try {
    const result = await closeManagementRegister({
      opening_float: Number(closingForm.opening_float || 0),
      counted_cash: Number(closingForm.counted_cash || 0),
      note: closingForm.note || '',
    })
    lastClosingResult.value = result
    closingMessage.value = 'صندوق با موفقیت تسویه و بسته شد.'
    closingForm.note = ''
    await loadClosingTab()
    lastClosingResult.value = result
  } catch (err) {
    closingError.value = err?.message || 'ثبت اختتامیه صندوق ناموفق بود.'
  } finally {
    closingSubmitting.value = false
  }
}

async function viewClosingDetail(closing) {
  if (expandedClosing.value === closing.name) {
    expandedClosing.value = ''
    closingDetail.value = null
    return
  }
  expandedClosing.value = closing.name
  closingDetail.value = null
  try {
    closingDetail.value = await getManagementRegisterClosingDetail(closing.name)
  } catch (err) {
    closingError.value = err?.message || 'دریافت جزئیات اختتامیه ناموفق بود.'
  }
}

// ------------------------- Work shifts -------------------------
const shiftsLoading = ref(false)
const shiftsSaving = ref(false)
const shiftsError = ref('')
const shiftsMessage = ref('')
const shiftsForm = ref([])

async function loadShifts() {
  shiftsLoading.value = true
  shiftsError.value = ''
  try {
    const payload = await getManagementWorkShifts()
    shiftsForm.value = (payload.shifts || []).map((shift) => ({
      key: shift.key,
      label: shift.label,
      start: shift.start,
      end: shift.end,
    }))
    if (!shiftsForm.value.length) {
      shiftsForm.value = [{ key: 'morning', label: 'صبح', start: '08:00', end: '16:00' }]
    }
  } catch (err) {
    shiftsError.value = err?.message || 'دریافت شیفت‌ها ناموفق بود.'
  } finally {
    shiftsLoading.value = false
  }
}

function addShift() {
  shiftsForm.value.push({ key: `shift_${Date.now()}`, label: '', start: '08:00', end: '16:00' })
}

function removeShift(index) {
  shiftsForm.value.splice(index, 1)
}

async function saveShifts() {
  shiftsSaving.value = true
  shiftsError.value = ''
  shiftsMessage.value = ''
  try {
    const payload = await setManagementWorkShifts(shiftsForm.value.map((shift) => ({
      key: shift.key,
      label: shift.label,
      start: shift.start,
      end: shift.end,
    })))
    shiftsForm.value = payload.shifts || shiftsForm.value
    shiftsMessage.value = 'شیفت‌های کاری ذخیره شدند.'
  } catch (err) {
    shiftsError.value = err?.message || 'ذخیره شیفت‌ها ناموفق بود.'
  } finally {
    shiftsSaving.value = false
  }
}

// ------------------------- Packaging -------------------------
const packagingLoading = ref(false)
const packagingSaving = ref(false)
const packagingError = ref('')
const packagingMessage = ref('')
const packagingForm = reactive({
  enabled: false,
  flat_fee: 0,
  per_item: true,
  label: 'هزینه بسته‌بندی',
  modes: { takeaway: true, delivery: true, dine_in: false },
})

async function loadPackaging() {
  packagingLoading.value = true
  packagingError.value = ''
  try {
    const payload = await getManagementPackagingSettings()
    packagingForm.enabled = Boolean(payload.enabled)
    packagingForm.flat_fee = Number(payload.flat_fee || 0)
    packagingForm.per_item = Boolean(payload.per_item)
    packagingForm.label = payload.label || 'هزینه بسته‌بندی'
    const modes = Array.isArray(payload.apply_modes) ? payload.apply_modes : []
    packagingForm.modes = {
      takeaway: modes.includes('takeaway'),
      delivery: modes.includes('delivery'),
      dine_in: modes.includes('dine_in'),
    }
    currency.value = payload.currency || currency.value
  } catch (err) {
    packagingError.value = err?.message || 'دریافت تنظیمات بسته‌بندی ناموفق بود.'
  } finally {
    packagingLoading.value = false
  }
}

async function savePackaging() {
  packagingSaving.value = true
  packagingError.value = ''
  packagingMessage.value = ''
  try {
    const modes = Object.entries(packagingForm.modes)
      .filter(([, enabled]) => enabled)
      .map(([mode]) => mode)
    await setManagementPackagingSettings({
      enabled: packagingForm.enabled ? 1 : 0,
      flat_fee: Number(packagingForm.flat_fee || 0),
      per_item: packagingForm.per_item ? 1 : 0,
      label: packagingForm.label,
      apply_modes: modes,
    })
    packagingMessage.value = 'تنظیمات بسته‌بندی ذخیره شد.'
  } catch (err) {
    packagingError.value = err?.message || 'ذخیره تنظیمات بسته‌بندی ناموفق بود.'
  } finally {
    packagingSaving.value = false
  }
}

// ------------------------- Combos -------------------------
const combos = ref([])
const combosLoading = ref(false)
const comboSaving = ref(false)
const comboDeleting = ref('')
const combosError = ref('')
const combosMessage = ref('')
const productOptions = ref([])
const comboForm = reactive({ combo_item: '', items: [{ item_code: '', qty: 1 }] })

async function loadCombosTab() {
  combosLoading.value = true
  combosError.value = ''
  try {
    const payload = await listManagementCombos()
    combos.value = payload.combos || []
    if (!productOptions.value.length) {
      const productsPayload = await listManagementProducts({ active_only: 0 })
      productOptions.value = (productsPayload.products || [])
        .map((product) => ({
          value: String(product.name || product.item_code || '').trim(),
          label: `${product.title || product.item_name || product.name} (${product.item_code || product.name})`,
        }))
        .filter((option) => option.value)
    }
  } catch (err) {
    combosError.value = err?.message || 'دریافت کمبوها ناموفق بود.'
  } finally {
    combosLoading.value = false
  }
}

async function saveCombo() {
  comboSaving.value = true
  combosError.value = ''
  combosMessage.value = ''
  try {
    const result = await saveManagementCombo({
      combo_item: comboForm.combo_item,
      items: comboForm.items
        .filter((component) => component.item_code)
        .map((component) => ({ item_code: component.item_code, qty: Number(component.qty || 1) })),
    })
    combosMessage.value = `کمبو «${result?.combo?.item_name || comboForm.combo_item}» ذخیره شد.`
    comboForm.combo_item = ''
    comboForm.items = [{ item_code: '', qty: 1 }]
    await loadCombosTab()
  } catch (err) {
    combosError.value = err?.message || 'ذخیره کمبو ناموفق بود.'
  } finally {
    comboSaving.value = false
  }
}

function editCombo(combo) {
  comboForm.combo_item = combo.combo_item
  comboForm.items = (combo.items || []).map((component) => ({
    item_code: component.item_code,
    qty: component.qty,
  }))
  if (!comboForm.items.length) {
    comboForm.items = [{ item_code: '', qty: 1 }]
  }
}

async function removeCombo(combo) {
  comboDeleting.value = combo.name
  combosError.value = ''
  try {
    await deleteManagementCombo(combo.combo_item)
    combosMessage.value = 'کمبو حذف شد.'
    await loadCombosTab()
  } catch (err) {
    combosError.value = err?.message || 'حذف کمبو ناموفق بود.'
  } finally {
    comboDeleting.value = ''
  }
}

// ------------------------- Print fonts -------------------------
const fontsLoading = ref(false)
const fontsSaving = ref(false)
const fontsError = ref('')
const fontsMessage = ref('')
const fontsForm = reactive({ font_family: 'Peyda', font_size: 11, receipt_font_scale: 'متوسط' })
const fontFamilyOptions = ref([])
const fontScaleOptions = ref([])

async function loadFonts() {
  fontsLoading.value = true
  fontsError.value = ''
  try {
    const payload = await getManagementPrintFontSettings()
    fontsForm.font_family = payload.font_family || 'Peyda'
    fontsForm.font_size = Number(payload.font_size || 11)
    fontsForm.receipt_font_scale = payload.receipt_font_scale || 'متوسط'
    fontFamilyOptions.value = (payload.font_options || []).map((font) => ({ value: font, label: font }))
    fontScaleOptions.value = (payload.scale_options || []).map((scale) => ({ value: scale, label: scale }))
  } catch (err) {
    fontsError.value = err?.message || 'دریافت تنظیمات فونت ناموفق بود.'
  } finally {
    fontsLoading.value = false
  }
}

async function saveFonts() {
  fontsSaving.value = true
  fontsError.value = ''
  fontsMessage.value = ''
  try {
    await setManagementPrintFontSettings({
      font_family: fontsForm.font_family,
      font_size: Number(fontsForm.font_size || 11),
      receipt_font_scale: fontsForm.receipt_font_scale,
    })
    fontsMessage.value = 'تنظیمات فونت چاپ ذخیره شد.'
  } catch (err) {
    fontsError.value = err?.message || 'ذخیره تنظیمات فونت ناموفق بود.'
  } finally {
    fontsSaving.value = false
  }
}

const loadingAny = computed(
  () => closingLoading.value || shiftsLoading.value || packagingLoading.value || combosLoading.value || fontsLoading.value,
)

onMounted(() => {
  loadClosingTab()
})
</script>

<style scoped>
.tabs-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.tab-btn {
  border: 1px solid var(--border-color, #d8d2c4);
  background: var(--surface-soft, #f7f4ee);
  color: var(--text-primary, #2f3c36);
  border-radius: 999px;
  padding: 0.45rem 1rem;
  cursor: pointer;
  font: inherit;
}
.tab-btn.active {
  background: var(--accent-green, #2f6f5c);
  border-color: var(--accent-green, #2f6f5c);
  color: #fff;
}
.tab-body {
  display: grid;
  gap: 0.9rem;
}
.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.65rem;
  margin-bottom: 0.9rem;
}
.meta-grid small {
  display: block;
}
.totals-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 0.55rem;
}
.total-box {
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.55rem 0.7rem;
  display: grid;
  gap: 0.2rem;
}
.total-box small {
  color: var(--text-muted, #6b7a72);
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
.expected-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.6rem;
  padding: 0.6rem 0.7rem;
  border-radius: 10px;
  background: var(--surface-soft, #f7f4ee);
  margin-bottom: 0.7rem;
}
.diff-pill {
  border-radius: 999px;
  padding: 0.2rem 0.7rem;
  font-size: 0.8rem;
}
.diff-pill.ok {
  background: rgba(47, 111, 92, 0.14);
  color: var(--accent-green, #2f6f5c);
}
.diff-pill.warn {
  background: rgba(184, 79, 79, 0.14);
  color: #b84f4f;
}
.btn-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.6rem;
}
.receipt-block {
  margin-top: 1rem;
  border-top: 1px dashed var(--border-color, #d8d2c4);
  padding-top: 0.8rem;
}
.receipt-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.receipt-html {
  max-width: 420px;
  margin-top: 0.7rem;
}
.detail-receipt {
  grid-column: 1 / -1;
}
.closing-list {
  display: grid;
  gap: 0.55rem;
}
.closing-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 0.4rem;
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.6rem 0.75rem;
}
.closing-row-main {
  display: flex;
  align-items: baseline;
  gap: 0.6rem;
  flex-wrap: wrap;
}
.closing-row-nums {
  display: flex;
  gap: 0.9rem;
  flex-wrap: wrap;
  font-size: 0.84rem;
}
.ok-text {
  color: var(--accent-green, #2f6f5c);
}
.warn-text {
  color: #b84f4f;
}
.shift-rows,
.combo-components {
  display: grid;
  gap: 0.45rem;
}
.shift-row,
.combo-component-row {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 0.5rem;
  align-items: center;
}
.combo-component-row {
  grid-template-columns: minmax(0, 3fr) minmax(0, 1fr) auto;
}
.shift-head,
.component-head {
  font-size: 0.78rem;
  color: var(--text-muted, #6b7a72);
}
.mode-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin: 0.4rem 0;
}
.check-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.88rem;
}
.combo-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.65rem;
}
.combo-card {
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.65rem 0.75rem;
  display: grid;
  gap: 0.4rem;
}
.combo-card ul {
  margin: 0;
  padding-inline-start: 1.1rem;
  font-size: 0.84rem;
}
.font-preview {
  margin-top: 1rem;
  border: 1px dashed var(--border-color, #d8d2c4);
  border-radius: 12px;
  padding: 0.8rem 1rem;
  display: grid;
  gap: 0.25rem;
}
.hint-line {
  font-size: 0.78rem;
  color: var(--text-muted, #6b7a72);
  margin-top: 0.5rem;
}
.error {
  color: #b84f4f;
}
.success-msg {
  color: var(--accent-green, #2f6f5c);
}
.muted {
  color: var(--text-muted, #6b7a72);
}
.tertiary-btn.danger {
  color: #b84f4f;
}
</style>
