<template>
  <ManagementPageScaffold
    :title="detailOnly ? (form.name ? 'جزئیات کاربر' : 'کاربر جدید') : 'کاربران و دسترسی‌ها'"
    :subtitle="detailOnly ? 'پروفایل کاربر، نقش‌ها و وضعیت دسترسی' : 'مدیریت کاربران، نقش‌ها و دسترسی ورود به پنل'"
  >
    <template #actions>
      <a v-if="detailOnly" class="secondary-btn" href="/management/users">بازگشت به لیست کاربران</a>
      <button v-if="!detailOnly" class="primary-btn" type="button" @click="openNewUser">+ کاربر جدید</button>
      <button class="secondary-btn" type="button" :disabled="loading" @click="loadUsers">بروزرسانی</button>
    </template>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="success" class="success">{{ success }}</p>

    <div class="users-layout" :class="{ 'users-layout--detail': detailOnly }">
      <ManagementSurfaceCard v-if="!detailOnly" title="فهرست کاربران" subtitle="برای ویرایش، روی نام کاربر کلیک کنید.">
        <template v-if="!detailOnly">
          <ManagementCollectionView v-model="viewMode" :modes="userViewModes">
            <template #toolbar>
              <div class="toolbar-row">
                <input v-model.trim="search" class="input" placeholder="جستجو بر اساس نام یا ایمیل" @keyup.enter="loadUsers" />
                <button class="secondary-btn" type="button" @click="loadUsers">جستجو</button>
              </div>
            </template>

            <template #table>
              <ManagementListView :columns="userColumns" :rows="users" row-key="name" :row-clickable="true" @row-click="openUserDetail">
                <template #cell-full_name="{ row }"><strong>{{ row.full_name || row.email }}</strong></template>
                <template #cell-email="{ value }"><span dir="ltr">{{ value || '—' }}</span></template>
                <template #cell-enabled="{ row }"><span :class="['status-pill', row.enabled ? 'active' : 'disabled']">{{ row.enabled ? 'فعال' : 'غیرفعال' }}</span></template>
                <template #cell-roles="{ row }">{{ row.roles?.join('، ') || 'بدون نقش' }}</template>
                <template #cell-actions="{ row }"><button class="secondary-btn mini-link-btn" type="button" @click.stop="openUserDetail(row)">جزئیات</button></template>
                <template #empty>کاربری پیدا نشد.</template>
              </ManagementListView>
            </template>

            <template #list>
              <ManagementNotionListView
                :rows="users"
                row-key="name"
                title-key="full_name"
                code-key="email"
                :properties="{ enabled: true, roles: true }"
                :property-order="['enabled', 'roles']"
                :chip-renderers="userChipRenderers"
                :row-clickable="true"
                @row-click="openUserDetail"
              />
            </template>

            <template #gallery>
              <ManagementGalleryView
                :rows="users"
                row-key="name"
                title-field="full_name"
                code-field="email"
                :clickable="true"
                @click-item="openUserDetail"
              />
            </template>
          </ManagementCollectionView>
          <p v-if="!loading && !users.length" class="empty">کاربری پیدا نشد.</p>
        </template>
      </ManagementSurfaceCard>

      <ManagementSurfaceCard :title="form.name ? 'ویرایش کاربر' : 'ایجاد کاربر جدید'" subtitle="نقش‌ها سطح دسترسی پایه کاربر را مشخص می‌کنند.">
        <div class="form-grid">
          <label>نام کامل<input v-model.trim="form.full_name" class="input" placeholder="نام و نام خانوادگی" /></label>
          <label>ایمیل / نام کاربری<input v-model.trim="form.email" class="input" type="email" dir="ltr" :disabled="Boolean(form.name)" /></label>
          <label>شماره موبایل<input v-model.trim="form.mobile_no" class="input" dir="ltr" /></label>
          <label v-if="!form.name">رمز عبور<input v-model="form.new_password" class="input" type="password" dir="ltr" minlength="8" placeholder="حداقل ۸ کاراکتر" /></label>
        </div>
        <div class="roles-block">
          <strong>نقش‌ها و دسترسی‌ها</strong>
          <p>با انتخاب نقش، دسترسی‌های مرتبط با آن نقش در پنل فعال می‌شود.</p>
          <div class="roles-grid">
            <label v-for="role in roles" :key="role" class="role-option"><input v-model="form.roles" type="checkbox" :value="role" />{{ role }}</label>
          </div>
        </div>
        <label class="check-row"><input v-model="form.enabled" type="checkbox" /> کاربر فعال باشد و بتواند وارد سیستم شود</label>
        <div class="form-actions">
          <button class="primary-btn" type="button" :disabled="saving" @click="saveUser">{{ saving ? 'در حال ذخیره...' : 'ذخیره کاربر' }}</button>
          <button class="secondary-btn" type="button" @click="startNew">پاک کردن فرم</button>
          <button v-if="form.name && form.name !== currentUser" class="danger-btn" type="button" :disabled="saving" @click="removeUser">حذف کاربر</button>
        </div>
      </ManagementSurfaceCard>
    </div>
  </ManagementPageScaffold>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import ManagementCollectionView from '@/components/management/ManagementCollectionView.vue'
import ManagementGalleryView from '@/components/management/ManagementGalleryView.vue'
import ManagementListView from '@/components/management/ManagementListView.vue'
import ManagementNotionListView from '@/components/management/ManagementNotionListView.vue'
import ManagementPageScaffold from '@/components/management/ManagementPageScaffold.vue'
import ManagementSurfaceCard from '@/components/management/ManagementSurfaceCard.vue'
import { deleteManagementUser, listManagementUsers, saveManagementUser } from '@/utils/api'
import { parseQuery } from '@/utils/format'

const props = defineProps({ detailOnly: { type: Boolean, default: false } })
const detailOnly = computed(() => Boolean(props.detailOnly))
const query = parseQuery()
const detailUserName = ref(String(query.name || query.user || query.email || '').trim())
const viewMode = ref(String(query.view || 'table').trim() || 'table')

const users = ref([])
const roles = ref([])
const search = ref('')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const currentUser = typeof window !== 'undefined' ? String(window._BOOT?.user || window._BOOT?.user_email || '').trim() : ''
const form = reactive(createForm())

const userColumns = [
  { key: 'full_name', label: 'نام کاربر' },
  { key: 'email', label: 'ایمیل' },
  { key: 'enabled', label: 'وضعیت' },
  { key: 'roles', label: 'نقش‌ها' },
  { key: 'actions', label: 'عملیات' },
]
const userViewModes = [
  { value: 'table', label: 'جدول', icon: '☷' },
  { value: 'list', label: 'لیست', icon: '≡' },
  { value: 'gallery', label: 'گالری', icon: '▦' },
]
const userChipRenderers = {
  enabled: (row) => ({ text: row.enabled ? 'فعال' : 'غیرفعال', cls: row.enabled ? 'chip-ok' : 'chip-danger' }),
  roles: (row) => ({ text: row.roles?.join('، ') || 'بدون نقش', cls: '' }),
}

function createForm() {
  return { name: '', email: '', full_name: '', mobile_no: '', new_password: '', enabled: true, roles: [] }
}
function startNew() { Object.assign(form, createForm()) }
function openNewUser() { window.location.href = '/management/user' }
function openUserDetail(user) {
  const name = String(user?.name || '').trim()
  if (name) window.location.href = `/management/user?name=${encodeURIComponent(name)}`
}
function editUser(user) { Object.assign(form, { ...createForm(), ...user, roles: [...(user.roles || [])], enabled: Boolean(user.enabled) }) }
async function loadUsers() {
  loading.value = true; error.value = ''
  try { const payload = await listManagementUsers({ search: search.value }); users.value = payload?.users || []; roles.value = payload?.roles || [] }
  catch (err) { error.value = err?.message || 'بارگذاری کاربران ناموفق بود.' }
  finally { loading.value = false }
}
async function saveUser() {
  if (!form.email || (!form.name && form.new_password.length < 8)) { error.value = 'ایمیل و رمز عبور حداقل ۸ کاراکتری الزامی است.'; return }
  saving.value = true; error.value = ''; success.value = ''
  try { await saveManagementUser({ ...form }); success.value = 'کاربر با موفقیت ذخیره شد.'; startNew(); await loadUsers() }
  catch (err) { error.value = err?.message || 'ذخیره کاربر ناموفق بود.' }
  finally { saving.value = false }
}
async function removeUser() {
  if (!window.confirm(`کاربر «${form.full_name || form.email}» حذف شود؟`)) return
  saving.value = true; error.value = ''
  try { await deleteManagementUser(form.name); success.value = 'کاربر حذف شد.'; startNew(); await loadUsers() }
  catch (err) { error.value = err?.message || 'حذف کاربر ناموفق بود.' }
  finally { saving.value = false }
}
onMounted(async () => {
  await loadUsers()
  if (detailOnly.value && detailUserName.value) {
    const user = users.value.find((row) => String(row.name || '') === detailUserName.value || String(row.email || '') === detailUserName.value)
    if (user) editUser(user)
    else error.value = 'کاربر موردنظر پیدا نشد.'
  }
})
</script>

<style scoped>
.users-layout { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(360px, .95fr); gap: 1rem; }
.users-layout--detail { grid-template-columns: minmax(0, 1fr); }
.toolbar-row, .form-actions { display: flex; gap: .65rem; align-items: center; flex-wrap: wrap; margin-bottom: 1rem; }
.user-list { display: grid; gap: .5rem; max-height: 620px; overflow: auto; }
.user-row { width: 100%; display: flex; align-items: center; gap: .75rem; border: 1px solid var(--mg-border-light); border-radius: var(--mg-radius-sm); padding: .75rem; background: transparent; color: var(--mg-text-main); text-align: right; cursor: pointer; transition: .2s ease; }
.user-row:hover, .user-row.selected { background: var(--mg-bg-page); border-color: var(--mg-primary); }
.avatar { flex: 0 0 2.35rem; height: 2.35rem; display: grid; place-items: center; border-radius: 50%; background: var(--mg-primary); color: white; font-weight: 800; }
.user-main, .user-meta { display: grid; gap: .2rem; min-width: 0; }
.user-main { flex: 1; } .user-main strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; } .user-row small { color: var(--mg-text-muted); font-size: .72rem; }
.user-meta { text-align: left; justify-items: end; } .status-pill { border-radius: 999px; padding: .2rem .5rem; font-size: .7rem; font-weight: 800; } .status-pill.active { background: var(--mg-success-bg); color: var(--mg-success); } .status-pill.disabled { background: var(--mg-danger-bg); color: var(--mg-danger); }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; } label { display: grid; gap: .4rem; color: var(--mg-text-muted); font-size: .82rem; }
.roles-block { margin: 1.25rem 0; padding-top: 1rem; border-top: 1px solid var(--mg-border-light); } .roles-block strong { color: var(--mg-text-main); } .roles-block p { color: var(--mg-text-muted); font-size: .8rem; margin: .35rem 0 .8rem; }
.roles-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .5rem; } .role-option, .check-row { display: flex; align-items: center; gap: .5rem; padding: .55rem; border: 1px solid var(--mg-border-light); border-radius: var(--mg-radius-sm); }
.empty { color: var(--mg-text-muted); text-align: center; padding: 2rem; } .danger-btn { background: var(--mg-danger); color: #fff; border: 0; border-radius: var(--mg-radius-sm); padding: .7rem 1rem; cursor: pointer; }
@media (max-width: 800px) { .users-layout, .form-grid { grid-template-columns: 1fr; } .roles-grid { grid-template-columns: 1fr; } }
</style>
