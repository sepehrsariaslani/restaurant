<template>
  <section class="order-flow-page">
    <header class="order-flow-hero">
      <div>
        <p class="order-flow-eyebrow">شروع سفارش</p>
        <h1 class="order-flow-title">از همین‌جا سفارش جدید را شروع کنید</h1>
        <p class="order-flow-subtitle">مسیر سفارش مرحله‌به‌مرحله طراحی شده تا همیشه بدانید سفارش برای کجاست، چه زمانی آماده می‌شود، چقدر پرداخت می‌کنید و قدم بعدی چیست.</p>
      </div>
      <div class="order-flow-actions">
        <a class="order-flow-primary" href="/order/type">شروع سفارش جدید</a>
        <a class="order-flow-secondary" :href="trackUrl">پیگیری سفارش</a>
      </div>
    </header>

    <section class="order-flow-context-grid">
      <div class="order-flow-fact"><small>۱</small><strong>نوع سفارش را انتخاب کنید</strong></div>
      <div class="order-flow-fact"><small>۲</small><strong>شعبه، میز یا آدرس را مشخص کنید</strong></div>
      <div class="order-flow-fact"><small>۳</small><strong>منو را ببینید و سبد را بسازید</strong></div>
      <div class="order-flow-fact"><small>۴</small><strong>پرداخت و پیگیری سفارش</strong></div>
    </section>

    <div class="order-flow-grid">
      <article class="order-flow-card order-flow-card--selectable">
        <div class="order-flow-card-head">
          <div>
            <h2>سفارش جدید</h2>
            <p>حضوری، بیرون‌بر یا ارسال را انتخاب کنید.</p>
          </div>
          <span class="order-flow-icon"><Plus :size="24" /></span>
        </div>
        <a class="order-flow-primary" href="/order/type">شروع سفارش جدید</a>
      </article>

      <article class="order-flow-card order-flow-card--selectable">
        <div class="order-flow-card-head">
          <div>
            <h2>تکرار سفارش قبلی</h2>
            <p>از سفارش‌های اخیر استفاده کنید و سریع‌تر سفارش دهید.</p>
          </div>
          <span class="order-flow-icon"><RotateCcw :size="24" /></span>
        </div>
        <a class="order-flow-secondary" href="/customer/orders">مشاهده سفارش‌های قبلی</a>
      </article>

      <article class="order-flow-card order-flow-card--selectable">
        <div class="order-flow-card-head">
          <div>
            <h2>پیگیری سفارش</h2>
            <p>اگر سفارش فعالی دارید، وضعیت آن را دنبال کنید.</p>
          </div>
          <span class="order-flow-icon"><MapPinned :size="24" /></span>
        </div>
        <a class="order-flow-secondary" :href="trackUrl">پیگیری سفارش</a>
      </article>
    </div>

    <div class="order-flow-grid order-flow-grid--2" style="margin-top:1rem">
      <article class="order-flow-card">
        <h2>آدرس‌های ذخیره‌شده</h2>
        <p>برای سفارش ارسال، آدرس‌های خود را مدیریت کنید.</p>
        <a class="order-flow-secondary" href="/customer/addresses">مدیریت آدرس‌ها</a>
      </article>
      <article class="order-flow-card">
        <h2>سفارش‌های اخیر</h2>
        <p>تاریخچه سفارش‌ها و جزئیات پرداخت را ببینید.</p>
        <a class="order-flow-secondary" href="/customer/orders">مشاهده سفارش‌ها</a>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { MapPinned, Plus, RotateCcw } from 'lucide-vue-next'
import { cartState } from '@/stores/cartStore'
import './orderFlow.css'

const trackUrl = computed(() => {
  const code = cartState.lastOrder?.order_code
  const mobile = cartState.lastOrder?.mobile
  return code && mobile ? `/order-success/${encodeURIComponent(code)}?mobile=${encodeURIComponent(mobile)}` : '/customer/orders'
})
</script>
