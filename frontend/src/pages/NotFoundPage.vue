<template>
  <div class="notfound-page" dir="rtl">
    <div class="nf-body">

      <div class="nf-illustration">
        <div class="nf-plate">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#c4a882" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M8.56 2.75c4.37 6.03 6.02 9.42 8.03 17.72m2.54-15.38c-3.72 4.35-8.94 5.66-16.88 5.85m19.5 1.9c-3.5-3.92-7.47-6.98-13-8.3"/>
          </svg>
        </div>
        <div class="nf-number">۴۰۴</div>
      </div>

      <h1 class="nf-title">صفحه پیدا نشد</h1>
      <p class="nf-sub">این صفحه وجود ندارد یا آدرس نادرست است.</p>

      <div class="nf-actions">
        <a href="/" class="primary-btn">🏠 برگشت به خانه</a>
        <a href="/menu" class="secondary-btn">مشاهده منو</a>
      </div>

      <div class="nf-quick">
        <p>یا از اینجا برو:</p>
        <div class="nf-links">
          <a href="/customer/dashboard">داشبورد</a>
          <a href="/customer/orders">سفارش‌ها</a>
          <a href="/table-reservation">رزرو میز</a>
          <a href="/search">جستجو</a>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.notfound-page {
  min-height: 100vh;
  background: #f7f0e8;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.nf-body {
  max-width: 400px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.1rem;
  text-align: center;
}

.nf-illustration {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.nf-plate {
  width: 120px;
  height: 120px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(111,74,49,0.12);
}

.nf-number {
  position: absolute;
  bottom: -12px;
  background: #6f4a31;
  color: #fff;
  font-size: 1.1rem;
  font-weight: 800;
  padding: 0.25rem 0.9rem;
  border-radius: 20px;
  letter-spacing: 0.1em;
}

.nf-title {
  font-size: 1.8rem;
  font-weight: 800;
  color: #3f2a1d;
  margin: 0.5rem 0 0;
}

.nf-sub {
  color: #9e8878;
  font-size: 0.95rem;
  margin: 0;
  line-height: 1.6;
}

.nf-actions {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  width: 100%;
  margin-top: 0.25rem;
}

.primary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  background: #6f4a31;
  color: #fff;
  padding: 0.9rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 700;
  font-size: 0.97rem;
  transition: background 0.2s;
}
.primary-btn:hover { background: #5a3a27; }

.secondary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  color: #6f4a31;
  padding: 0.85rem;
  border-radius: 12px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.92rem;
  border: 1.5px solid #c4a882;
  transition: background 0.2s;
}
.secondary-btn:hover { background: #fdf5ee; }

.nf-quick {
  margin-top: 0.5rem;
  width: 100%;
}

.nf-quick p {
  font-size: 0.83rem;
  color: #b0998a;
  margin: 0 0 0.65rem;
}

.nf-links {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.nf-links a {
  background: #fff;
  color: #6f4a31;
  border: 1px solid #e8ddd3;
  border-radius: 20px;
  padding: 0.4rem 0.9rem;
  font-size: 0.85rem;
  text-decoration: none;
  transition: background 0.15s;
}
.nf-links a:hover { background: #fdf5ee; }
</style>
