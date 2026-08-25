<template>
  <section class="foodbar-hero" dir="rtl">
    <div class="fb-left">
      <div class="fb-side-labels" aria-hidden="true">
        <span>process</span>
        <span>design</span>
        <span>material</span>
      </div>
      <div class="fb-dish-frame">
        <Transition name="dish" mode="out-in">
          <img
            :key="activeItem.slug"
            :src="activeItem.image || fallback"
            :alt="activeItem.title"
            class="fb-dish-img"
          />
        </Transition>
        <div class="fb-dish-glow"></div>
      </div>
    </div>

    <div class="fb-right">
      <Transition name="info" mode="out-in">
        <div :key="activeItem.slug" class="fb-info">
          <p class="fb-eyebrow">{{ activeItem.category_title || 'پرفروش‌ترین' }}</p>
          <h1 class="fb-product-name">{{ activeItem.title }}</h1>
          <p class="fb-product-desc">{{ activeItem.short_desc || 'یکی از محبوب‌ترین انتخاب‌های مشتریان ما' }}</p>
          <div class="fb-price-row">
            <span class="fb-price-label">از</span>
            <strong class="fb-price">{{ formatMoney(activeItem.base_price, currency) }}</strong>
          </div>
          <div class="fb-actions">
            <a :href="`/item/${activeItem.slug}`" class="fb-order-btn">سفارش الان ←</a>
            <a href="/menu" class="fb-menu-btn">مشاهده منو</a>
          </div>
          <div class="fb-rating-row">
            <span class="fb-stars">★★★★★</span>
            <span class="fb-rating-text">{{ activeItem.rating || '5.0' }} از ۵</span>
          </div>
        </div>
      </Transition>
    </div>

    <div class="fb-thumbs-area">
      <button
        v-for="(item, idx) in visibleItems"
        :key="item.slug"
        class="fb-thumb"
        :class="{ 'fb-thumb--active': activeIndex === idx }"
        type="button"
        @click="setActive(idx)"
      >
        <div class="fb-thumb-img-wrap">
          <img :src="item.image || fallback" :alt="item.title" class="fb-thumb-img" />
          <span class="fb-thumb-price">{{ formatMoney(item.base_price, currency) }}</span>
        </div>
        <div class="fb-thumb-body">
          <strong class="fb-thumb-name">{{ item.title }}</strong>
          <small class="fb-thumb-cat">{{ item.category_title || 'منو' }}</small>
        </div>
        <div class="fb-thumb-footer">
          <span class="fb-thumb-rating">★ {{ item.rating || '5.0' }}</span>
          <button
            class="fb-thumb-add"
            type="button"
            @click.stop="$emit('quick-add', item)"
            aria-label="افزودن به سبد"
          >→</button>
        </div>
      </button>
    </div>

    <div class="fb-dots" aria-hidden="true">
      <button
        v-for="(_, idx) in visibleItems"
        :key="idx"
        class="fb-dot"
        :class="{ 'fb-dot--active': activeIndex === idx }"
        type="button"
        @click="setActive(idx)"
      ></button>
    </div>

    <div class="fb-social" aria-label="شبکه‌های اجتماعی">
      <a href="#" class="fb-social-link" aria-label="Instagram">ig</a>
      <a href="#" class="fb-social-link" aria-label="Telegram">tg</a>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
})

defineEmits(['quick-add'])

const fallback = 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600&auto=format&fit=crop&q=60'

const activeIndex = ref(0)

const visibleItems = computed(() => {
  const items = Array.isArray(props.items) ? props.items : []
  return items.slice(0, 5)
})

const activeItem = computed(() => {
  const items = visibleItems.value
  if (!items.length) {
    return {
      slug: 'placeholder',
      title: 'محصول پرفروش',
      short_desc: 'یکی از محبوب‌ترین انتخاب‌های مشتریان ما',
      base_price: 0,
      image: '',
      category_title: 'ویژه',
      rating: '5.0',
    }
  }
  return items[Math.min(activeIndex.value, items.length - 1)]
})

function setActive(idx) {
  activeIndex.value = idx
  resetTimer()
}

let timer = null
function startTimer() {
  if (visibleItems.value.length <= 1) return
  timer = setInterval(() => {
    activeIndex.value = (activeIndex.value + 1) % visibleItems.value.length
  }, 4500)
}

function resetTimer() {
  clearInterval(timer)
  startTimer()
}

onMounted(startTimer)
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.foodbar-hero {
  position: relative;
  min-height: 100svh;
  background: #fff;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr auto auto;
  overflow: hidden;
}

.fb-left {
  grid-column: 1;
  grid-row: 1;
  background: #1c1411;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 3rem 2rem;
}

.fb-side-labels {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.fb-side-labels span {
  writing-mode: vertical-rl;
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.35);
  font-weight: 500;
}

.fb-dish-frame {
  position: relative;
  width: min(420px, 80%);
  aspect-ratio: 1;
}

.fb-dish-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  filter: drop-shadow(0 24px 60px rgba(0, 0, 0, 0.6));
}

.fb-dish-glow {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  height: 40px;
  background: radial-gradient(ellipse, rgba(201, 141, 66, 0.35) 0%, transparent 70%);
  filter: blur(12px);
}

.fb-right {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  align-items: center;
  padding: 3rem 3rem 3rem 2rem;
  background: #fff;
}

.fb-info {
  max-width: 420px;
}

.fb-eyebrow {
  margin: 0 0 0.5rem;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--accent-green, #6f4a31);
  font-weight: 700;
}

.fb-product-name {
  margin: 0 0 0.75rem;
  font-size: clamp(2rem, 4vw, 3.2rem);
  font-weight: 900;
  color: #111;
  line-height: 1.1;
}

.fb-product-desc {
  margin: 0 0 1.25rem;
  font-size: 0.9rem;
  color: #777;
  line-height: 1.7;
}

.fb-price-row {
  display: flex;
  align-items: baseline;
  gap: 0.4rem;
  margin-bottom: 1.5rem;
}

.fb-price-label {
  font-size: 0.8rem;
  color: #999;
}

.fb-price {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--accent-green, #6f4a31);
}

.fb-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.fb-order-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: #1c1411;
  color: #fff;
  border-radius: 12px;
  padding: 0.85rem 1.6rem;
  font-size: 0.95rem;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.2s;
}

.fb-order-btn:hover {
  background: var(--accent-green, #6f4a31);
}

.fb-menu-btn {
  color: #555;
  font-size: 0.9rem;
  text-decoration: none;
  border-bottom: 1px solid #ccc;
  padding-bottom: 1px;
}

.fb-rating-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.fb-stars {
  color: #f5c518;
  font-size: 1rem;
  letter-spacing: -2px;
}

.fb-rating-text {
  font-size: 0.8rem;
  color: #999;
}

.fb-thumbs-area {
  grid-column: 1 / -1;
  grid-row: 2;
  display: flex;
  gap: 0;
  background: #1c1411;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  overflow-x: auto;
  scrollbar-width: none;
}

.fb-thumbs-area::-webkit-scrollbar {
  display: none;
}

.fb-thumb {
  flex: 1;
  min-width: 160px;
  border: none;
  background: transparent;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1rem 1rem 0.75rem;
  cursor: pointer;
  text-align: right;
  transition: background 0.2s;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  position: relative;
}

.fb-thumb:last-child {
  border-right: none;
}

.fb-thumb:hover,
.fb-thumb--active {
  background: rgba(255, 255, 255, 0.06);
}

.fb-thumb--active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-gold, #c98d42);
}

.fb-thumb-img-wrap {
  position: relative;
  height: 80px;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.06);
}

.fb-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.fb-thumb-price {
  position: absolute;
  top: 6px;
  left: 6px;
  background: var(--accent-green, #6f4a31);
  color: #fff;
  border-radius: 999px;
  padding: 0.1rem 0.45rem;
  font-size: 0.68rem;
  font-weight: 700;
}

.fb-thumb-body {
  text-align: right;
}

.fb-thumb-name {
  display: block;
  font-size: 0.8rem;
  color: #fff;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fb-thumb-cat {
  display: block;
  font-size: 0.68rem;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 0.1rem;
}

.fb-thumb-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.fb-thumb-rating {
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.55);
}

.fb-thumb-add {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s, border-color 0.2s;
}

.fb-thumb-add:hover {
  background: var(--accent-gold, #c98d42);
  border-color: var(--accent-gold, #c98d42);
  color: #fff;
}

.fb-dots {
  grid-column: 1 / -1;
  grid-row: 3;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  padding: 0.75rem 1rem;
  background: #1c1411;
}

.fb-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.25);
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}

.fb-dot--active {
  background: var(--accent-gold, #c98d42);
  transform: scale(1.3);
}

.fb-social {
  position: absolute;
  left: 1.5rem;
  bottom: 7rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  z-index: 2;
}

.fb-social-link {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: rgba(255, 255, 255, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  transition: border-color 0.2s, color 0.2s;
}

.fb-social-link:hover {
  border-color: var(--accent-gold, #c98d42);
  color: var(--accent-gold, #c98d42);
}

.dish-enter-active,
.dish-leave-active {
  transition: opacity 0.4s, transform 0.4s;
}

.dish-enter-from {
  opacity: 0;
  transform: scale(0.9) rotate(-4deg);
}

.dish-leave-to {
  opacity: 0;
  transform: scale(1.05) rotate(2deg);
}

.info-enter-active,
.info-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.info-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.info-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

@media (max-width: 768px) {
  .foodbar-hero {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto auto;
    min-height: auto;
  }

  .fb-left {
    grid-column: 1;
    grid-row: 1;
    padding: 2rem 1.5rem 1rem;
    min-height: 320px;
  }

  .fb-right {
    grid-column: 1;
    grid-row: 2;
    padding: 1.5rem;
    background: #fff;
  }

  .fb-side-labels {
    display: none;
  }

  .fb-thumbs-area {
    grid-column: 1;
    grid-row: 3;
  }

  .fb-dots {
    grid-column: 1;
    grid-row: 4;
  }

  .fb-social {
    display: none;
  }

  .fb-dish-frame {
    width: min(280px, 80%);
  }
}
</style>
