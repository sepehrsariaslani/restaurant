<template>
  <div class="branches-page" dir="rtl">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">شعبه‌های ما</h1>
      <div style="width:40px"></div>
    </div>

    <div class="branches-list">
      <div v-for="branch in branches" :key="branch.id" class="branch-card">
        <div class="branch-img-wrap">
          <img :src="branch.image" :alt="branch.name" loading="lazy" />
          <span class="branch-status" :class="branch.isOpen ? 'open' : 'closed'">
            {{ branch.isOpen ? '● باز' : '● بسته' }}
          </span>
        </div>
        <div class="branch-body">
          <h3 class="branch-name">{{ branch.name }}</h3>
          <p class="branch-address">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            {{ branch.address }}
          </p>
          <p class="branch-hours">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
            {{ branch.hours }}
          </p>
          <p class="branch-phone" v-if="branch.phone">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 9.81 19.79 19.79 0 0 1 1.61 1.18 2 2 0 0 1 3.61 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 8.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            <a :href="`tel:${branch.phone}`" class="phone-link">{{ branch.phone }}</a>
          </p>
          <div class="branch-actions">
            <a :href="branch.mapUrl" class="branch-map-btn" target="_blank" rel="noopener">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>
              مسیریابی
            </a>
            <a href="/menu" class="branch-order-btn">سفارش از این شعبه</a>
          </div>
        </div>
      </div>
    </div>
    <div class="bottom-spacer"></div>
  </div>
</template>

<script setup>
function goBack() { window.history.back() }

const branches = [
  {
    id: 1,
    name: 'شعبه مرکزی',
    address: 'تهران، خیابان ولیعصر، پلاک ۱۲۳',
    hours: 'شنبه تا پنجشنبه ۱۲:۰۰ – ۲۳:۰۰',
    phone: '۰۲۱-۱۲۳۴۵۶۷۸',
    isOpen: true,
    mapUrl: 'https://maps.google.com',
    image: 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&auto=format&fit=crop&q=70',
  },
  {
    id: 2,
    name: 'شعبه شمال',
    address: 'تهران، الهیه، خیابان فرشته، پلاک ۴۵',
    hours: 'همه روزه ۱۱:۰۰ – ۲۴:۰۰',
    phone: '۰۲۱-۸۷۶۵۴۳۲۱',
    isOpen: true,
    mapUrl: 'https://maps.google.com',
    image: 'https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=70',
  },
  {
    id: 3,
    name: 'شعبه غرب',
    address: 'تهران، پونک، خیابان اشرفی اصفهانی، پلاک ۶۷',
    hours: 'دوشنبه تا جمعه ۱۳:۰۰ – ۲۲:۰۰',
    phone: '۰۲۱-۱۱۲۲۳۳۴۴',
    isOpen: false,
    mapUrl: 'https://maps.google.com',
    image: 'https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=600&auto=format&fit=crop&q=70',
  },
]
</script>

<style scoped>
.branches-page { min-height: 100vh; background: #f7f0e8; direction: rtl; padding-bottom: 3rem; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 3.5rem 1rem 1rem; background: #fff; border-bottom: 1px solid #ede3d8;
}
.back-btn { width: 40px; height: 40px; border-radius: 50%; background: #f7f0e8; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #3f2a1d; }
.page-title { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; margin: 0; }

.branches-list { display: flex; flex-direction: column; gap: 1.1rem; padding: 1.25rem; }
.branch-card { background: #fff; border-radius: 24px; overflow: hidden; box-shadow: 0 4px 16px rgba(0,0,0,0.07); }

.branch-img-wrap { position: relative; height: 160px; overflow: hidden; }
.branch-img-wrap img { width: 100%; height: 100%; object-fit: cover; }
.branch-status {
  position: absolute; top: 12px; right: 12px;
  font-size: 0.75rem; font-weight: 700; border-radius: 999px; padding: 4px 10px;
}
.branch-status.open { background: rgba(46,125,50,0.9); color: #fff; }
.branch-status.closed { background: rgba(183,28,28,0.9); color: #fff; }

.branch-body { padding: 1.2rem; }
.branch-name { font-size: 1.05rem; font-weight: 800; color: #3f2a1d; margin: 0 0 0.75rem; }
.branch-address, .branch-hours, .branch-phone {
  display: flex; align-items: flex-start; gap: 0.5rem;
  font-size: 0.83rem; color: #846b58; margin: 0 0 0.45rem;
}
.phone-link { color: #6f4a31; font-weight: 600; text-decoration: none; }

.branch-actions { display: flex; gap: 0.75rem; margin-top: 1rem; }
.branch-map-btn {
  display: flex; align-items: center; gap: 0.4rem;
  border: 1.5px solid #6f4a31; border-radius: 12px; padding: 0.65rem 1rem;
  color: #6f4a31; font-size: 0.85rem; font-weight: 700; text-decoration: none;
}
.branch-order-btn {
  flex: 1; display: flex; align-items: center; justify-content: center;
  background: #6f4a31; border-radius: 12px; padding: 0.65rem 1rem;
  color: #fff; font-size: 0.85rem; font-weight: 700; text-decoration: none;
}

.bottom-spacer { height: 2rem; }
</style>
