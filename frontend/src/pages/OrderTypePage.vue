<template>
  <section class="order-flow-page">
    <header class="order-flow-hero">
      <div>
        <p class="order-flow-eyebrow">انتخاب نوع سفارش</p>
        <h1 class="order-flow-title">سفارش را چطور دریافت می‌کنید؟</h1>
        <p class="order-flow-subtitle">انتخاب این مرحله روی شعبه، آدرس، هزینه ارسال و روند پیگیری سفارش اثر می‌گذارد.</p>
      </div>
      <a class="order-flow-secondary" href="/order/start">بازگشت</a>
    </header>

    <div class="order-flow-grid">
      <article class="order-flow-card order-flow-card--selectable">
        <div class="order-flow-card-head">
          <div>
            <h2>حضوری</h2>
            <p>برای سفارش روی میز یا داخل سالن. معمولاً با QR میز شروع می‌شود.</p>
          </div>
          <span class="order-flow-icon"><Utensils :size="24" /></span>
        </div>
        <button class="order-flow-primary" type="button" @click="choose('dine_in')">ادامه سفارش حضوری</button>
      </article>

      <article class="order-flow-card order-flow-card--selectable">
        <div class="order-flow-card-head">
          <div>
            <h2>بیرون‌بر</h2>
            <p>سفارش بدهید و خودتان از شعبه تحویل بگیرید. هزینه ارسال ندارد.</p>
          </div>
          <span class="order-flow-icon"><PackageCheck :size="24" /></span>
        </div>
        <button class="order-flow-primary" type="button" @click="choose('pickup')">انتخاب شعبه برای تحویل</button>
      </article>

      <article class="order-flow-card order-flow-card--selectable">
        <div class="order-flow-card-head">
          <div>
            <h2>ارسال</h2>
            <p>تحویل سفارش با پیک در آدرس شما، همراه با هزینه ارسال و ETA.</p>
          </div>
          <span class="order-flow-icon"><Bike :size="24" /></span>
        </div>
        <button class="order-flow-primary" type="button" @click="choose('delivery')">انتخاب آدرس</button>
      </article>
    </div>
  </section>
</template>

<script setup>
import { Bike, PackageCheck, Utensils } from 'lucide-vue-next'
import { resetOrderContextForType } from '@/utils/orderFlow'
import './orderFlow.css'

function choose(type) {
  resetOrderContextForType(type)
  window.location.href = `/order/${type === 'dine_in' ? 'dine-in' : type}`
}
</script>
