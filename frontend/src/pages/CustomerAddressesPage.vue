<template>
  <div class="addresses-page" dir="rtl">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">آدرس‌های من</h1>
      <button class="add-btn-header" @click="openAddForm">+ جدید</button>
    </div>

    <div class="content-area">
      <div v-if="addresses.length === 0" class="empty-state">
        <div class="empty-icon">📍</div>
        <h3>آدرسی ثبت نشده</h3>
        <p>آدرس تحویل سفارش‌هایتان را اینجا ذخیره کنید</p>
        <button class="primary-btn" @click="openAddForm">+ افزودن آدرس جدید</button>
      </div>

      <div v-else class="address-list">
        <div
          v-for="addr in addresses"
          :key="addr.id"
          class="address-card"
          :class="{ selected: selectedId === addr.id }"
          @click="selectedId = addr.id"
        >
          <div class="addr-radio">
            <div class="radio-dot" :class="{ active: selectedId === addr.id }"></div>
          </div>
          <div class="addr-body">
            <div class="addr-top">
              <span class="addr-label">{{ addr.label }}</span>
              <span class="addr-type-chip">{{ addr.type }}</span>
            </div>
            <p class="addr-text">{{ addr.address }}</p>
            <p class="addr-detail" v-if="addr.detail">{{ addr.detail }}</p>
          </div>
          <div class="addr-actions">
            <button class="icon-btn" @click.stop="editAddress(addr)" title="ویرایش">✎</button>
            <button class="icon-btn danger" @click.stop="deleteAddress(addr.id)" title="حذف">✕</button>
          </div>
        </div>

        <button class="add-address-row" @click="openAddForm">
          <span>+</span>
          افزودن آدرس جدید
        </button>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="showForm" @click.self="closeForm">
        <div class="modal-sheet" dir="rtl">
          <div class="modal-handle"></div>
          <h3 class="modal-title">{{ editingId ? 'ویرایش آدرس' : 'آدرس جدید' }}</h3>

          <div class="form-group">
            <label>برچسب آدرس</label>
            <div class="chip-select">
              <button v-for="t in types" :key="t" class="type-chip" :class="{ active: newAddr.type === t }" @click="newAddr.type = t">{{ t }}</button>
            </div>
          </div>
          <div class="form-group">
            <label>نام یا عنوان</label>
            <input class="form-input" v-model="newAddr.label" placeholder="مثلاً: خانه، محل کار" />
          </div>
          <div class="form-group">
            <label>آدرس کامل</label>
            <textarea class="form-input" v-model="newAddr.address" placeholder="شهر، خیابان، کوچه..." rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>واحد / طبقه / جزئیات بیشتر</label>
            <input class="form-input" v-model="newAddr.detail" placeholder="مثلاً: واحد ۳" />
          </div>

          <div class="modal-actions">
            <button class="cancel-btn" @click="closeForm">انصراف</button>
            <button class="save-btn" @click="saveAddress" :disabled="!newAddr.address.trim()">ذخیره</button>
          </div>
        </div>
      </div>
    </Teleport>

    <div class="bottom-cta" v-if="addresses.length > 0">
      <button class="confirm-btn" @click="confirmSelection">تأیید این آدرس</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const STORAGE_KEY = 'customer_addresses_v1'
function loadAddresses() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') } catch { return [] } }
function saveAddresses(list) { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(list)) } catch {} }

const addresses = ref(loadAddresses())
const selectedId = ref(addresses.value[0]?.id || null)
const showForm = ref(false)
const editingId = ref(null)
const types = ['خانه', 'محل کار', 'سایر']

const newAddr = ref({ label: 'خانه', type: 'خانه', address: '', detail: '' })

function goBack() { window.history.back() }

function openAddForm() {
  editingId.value = null
  newAddr.value = { label: 'خانه', type: 'خانه', address: '', detail: '' }
  showForm.value = true
}

function editAddress(addr) {
  editingId.value = addr.id
  newAddr.value = { ...addr }
  showForm.value = true
}

function closeForm() { showForm.value = false; editingId.value = null }

function saveAddress() {
  if (!newAddr.value.address.trim()) return
  if (editingId.value) {
    const idx = addresses.value.findIndex(a => a.id === editingId.value)
    if (idx >= 0) addresses.value[idx] = { ...newAddr.value, id: editingId.value }
  } else {
    addresses.value.push({ ...newAddr.value, id: Date.now() })
  }
  saveAddresses(addresses.value)
  closeForm()
}

function deleteAddress(id) {
  if (!confirm('این آدرس حذف شود؟')) return
  addresses.value = addresses.value.filter(a => a.id !== id)
  if (selectedId.value === id) selectedId.value = addresses.value[0]?.id || null
  saveAddresses(addresses.value)
}

function confirmSelection() {
  const addr = addresses.value.find(a => a.id === selectedId.value)
  if (addr) {
    try { localStorage.setItem('selected_address', JSON.stringify(addr)) } catch {}
    window.history.back()
  }
}
</script>

<style scoped>
.addresses-page { min-height: 100vh; background: #f7f0e8; direction: rtl; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 3.5rem 1rem 1rem; background: #fff; border-bottom: 1px solid #ede3d8;
}
.back-btn { width: 40px; height: 40px; border-radius: 50%; background: #f7f0e8; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #3f2a1d; }
.page-title { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; margin: 0; }
.add-btn-header { background: #6f4a31; color: #fff; border: none; border-radius: 12px; padding: 0.5rem 0.9rem; font-size: 0.85rem; font-weight: 700; font-family: inherit; cursor: pointer; }

.content-area { padding: 1.25rem; padding-bottom: 8rem; }

.empty-state { text-align: center; padding: 4rem 2rem; }
.empty-icon { font-size: 3.5rem; margin-bottom: 1rem; }
.empty-state h3 { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; margin: 0 0 0.5rem; }
.empty-state p { color: #846b58; font-size: 0.88rem; margin: 0 0 2rem; }
.primary-btn { background: #6f4a31; color: #fff; border: none; border-radius: 16px; padding: 0.9rem 2rem; font-size: 0.95rem; font-weight: 700; font-family: inherit; cursor: pointer; }

.address-list { display: flex; flex-direction: column; gap: 0.75rem; }
.address-card {
  background: #fff; border-radius: 20px; padding: 1rem 1.1rem;
  display: flex; align-items: flex-start; gap: 0.9rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
  border: 2px solid transparent; transition: border-color 0.2s; cursor: pointer;
}
.address-card.selected { border-color: #6f4a31; }

.addr-radio { padding-top: 0.1rem; flex-shrink: 0; }
.radio-dot { width: 20px; height: 20px; border-radius: 50%; border: 2px solid #c5b09a; transition: all 0.2s; }
.radio-dot.active { background: #6f4a31; border-color: #6f4a31; }

.addr-body { flex: 1; min-width: 0; }
.addr-top { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem; }
.addr-label { font-size: 0.9rem; font-weight: 700; color: #3f2a1d; }
.addr-type-chip { font-size: 0.7rem; background: #f1e7db; color: #846b58; border-radius: 999px; padding: 2px 8px; }
.addr-text { font-size: 0.83rem; color: #3f2a1d; margin: 0 0 0.2rem; line-height: 1.5; }
.addr-detail { font-size: 0.78rem; color: #846b58; margin: 0; }

.addr-actions { display: flex; flex-direction: column; gap: 0.3rem; flex-shrink: 0; }
.icon-btn { width: 30px; height: 30px; border-radius: 8px; border: 1px solid #e5ddd4; background: #fdf8f1; cursor: pointer; font-size: 0.9rem; display: flex; align-items: center; justify-content: center; }
.icon-btn.danger { border-color: #ffcdd2; background: #fff5f5; color: #e74c3c; }

.add-address-row {
  display: flex; align-items: center; gap: 0.75rem; justify-content: center;
  background: #fff; border-radius: 20px; border: 2px dashed #c5b09a;
  padding: 1rem; color: #6f4a31; font-size: 0.9rem; font-weight: 700;
  font-family: inherit; cursor: pointer; gap: 0.4rem;
}

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 200; display: flex; align-items: flex-end; }
.modal-sheet { background: #fff; border-radius: 28px 28px 0 0; width: 100%; padding: 1.5rem 1.5rem 3rem; max-height: 90vh; overflow-y: auto; }
.modal-handle { width: 36px; height: 4px; background: #e5ddd4; border-radius: 2px; margin: 0 auto 1.5rem; }
.modal-title { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; margin: 0 0 1.5rem; }

.form-group { margin-bottom: 1.1rem; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 700; color: #846b58; margin-bottom: 0.45rem; }
.form-input { width: 100%; padding: 0.85rem 1rem; border: 1.5px solid #e5ddd4; border-radius: 14px; background: #fdf8f1; font-size: 0.92rem; font-family: inherit; outline: none; box-sizing: border-box; resize: none; }
.form-input:focus { border-color: #6f4a31; }

.chip-select { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.type-chip { padding: 0.4rem 0.9rem; border-radius: 999px; border: 1.5px solid #e5ddd4; background: #fdf8f1; font-family: inherit; font-size: 0.85rem; cursor: pointer; font-weight: 600; color: #846b58; transition: all 0.2s; }
.type-chip.active { background: #6f4a31; border-color: #6f4a31; color: #fff; }

.modal-actions { display: flex; gap: 0.75rem; margin-top: 1.5rem; }
.cancel-btn { flex: 1; padding: 0.9rem; border: 1.5px solid #e5ddd4; border-radius: 14px; background: #fdf8f1; color: #3f2a1d; font-size: 0.95rem; font-weight: 700; font-family: inherit; cursor: pointer; }
.save-btn { flex: 2; padding: 0.9rem; background: #6f4a31; border: none; border-radius: 14px; color: #fff; font-size: 0.95rem; font-weight: 700; font-family: inherit; cursor: pointer; }
.save-btn:disabled { opacity: 0.5; }

.bottom-cta { position: fixed; bottom: 0; left: 0; right: 0; padding: 1rem; background: rgba(247,240,232,0.95); backdrop-filter: blur(8px); border-top: 1px solid #ede3d8; }
.confirm-btn { width: 100%; padding: 1rem; background: #6f4a31; color: #fff; border: none; border-radius: 16px; font-size: 1rem; font-weight: 700; font-family: inherit; cursor: pointer; }
</style>
