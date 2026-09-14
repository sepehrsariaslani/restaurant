<template>
  <ManagementPageScaffold title="پروفایل POS" subtitle="مشاهده داکتایپ POS Profile و انتخاب پروفایل فعال اپراتور">
    <template #actions>
      <button class="secondary-btn" type="button" @click="loadPOSProfile(activeProfileName)" :disabled="loading">
        {{ loading ? 'در حال بروزرسانی...' : 'بروزرسانی اطلاعات' }}
      </button>
      <button class="primary-btn" type="button" @click="setAsOperatorDefault" :disabled="saving || !activeProfileName">
        {{ saving ? 'در حال ثبت...' : 'ثبت به عنوان POS پیش فرض' }}
      </button>
    </template>

    <p class="error" v-if="error">{{ error }}</p>
    <p class="success" v-if="successMessage">{{ successMessage }}</p>

    <ManagementSurfaceCard
      tone="accent"
      title="POS فعال اپراتور"
      :subtitle="activeProfile?.title || activeProfile?.name || 'پروفایلی انتخاب نشده است'"
    >
      <div class="active-profile-grid">
        <div class="active-profile-main">
          <strong>{{ activeProfile?.title || activeProfile?.name || 'نامشخص' }}</strong>
          <small>کاربر جاری: {{ currentUser || '-' }}</small>
          <small>منبع انتخاب: {{ sourceLabel }}</small>
          <small v-if="activeProfile?.company">شرکت: {{ activeProfile.company }}</small>
          <small v-if="activeProfile?.warehouse">انبار: {{ activeProfile.warehouse }}</small>
          <small v-if="activeProfile?.selling_price_list">لیست قیمت: {{ activeProfile.selling_price_list }}</small>
        </div>

        <div class="active-profile-shift">
          <strong>{{ openingShift?.name ? 'شیفت باز فعال است' : 'شیفت باز ندارید' }}</strong>
          <small v-if="openingShift?.name">کد شیفت: {{ openingShift.name }}</small>
          <small v-if="openingShift?.opened_at">شروع شیفت: {{ formatDateTime(openingShift.opened_at) }}</small>
          <small v-if="openingShift?.opening_amount">
            مانده افتتاحیه: {{ formatMoney(openingShift.opening_amount || 0, activeProfile?.currency || 'IRR') }}
          </small>
        </div>

        <a
          v-if="activeProfile?.name"
          class="secondary-btn"
          :href="`/app/pos-profile/${encodeURIComponent(activeProfile.name)}`"
          target="_blank"
          rel="noreferrer"
        >
          باز کردن داکتایپ در ERPNext
        </a>
      </div>
    </ManagementSurfaceCard>

    <section class="profile-layout">
      <ManagementSurfaceCard title="لیست POS Profile ها" subtitle="پروفایل مناسب را انتخاب کنید">
        <p class="muted" v-if="loading">در حال دریافت پروفایل‌ها...</p>
        <p class="muted" v-else-if="!profiles.length">هیچ POS Profile فعالی پیدا نشد.</p>

        <div v-else class="profile-list">
          <button
            v-for="profile in profiles"
            :key="profile.name"
            type="button"
            class="profile-pill"
            :class="{ active: profile.name === activeProfileName, disabled: profile.disabled }"
            @click="loadPOSProfile(profile.name)"
          >
            <div class="profile-pill-head">
              <strong>{{ profile.title || profile.name }}</strong>
              <span class="tag" v-if="profile.has_open_shift">شیفت باز</span>
              <span class="tag warning" v-else-if="profile.disabled">غیرفعال</span>
            </div>
            <small v-if="profile.company">شرکت: {{ profile.company }}</small>
            <small v-if="profile.warehouse">انبار: {{ profile.warehouse }}</small>
            <small>ارز: {{ profile.currency || 'IRR' }}</small>
          </button>
        </div>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard
        title="جزئیات پروفایل انتخابی"
        :subtitle="activeProfile?.name ? `اطلاعات کامل ${activeProfile.name}` : 'یک پروفایل انتخاب کنید'"
      >
        <p class="muted" v-if="!activeProfile?.name">برای نمایش جزئیات، یک پروفایل انتخاب کنید.</p>

        <template v-else>
          <div class="edit-grid">
            <label>
              عنوان POS
              <input v-model.trim="profileForm.title" class="input" type="text" />
            </label>
            <label>
              شرکت
              <SearchableDropdown
                v-model="profileForm.company"
                :options="optionList('companies')"
                placeholder="انتخاب شرکت"
                search-placeholder="جستجوی شرکت..."
                include-empty-option
                empty-label="انتخاب شرکت"
              />
            </label>
            <label>
              انبار
              <SearchableDropdown
                v-model="profileForm.warehouse"
                :options="optionList('warehouses')"
                placeholder="انتخاب انبار"
                search-placeholder="جستجوی انبار..."
                include-empty-option
                empty-label="انتخاب انبار"
              />
            </label>
            <label>
              لیست قیمت
              <SearchableDropdown
                v-model="profileForm.selling_price_list"
                :options="optionList('price_lists')"
                placeholder="انتخاب لیست قیمت"
                search-placeholder="جستجوی لیست قیمت..."
                include-empty-option
                empty-label="انتخاب لیست قیمت"
              />
            </label>
            <label>
              مشتری پیش فرض
              <SearchableDropdown
                v-model="profileForm.customer"
                :options="optionList('customers')"
                placeholder="انتخاب مشتری"
                search-placeholder="جستجوی مشتری..."
                include-empty-option
                empty-label="انتخاب مشتری"
              />
            </label>
            <label>
              مرکز هزینه
              <SearchableDropdown
                v-model="profileForm.cost_center"
                :options="optionList('cost_centers')"
                placeholder="انتخاب مرکز هزینه"
                search-placeholder="جستجوی مرکز هزینه..."
                include-empty-option
                empty-label="انتخاب مرکز هزینه"
              />
            </label>
            <label>
              ارز
              <SearchableDropdown
                v-model="profileForm.currency"
                :options="optionList('currencies')"
                placeholder="انتخاب ارز"
                search-placeholder="جستجوی ارز..."
                include-empty-option
                empty-label="انتخاب ارز"
              />
            </label>
            <label>
              کمپین
              <input v-model.trim="profileForm.campaign" class="input" type="text" />
            </label>
            <label>
              الگوی مالیات
              <SearchableDropdown
                v-model="profileForm.taxes_and_charges"
                :options="optionList('taxes_templates')"
                placeholder="انتخاب مالیات"
                search-placeholder="جستجوی مالیات..."
                include-empty-option
                empty-label="انتخاب مالیات"
              />
            </label>
            <label>
              حساب Write Off
              <SearchableDropdown
                v-model="profileForm.write_off_account"
                :options="optionList('accounts')"
                placeholder="انتخاب حساب"
                search-placeholder="جستجوی حساب..."
                include-empty-option
                empty-label="انتخاب حساب"
              />
            </label>
            <label>
              Cost Center Write Off
              <SearchableDropdown
                v-model="profileForm.write_off_cost_center"
                :options="optionList('cost_centers')"
                placeholder="انتخاب مرکز هزینه"
                search-placeholder="جستجوی مرکز هزینه..."
                include-empty-option
                empty-label="انتخاب مرکز هزینه"
              />
            </label>
            <label class="check-row">
              <input v-model="profileForm.disabled" type="checkbox" />
              غیرفعال باشد
            </label>
          </div>

          <div class="detail-box">
            <strong>قابلیت‌ها</strong>
            <div class="capabilities controls">
              <label class="check-row"><input v-model="profileForm.allow_rate_change" type="checkbox" /> تغییر نرخ</label>
              <label class="check-row">
                <input v-model="profileForm.allow_discount_change" type="checkbox" />
                تغییر تخفیف
              </label>
              <label class="check-row">
                <input v-model="profileForm.ignore_pricing_rule" type="checkbox" />
                Ignore Pricing Rule
              </label>
              <label class="check-row"><input v-model="profileForm.update_stock" type="checkbox" /> ثبت انبار</label>
              <label class="check-row">
                <input v-model="profileForm.allow_negative_stock" type="checkbox" />
                موجودی منفی
              </label>
              <label class="check-row">
                <input v-model="profileForm.print_receipt_on_order_complete" type="checkbox" />
                چاپ خودکار رسید
              </label>
            </div>
          </div>

          <div class="detail-box">
            <header class="detail-head">
              <strong>روش‌های پرداخت</strong>
              <button type="button" class="secondary-btn" @click="addPaymentRow">افزودن روش پرداخت</button>
            </header>
            <p class="muted" v-if="!paymentRows.length">هیچ روش پرداختی ثبت نشده است.</p>
            <div v-else class="payment-grid">
              <article v-for="(payment, index) in paymentRows" :key="`payment-${index}`" class="payment-row">
                <label>
                  روش
                  <SearchableDropdown
                    v-model="payment.mode_of_payment"
                    :options="optionList('modes_of_payment')"
                    placeholder="انتخاب روش"
                    search-placeholder="جستجوی روش..."
                    include-empty-option
                    empty-label="انتخاب روش"
                  />
                </label>
                <label>
                  حساب
                  <SearchableDropdown
                    v-model="payment.account"
                    :options="optionList('accounts')"
                    placeholder="انتخاب حساب"
                    search-placeholder="جستجوی حساب..."
                    include-empty-option
                    empty-label="انتخاب حساب"
                  />
                </label>
                <label>
                  نوع
                  <input v-model.trim="payment.type" class="input" type="text" placeholder="cash / card" />
                </label>
                <label class="check-row">
                  <input v-model="payment.default" type="checkbox" />
                  پیش فرض
                </label>
                <button type="button" class="secondary-btn danger" @click="removePaymentRow(index)">حذف</button>
              </article>
            </div>
          </div>

          <div class="detail-box">
            <strong>کاربران مجاز</strong>
            <textarea
              v-model="usersText"
              class="input users-textarea"
              rows="4"
              placeholder="ایمیل کاربران را با ویرگول یا خط جدید جدا کنید"
            ></textarea>
            <small class="muted">برای مثال: user1@example.com, user2@example.com</small>
          </div>

          <div class="edit-actions">
            <button class="primary-btn" type="button" :disabled="saving || !activeProfileName" @click="saveProfileSettings(false)">
              {{ saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات POS' }}
            </button>
            <button class="secondary-btn" type="button" :disabled="saving || !activeProfileName" @click="saveProfileSettings(true)">
              ذخیره + ثبت به عنوان POS پیش فرض
            </button>
          </div>
        </template>
      </ManagementSurfaceCard>
    </section>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import SearchableDropdown from '@/components/SearchableDropdown.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { getManagementPOSProfile, setManagementPOSProfile, setManagementPOSProfileSettings } from '@/utils/api'
import { formatMoney } from '@/utils/format'

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const successMessage = ref('')
const currentUser = ref('')
const activeSource = ref('fallback')
const activeProfileName = ref('')
const profiles = ref([])
const activeProfile = ref(null)
const openingShift = ref(null)
const lookups = ref({})
const paymentRows = ref([])
const usersText = ref('')
const profileForm = reactive({
  title: '',
  company: '',
  warehouse: '',
  selling_price_list: '',
  customer: '',
  cost_center: '',
  currency: 'IRR',
  campaign: '',
  taxes_and_charges: '',
  write_off_account: '',
  write_off_cost_center: '',
  disabled: false,
  allow_rate_change: false,
  allow_discount_change: false,
  ignore_pricing_rule: false,
  update_stock: false,
  allow_negative_stock: false,
  print_receipt_on_order_complete: false,
})

const sourceLabel = computed(() => {
  const map = {
    requested: 'انتخاب مستقیم',
    open_shift: 'شیفت باز',
    user_default: 'پیش فرض کاربر',
    fallback: 'اولین پروفایل موجود',
    none: 'نامشخص',
  }
  return map[activeSource.value] || map.none
})

function optionList(key) {
  const rows = lookups.value?.[key]
  return Array.isArray(rows) ? rows : []
}

function applyProfileToForm(profile) {
  const source = profile && typeof profile === 'object' ? profile : {}
  profileForm.title = String(source.title || source.name || '').trim()
  profileForm.company = String(source.company || '').trim()
  profileForm.warehouse = String(source.warehouse || '').trim()
  profileForm.selling_price_list = String(source.selling_price_list || '').trim()
  profileForm.customer = String(source.customer || '').trim()
  profileForm.cost_center = String(source.cost_center || '').trim()
  profileForm.currency = String(source.currency || 'IRR').trim() || 'IRR'
  profileForm.campaign = String(source.campaign || '').trim()
  profileForm.taxes_and_charges = String(source.taxes_and_charges || '').trim()
  profileForm.write_off_account = String(source.write_off_account || '').trim()
  profileForm.write_off_cost_center = String(source.write_off_cost_center || '').trim()
  profileForm.disabled = Boolean(source.disabled)
  profileForm.allow_rate_change = Boolean(source.allow_rate_change)
  profileForm.allow_discount_change = Boolean(source.allow_discount_change)
  profileForm.ignore_pricing_rule = Boolean(source.ignore_pricing_rule)
  profileForm.update_stock = Boolean(source.update_stock)
  profileForm.allow_negative_stock = Boolean(source.allow_negative_stock)
  profileForm.print_receipt_on_order_complete = Boolean(source.print_receipt_on_order_complete)

  paymentRows.value = Array.isArray(source.payments)
    ? source.payments.map((row) => ({
        mode_of_payment: String(row?.mode_of_payment || '').trim(),
        account: String(row?.account || '').trim(),
        type: String(row?.type || '').trim(),
        default: Boolean(row?.default),
      }))
    : []
  usersText.value = Array.isArray(source.users) ? source.users.join(', ') : ''
}

function applyPayload(payload) {
  currentUser.value = String(payload?.current_user || '')
  activeSource.value = String(payload?.active_source || 'fallback')
  profiles.value = Array.isArray(payload?.profiles) ? payload.profiles : []
  activeProfileName.value = String(payload?.active_profile || '')
  activeProfile.value = payload?.profile && typeof payload.profile === 'object' ? payload.profile : null
  openingShift.value = payload?.opening_shift && typeof payload.opening_shift === 'object' ? payload.opening_shift : null
  lookups.value = payload?.options && typeof payload.options === 'object' ? payload.options : {}
  applyProfileToForm(activeProfile.value)
}

async function loadPOSProfile(profileName = '') {
  loading.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const payload = await getManagementPOSProfile({ profile_name: profileName || '' })
    applyPayload(payload || {})
  } catch (loadErr) {
    error.value = loadErr.message || 'دریافت تنظیمات POS Profile ناموفق بود.'
  } finally {
    loading.value = false
  }
}

async function setAsOperatorDefault() {
  if (!activeProfileName.value) {
    error.value = 'ابتدا یک POS Profile را انتخاب کنید.'
    return
  }
  saving.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const payload = await setManagementPOSProfile({ profile_name: activeProfileName.value })
    applyPayload(payload || {})
    successMessage.value = `پروفایل ${activeProfileName.value} برای کاربر جاری ذخیره شد.`
  } catch (saveErr) {
    error.value = saveErr.message || 'ذخیره POS Profile پیش فرض ناموفق بود.'
  } finally {
    saving.value = false
  }
}

function addPaymentRow() {
  paymentRows.value.push({
    mode_of_payment: '',
    account: '',
    type: '',
    default: false,
  })
}

function removePaymentRow(index) {
  if (index < 0 || index >= paymentRows.value.length) {
    return
  }
  paymentRows.value.splice(index, 1)
}

function normalizeUsers(rawUsers = '') {
  const uniqueUsers = []
  const chunks = String(rawUsers || '')
    .split(/[\n,]/g)
    .map((row) => row.trim())
    .filter(Boolean)
  for (const user of chunks) {
    if (!uniqueUsers.includes(user)) {
      uniqueUsers.push(user)
    }
  }
  return uniqueUsers
}

async function saveProfileSettings(setDefault = false) {
  if (!activeProfileName.value) {
    error.value = 'ابتدا یک POS Profile را انتخاب کنید.'
    return
  }

  saving.value = true
  error.value = ''
  successMessage.value = ''
  try {
    const payload = await setManagementPOSProfileSettings({
      profile_name: activeProfileName.value,
      settings: {
        title: profileForm.title,
        company: profileForm.company,
        warehouse: profileForm.warehouse,
        selling_price_list: profileForm.selling_price_list,
        customer: profileForm.customer,
        cost_center: profileForm.cost_center,
        currency: profileForm.currency,
        campaign: profileForm.campaign,
        taxes_and_charges: profileForm.taxes_and_charges,
        write_off_account: profileForm.write_off_account,
        write_off_cost_center: profileForm.write_off_cost_center,
        disabled: profileForm.disabled ? 1 : 0,
        allow_rate_change: profileForm.allow_rate_change ? 1 : 0,
        allow_discount_change: profileForm.allow_discount_change ? 1 : 0,
        ignore_pricing_rule: profileForm.ignore_pricing_rule ? 1 : 0,
        update_stock: profileForm.update_stock ? 1 : 0,
        allow_negative_stock: profileForm.allow_negative_stock ? 1 : 0,
        print_receipt_on_order_complete: profileForm.print_receipt_on_order_complete ? 1 : 0,
      },
      payments: paymentRows.value
        .map((row) => ({
          mode_of_payment: String(row.mode_of_payment || '').trim(),
          account: String(row.account || '').trim(),
          type: String(row.type || '').trim(),
          default: row.default ? 1 : 0,
        }))
        .filter((row) => row.mode_of_payment),
      users: normalizeUsers(usersText.value),
      set_default: setDefault ? 1 : 0,
    })
    applyPayload(payload || {})
    successMessage.value = setDefault
      ? `تنظیمات ${activeProfileName.value} ذخیره شد و پروفایل پیش فرض شد.`
      : `تنظیمات ${activeProfileName.value} ذخیره شد.`
  } catch (saveErr) {
    error.value = saveErr.message || 'ذخیره تنظیمات POS Profile ناموفق بود.'
  } finally {
    saving.value = false
  }
}

function formatDateTime(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return '-'
  }
  try {
    return new Intl.DateTimeFormat('fa-IR-u-ca-persian', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(raw))
  } catch (dateErr) {
    return raw
  }
}

loadPOSProfile()
</script>

<style scoped>
.active-profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: 0.6rem;
  align-items: start;
}

.active-profile-main,
.active-profile-shift {
  display: grid;
  gap: 0.2rem;
}

.active-profile-main strong,
.active-profile-shift strong {
  font-size: 0.9rem;
}

.active-profile-main small,
.active-profile-shift small {
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.76);
  font-size: 0.78rem;
}

.profile-layout {
  display: grid;
  grid-template-columns: minmax(260px, 0.9fr) minmax(0, 1.2fr);
  gap: 0.7rem;
}

.profile-list {
  display: grid;
  gap: 0.5rem;
  max-height: 64vh;
  overflow: auto;
  padding-inline-end: 0.12rem;
}

.profile-pill {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 16px;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  padding: 0.58rem;
  text-align: right;
  display: grid;
  gap: 0.2rem;
  transition: border-color 0.2s ease, transform 0.2s ease;
}

.profile-pill:hover {
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.58);
  transform: translateY(-1px);
}

.profile-pill.active {
  border-color: rgb(var(--palette-deep-saffron-rgb) / 0.72);
  box-shadow: 0 8px 20px rgb(var(--palette-deep-sapphire-rgb) / 0.14);
}

.profile-pill.disabled {
  opacity: 0.7;
}

.profile-pill-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
}

.tag {
  border-radius: 999px;
  padding: 0.16rem 0.5rem;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.24);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.9);
  font-size: 0.7rem;
}

.tag.warning {
  background: rgb(182 57 47 / 0.14);
  color: rgb(146 29 20);
}

.detail-grid {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 0.35rem 0.7rem;
  margin-bottom: 0.85rem;
}

.detail-grid span {
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.74);
  font-size: 0.79rem;
}

.detail-grid strong {
  font-size: 0.83rem;
}

.edit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
  margin-bottom: 0.65rem;
}

.edit-grid label {
  display: grid;
  gap: 0.2rem;
  font-size: 0.78rem;
}

.detail-box {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 14px;
  padding: 0.55rem;
  display: grid;
  gap: 0.45rem;
  margin-bottom: 0.55rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.6);
}

.capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.cap-chip {
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
  font-size: 0.74rem;
}

.capabilities.controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.32rem 0.5rem;
}

.check-row {
  display: inline-flex !important;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.76rem;
}

.cap-chip.on {
  background: rgb(var(--palette-june-bud-rgb) / 0.4);
  color: rgb(30 85 58);
}

.cap-chip.off {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.76);
}

.detail-box ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.3rem;
}

.detail-box li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
}

.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.payment-grid {
  display: grid;
  gap: 0.45rem;
}

.payment-row {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.12);
  border-radius: 12px;
  padding: 0.45rem;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.45rem;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
}

.payment-row label {
  display: grid;
  gap: 0.18rem;
  font-size: 0.76rem;
}

.payment-row .danger {
  justify-self: start;
}

.users-textarea {
  resize: vertical;
}

.edit-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.users-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.user-chip {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  color: rgb(var(--palette-deep-sapphire-rgb) / 0.86);
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
  font-size: 0.74rem;
}

@media (max-width: 980px) {
  .active-profile-grid,
  .profile-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .edit-grid,
  .capabilities.controls,
  .payment-row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
