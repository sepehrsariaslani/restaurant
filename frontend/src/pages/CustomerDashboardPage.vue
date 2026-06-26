<template>
  <div class="dashboard-page" dir="rtl">
    <!-- Hero Header -->
    <div class="dash-hero">
      <div class="hero-top-bar">
        <div class="hero-greeting">
          <p class="greeting-sub">خوش آمدید 👋</p>
          <h2 class="greeting-name">{{ customerName }}</h2>
        </div>
        <a href="/customer/profile" class="profile-avatar" aria-label="پروفایل">
          <span>{{ avatarLetter }}</span>
        </a>
      </div>

      <div class="search-bar" @click="goMenu">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <span class="search-placeholder">جستجو در منو...</span>
      </div>
    </div>

    <!-- Order Type Cards -->
    <div class="order-types">
      <a href="/delivery" class="order-type-card">
        <div class="ot-icon">🛵</div>
        <div class="ot-info">
          <strong>تحویل درب منزل</strong>
          <small>تا ۴۵ دقیقه</small>
        </div>
        <svg class="ot-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
      </a>
      <a href="/delivery?type=pickup" class="order-type-card">
        <div class="ot-icon">🏃</div>
        <div class="ot-info">
          <strong>بیرون‌بر</strong>
          <small>آماده در ۲۰ دقیقه</small>
        </div>
        <svg class="ot-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
      </a>
      <a href="/table-reservation" class="order-type-card">
        <div class="ot-icon">🍽️</div>
        <div class="ot-info">
          <strong>رزرو میز</strong>
          <small>حضوری</small>
        </div>
        <svg class="ot-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
      </a>
    </div>

    <!-- Quick Actions -->
    <div class="section-header">
      <h3>دسترسی سریع</h3>
    </div>
    <div class="quick-grid">
      <a href="/menu" class="quick-card">
        <span class="qc-icon">📋</span>
        <span class="qc-label">منو</span>
      </a>
      <a href="/customer/addresses" class="quick-card">
        <span class="qc-icon">📍</span>
        <span class="qc-label">آدرس‌ها</span>
      </a>
      <a href="/customer/branches" class="quick-card">
        <span class="qc-icon">🏪</span>
        <span class="qc-label">شعبه‌ها</span>
      </a>
      <a href="/customer/orders" class="quick-card">
        <span class="qc-icon">🧾</span>
        <span class="qc-label">سفارش‌ها</span>
      </a>
      <a href="/cart" class="quick-card">
        <span class="qc-icon">🛒</span>
        <span class="qc-label">سبد خرید</span>
        <i v-if="cartCount > 0" class="qc-badge">{{ cartCount }}</i>
      </a>
    </div>

    <!-- Special Offers -->
    <div class="section-header">
      <h3>پیشنهادات ویژه</h3>
      <a href="/menu" class="see-all">مشاهده همه</a>
    </div>
    <div class="offers-scroll">
      <a v-for="offer in specialOffers" :key="offer.id" href="/menu" class="offer-card">
        <div class="offer-img-wrap">
          <img :src="offer.image" :alt="offer.title" loading="lazy" />
          <span class="offer-badge" v-if="offer.discount">{{ offer.discount }}٪ تخفیف</span>
        </div>
        <div class="offer-body">
          <strong>{{ offer.title }}</strong>
          <p>{{ offer.subtitle }}</p>
        </div>
      </a>
    </div>

    <div class="bottom-spacer"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { cartState } from '@/stores/cartStore'
import { getCustomerProfile, getMenuItems } from '@/utils/api'

const CUSTOMER_AUTH_KEY = 'restaurant-customer-auth-v1'
const cartCount = computed(() => cartState.lines.reduce((s, l) => s + (Number(l.qty) || 0), 0))
const customer = ref({ name: '', mobile: '' })
const orders = ref([])
const specialOffers = ref([])

const customerName = computed(() => customer.value.name || 'مهمان عزیز')

const avatarLetter = computed(() => {
  const name = customerName.value
  return name !== 'مهمان عزیز' ? name.slice(0, 1) : '👤'
})

function goMenu() { window.location.href = '/search' }

function readAuth() {
  try {
    const auth = JSON.parse(localStorage.getItem(CUSTOMER_AUTH_KEY) || '{}')
    return {
      mobile: auth.mobile || localStorage.getItem('customer_phone') || '',
      name: auth.customer_name || localStorage.getItem('customer_name') || '',
    }
  } catch { return { mobile: '', name: '' } }
}

onMounted(async () => {
  const auth = readAuth()
  customer.value = { name: auth.name, mobile: auth.mobile }
  if (auth.mobile) {
    try {
      const profile = await getCustomerProfile({ mobile: auth.mobile })
      customer.value = profile?.customer || customer.value
      orders.value = profile?.orders || []
      if (customer.value.name) localStorage.setItem('customer_name', customer.value.name)
    } catch {}
  }
  try {
    const menu = await getMenuItems({ page_size: 6 })
    specialOffers.value = (menu?.items || []).slice(0, 6).map(item => ({
      id: item.slug || item.name,
      title: item.title,
      subtitle: item.short_desc || item.category_title || 'پیشنهاد امروز',
      discount: 0,
      image: item.image || 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&auto=format&fit=crop&q=60',
    }))
  } catch {}
})
</script>

<style scoped>
.dashboard-page { min-height: 100vh; background: #f7f0e8; padding-bottom: 7rem; direction: rtl; }

.dash-hero {
  background: linear-gradient(135deg, #3f2a1d 0%, #6f4a31 100%);
  padding: 3.5rem 1.25rem 2rem;
  position: relative;
  overflow: hidden;
}
.dash-hero::before {
  content: ''; position: absolute; top: -50px; right: -50px;
  width: 220px; height: 220px; border-radius: 50%;
  background: rgba(255,255,255,0.06);
}

.hero-top-bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.4rem; }
.greeting-sub { margin: 0; font-size: 0.82rem; color: rgba(255,255,255,0.65); }
.greeting-name { margin: 0.15rem 0 0; font-size: 1.2rem; font-weight: 800; color: #fff; }
.profile-avatar {
  width: 46px; height: 46px; border-radius: 50%;
  background: rgba(255,255,255,0.2); border: 2px solid rgba(255,255,255,0.4);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; color: #fff; text-decoration: none; font-weight: 700;
}

.search-bar {
  display: flex; align-items: center; gap: 0.75rem;
  background: rgba(255,255,255,0.13); backdrop-filter: blur(8px);
  border: 1px solid rgba(255,255,255,0.22); border-radius: 16px;
  padding: 0.85rem 1.1rem; cursor: pointer;
  color: rgba(255,255,255,0.7);
}
.search-placeholder { font-size: 0.9rem; color: rgba(255,255,255,0.55); }

.order-types {
  display: flex; flex-direction: column; gap: 0.65rem;
  padding: 1.4rem 1.25rem 0; margin-top: -18px; position: relative; z-index: 2;
}
.order-type-card {
  display: flex; align-items: center; gap: 0.9rem;
  background: #fff; border-radius: 18px; padding: 1rem 1.1rem;
  box-shadow: 0 4px 16px rgba(0,0,0,0.07); text-decoration: none; color: inherit;
  transition: transform 0.15s;
}
.order-type-card:active { transform: scale(0.98); }
.ot-icon { font-size: 1.5rem; flex-shrink: 0; }
.ot-info { flex: 1; }
.ot-info strong { display: block; font-size: 0.95rem; font-weight: 700; color: #3f2a1d; }
.ot-info small { font-size: 0.78rem; color: #846b58; }
.ot-arrow { color: #c5b09a; flex-shrink: 0; }

.section-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1.5rem 1.25rem 0.75rem;
}
.section-header h3 { margin: 0; font-size: 1rem; font-weight: 800; color: #3f2a1d; }
.see-all { font-size: 0.82rem; color: #6f4a31; font-weight: 600; text-decoration: none; }

.quick-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.7rem; padding: 0 1.25rem; }
.quick-card {
  background: #fff; border-radius: 18px; padding: 1rem 0.5rem;
  display: flex; flex-direction: column; align-items: center; gap: 0.4rem;
  text-decoration: none; position: relative;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06); transition: transform 0.15s;
}
.quick-card:active { transform: scale(0.96); }
.qc-icon { font-size: 1.6rem; }
.qc-label { font-size: 0.7rem; font-weight: 700; color: #3f2a1d; text-align: center; }
.qc-badge {
  position: absolute; top: 6px; left: 6px; background: #e74c3c; color: #fff;
  border-radius: 999px; font-size: 0.62rem; font-weight: 700; padding: 2px 5px; font-style: normal;
}

.offers-scroll { display: flex; gap: 0.85rem; padding: 0 1.25rem; overflow-x: auto; scrollbar-width: none; }
.offers-scroll::-webkit-scrollbar { display: none; }
.offer-card {
  background: #fff; border-radius: 20px; overflow: hidden;
  min-width: 175px; box-shadow: 0 4px 14px rgba(0,0,0,0.08); flex-shrink: 0;
  text-decoration: none; color: inherit;
}
.offer-img-wrap { position: relative; height: 110px; overflow: hidden; }
.offer-img-wrap img { width: 100%; height: 100%; object-fit: cover; }
.offer-badge {
  position: absolute; top: 8px; right: 8px; background: #e74c3c; color: #fff;
  font-size: 0.7rem; font-weight: 700; padding: 3px 8px; border-radius: 999px;
}
.offer-body { padding: 0.7rem 0.85rem; }
.offer-body strong { font-size: 0.88rem; font-weight: 700; color: #3f2a1d; display: block; }
.offer-body p { font-size: 0.75rem; color: #846b58; margin: 0.2rem 0 0; }

@media (max-width: 380px) { .quick-grid { grid-template-columns: repeat(4, 1fr); } }
.bottom-spacer { height: 2rem; }
</style>
