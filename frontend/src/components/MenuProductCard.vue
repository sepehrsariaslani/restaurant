<template>
  <article
    class="product-card"
    :class="[`layout--${layout}`, { 'is-added': justAdded }]"
    role="article"
  >
    <!-- ════ LAYOUT: featured ════ -->
    <template v-if="layout === 'featured'">
      <a class="featured-cover" :href="`/item/${item.slug}`" :aria-label="`مشاهده ${item.title}`">
        <img :src="resolvedImage" :alt="item.title" class="featured-img" loading="lazy" />
        <span class="prep-badge" v-if="item.prep_time_mins">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          {{ item.prep_time_mins }} دقیقه
        </span>
      </a>
      <div class="featured-body">
        <h3>{{ item.title }}</h3>
        <p class="desc muted">{{ item.short_desc || 'توضیحی برای این آیتم ثبت نشده است.' }}</p>
        <p class="nutrition-line" v-if="nutritionText">{{ nutritionText }}</p>
        <div class="featured-foot">
          <div>
            <small class="muted">قیمت</small>
            <strong class="price">{{ formatMoney(item.base_price, currency) }}</strong>
            <small class="in-cart-badge" v-if="cartQty > 0">در سبد: {{ cartQty }}</small>
          </div>
          <div class="foot-actions">
            <button class="like-btn" type="button" :aria-label="`علاقه‌مندی`" @click.prevent="toggleLike">
              <svg width="17" height="17" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            </button>
            <div class="qty-pill" v-if="cartQty > 0 && !hasCustomization">
              <button type="button" class="qty-step" @click.prevent="$emit('quick-decrease', item)">−</button>
              <strong>{{ cartQty }}</strong>
              <button type="button" class="qty-step" @click.prevent="$emit('quick-increase', item)">+</button>
            </div>
            <button v-else class="add-btn add-btn--pill" type="button" :class="{ added: justAdded }" :aria-label="`افزودن به سبد`" @click.prevent="handleAdd">
              <span>{{ justAdded ? 'افزوده شد' : 'افزودن به سبد' }}</span>
              <span class="add-circle">{{ justAdded ? '✓' : '+' }}</span>
            </button>
          </div>
        </div>
      </div>
    </template>

    <!-- ════ LAYOUT: list ════ -->
    <template v-else-if="layout === 'list'">
      <a class="list-cover" :href="`/item/${item.slug}`" :aria-label="`مشاهده ${item.title}`">
        <img :src="resolvedImage" :alt="item.title" class="list-img" loading="lazy" />
      </a>
      <div class="list-body">
        <div class="list-labels">
          <span class="mini-pill" v-if="item.category_title">{{ item.category_title }}</span>
          <span class="mini-pill sub" v-if="item.subcategory_title">{{ item.subcategory_title }}</span>
        </div>
        <h3>{{ item.title }}</h3>
        <p class="desc muted">{{ item.short_desc || '' }}</p>
        <p class="nutrition-line" v-if="nutritionText">{{ nutritionText }}</p>
        <div class="list-foot">
          <div>
            <strong class="price">{{ formatMoney(item.base_price, currency) }}</strong>
            <small class="in-cart-badge" v-if="cartQty > 0">در سبد: {{ cartQty }}</small>
          </div>
          <div class="qty-pill compact" v-if="cartQty > 0 && !hasCustomization">
            <button type="button" class="qty-step" @click.prevent="$emit('quick-decrease', item)">−</button>
            <strong>{{ cartQty }}</strong>
            <button type="button" class="qty-step" @click.prevent="$emit('quick-increase', item)">+</button>
          </div>
          <button v-else class="add-btn" type="button" :class="{ added: justAdded }" :aria-label="`افزودن ${item.title} به سبد`" @click.prevent="handleAdd">
            <span class="add-icon">{{ justAdded ? '✓' : '+' }}</span>
          </button>
        </div>
      </div>
    </template>

    <!-- ════ LAYOUT: grid ════ -->
    <template v-else>
      <a class="grid-cover" :href="`/item/${item.slug}`" :aria-label="`مشاهده ${item.title}`">
        <img :src="resolvedImage" :alt="item.title" class="grid-img" loading="lazy" />
        <span class="category-badge" v-if="item.subcategory_title || item.category_title">
          {{ item.subcategory_title || item.category_title }}
        </span>
      </a>
      <div class="grid-body">
        <h3>{{ item.title }}</h3>
        <p class="desc muted">{{ item.short_desc || 'توضیحی ثبت نشده.' }}</p>
        <p class="nutrition-line" v-if="nutritionText">{{ nutritionText }}</p>
        <div class="grid-foot">
          <div>
            <strong class="price">{{ formatMoney(item.base_price, currency) }}</strong>
            <small class="in-cart-badge" v-if="cartQty > 0">در سبد: {{ cartQty }}</small>
          </div>
          <div class="foot-actions">
            <a :href="`/item/${item.slug}`" class="detail-link">جزئیات</a>
            <div class="qty-pill compact" v-if="cartQty > 0 && !hasCustomization">
              <button type="button" class="qty-step" @click.prevent="$emit('quick-decrease', item)">−</button>
              <strong>{{ cartQty }}</strong>
              <button type="button" class="qty-step" @click.prevent="$emit('quick-increase', item)">+</button>
            </div>
            <button v-else class="add-btn" type="button" :class="{ added: justAdded }" :aria-label="`افزودن ${item.title} به سبد`" @click.prevent="handleAdd">
              <span class="add-icon">{{ justAdded ? '✓' : '+' }}</span>
            </button>
          </div>
        </div>
      </div>
    </template>
  </article>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  item: { type: Object, required: true },
  currency: { type: String, default: 'TOMAN' },
  cartQty: { type: Number, default: 0 },
  layout: {
    type: String,
    default: 'list',
    validator: (v) => ['featured', 'list', 'grid'].includes(v),
  },
})

const emit = defineEmits(['quick-add', 'quick-increase', 'quick-decrease'])
const justAdded = ref(false)
const liked = ref(false)
let addTimer = null

function handleAdd() {
  emit('quick-add', props.item)
  justAdded.value = true
  clearTimeout(addTimer)
  addTimer = setTimeout(() => { justAdded.value = false }, 1800)
}

function toggleLike() { liked.value = !liked.value }

const resolvedImage = computed(
  () => props.item.image || 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=900&auto=format&fit=crop&q=60',
)

const nutritionText = computed(() => {
  const kcal = Number(props.item?.nutrition?.kcal ?? props.item?.nutrition_kcal ?? 0)
  const protein = Number(props.item?.nutrition?.protein_g ?? props.item?.nutrition_protein_g ?? 0)
  const carb = Number(props.item?.nutrition?.carb_g ?? props.item?.nutrition_carb_g ?? 0)
  const sugar = Number(props.item?.nutrition?.sugar_g ?? props.item?.nutrition_sugar_g ?? 0)
  const parts = []
  if (Number.isFinite(kcal) && kcal > 0) parts.push(`${Math.round(kcal)} kcal`)
  if (Number.isFinite(protein) && protein > 0) parts.push(`P ${Math.round(protein)}g`)
  if (Number.isFinite(carb) && carb > 0) parts.push(`C ${Math.round(carb)}g`)
  if (Number.isFinite(sugar) && sugar > 0) parts.push(`S ${Math.round(sugar)}g`)
  return parts.join(' • ')
})

const hasCustomization = computed(() => Number(props.item?.has_customization || 0) === 1)
</script>

<style scoped>
/* ─── مشترک ─────────────────────────────────── */
.product-card { position: relative; overflow: hidden; }

.product-card.is-added {
  outline: 2px solid rgba(255, 255, 255, 0.45);
  outline-offset: 2px;
}

.price { font-size: 1.05rem; font-weight: 700; color: var(--ink-900, #141210); }
.desc  { margin: 0; font-size: 0.79rem; line-height: 1.55; }
.muted { color: var(--text-muted, #7a6e64); }
.foot-actions { display: flex; align-items: center; gap: 0.42rem; }
.nutrition-line { margin: 0.2rem 0 0; font-size: 0.72rem; color: var(--text-muted, #7a6e64); }
.in-cart-badge { display: block; margin-top: 0.12rem; font-size: 0.68rem; color: var(--accent-green, #2f6f5c); }

.mini-pill {
  border-radius: 999px;
  background: rgb(var(--palette-deep-saffron-rgb) / 0.16);
  padding: 0.16rem 0.48rem;
  font-size: 0.67rem;
  color: var(--ink-600, #4a4038);
}
.mini-pill.sub { background: rgb(var(--palette-june-bud-rgb) / 0.34); color: var(--ink-800); }

/* دکمه لایک */
.like-btn {
  width: 38px; height: 38px;
  border-radius: 50%;
  border: 1.5px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
  background: rgb(var(--palette-eggshell-rgb) / 0.74);
  color: var(--accent-gold);
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.18s ease;
  flex-shrink: 0;
}
.like-btn:hover { background: rgb(var(--palette-deep-saffron-rgb) / 0.14); transform: scale(1.1); }

/* دکمه افزودن (مربعی) */
.add-btn {
  width: 36px; height: 36px;
  border-radius: 12px; border: 0;
  background: var(--ink-800, #1e1a17);
  color: #fff;
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(20, 15, 8, 0.3);
  transition: background 0.28s ease, transform 0.18s ease;
  flex-shrink: 0;
}
.add-btn:hover  { transform: scale(1.1); }
.add-btn:active { transform: scale(0.93); }
.add-btn.added  { background: var(--accent-green); }

.add-icon {
  font-size: 1.3rem; line-height: 1;
  transition: transform 0.22s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.add-btn.added .add-icon { transform: scale(1.25); }

/* دکمه pill (featured) */
.add-btn--pill {
  width: auto; border-radius: 999px;
  padding: 0 0.65rem 0 1rem; gap: 0.5rem;
  font-size: 0.84rem; font-family: inherit; height: 42px;
}
.add-circle {
  width: 26px; height: 26px; border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 1.1rem;
}

/* detail link */
.detail-link {
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.34);
  padding: 0.3rem 0.72rem;
  font-size: 0.76rem; color: var(--ink-600, #4a4038);
  text-decoration: none;
  background: rgb(var(--palette-eggshell-rgb) / 0.72);
  transition: background 0.18s ease;
}
.detail-link:hover { background: rgb(var(--palette-eggshell-rgb) / 0.92); }

.qty-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.3);
  background: rgb(var(--palette-eggshell-rgb) / 0.78);
  padding: 0.2rem 0.35rem;
  min-height: 36px;
}

.qty-pill.compact {
  min-height: 34px;
}

.qty-step {
  width: 26px;
  height: 26px;
  border-radius: 999px;
  border: 1px solid rgb(var(--palette-deep-saffron-rgb) / 0.38);
  background: #fff;
  color: var(--ink-800, #1e1a17);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}

/* ─── LAYOUT: featured ───────────────────────── */
.layout--featured {
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 42px;
  box-shadow: 0 20px 44px rgb(15 23 42 / 0.1);
  display: flex; flex-direction: column;
}

.featured-cover {
  display: block;
  height: 280px;
  border-radius: 42px 42px 0 0;
  overflow: hidden;
  position: relative;
  text-decoration: none;
}

.featured-img {
  width: 100%; height: 100%;
  object-fit: contain;
  object-position: center;
  background: transparent;
  transition: transform 0.38s ease;
  transform-origin: center 45%;
}
.layout--featured:hover .featured-img { transform: scale(1.05); }

.prep-badge {
  position: absolute; top: 0.75rem; left: 0.75rem;
  border-radius: 999px;
  background: #fff;
  padding: 0.28rem 0.72rem;
  font-size: 0.72rem; font-weight: 600; color: var(--ink-700, #2e2820);
  display: flex; align-items: center; gap: 0.3rem;
}

.featured-body {
  padding: 1.1rem 1.2rem 1.3rem;
  display: flex; flex-direction: column; gap: 0.42rem;
}
.featured-body h3 {
  margin: 0; font-size: 1.5rem; font-weight: 700; line-height: 1.2;
  color: var(--ink-900, #141210);
}
.featured-foot {
  margin-top: 0.4rem;
  display: flex; align-items: flex-end; justify-content: space-between; gap: 0.6rem;
}
.featured-foot .price { font-size: 1.35rem; }
.featured-foot small { display: block; font-size: 0.7rem; color: var(--text-muted); margin-bottom: 0.1rem; }

/* ─── LAYOUT: list ───────────────────────────── */
.layout--list {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 24px;
  box-shadow: 0 14px 36px #19282229;
  display: grid; grid-template-columns: 120px 1fr;
  gap: 0.75rem; padding: 0.75rem;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.layout--list:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 40px rgb(var(--palette-deep-sapphire-rgb) / 0.16);
}

.list-cover { display: block; width: 90px; height: 100%; border-radius: 18px; overflow: hidden; }

.list-img {
  width: 95% ;
  height:95% ;
  object-fit: contain ; 
  object-position: center;
  background: transparent;
  border-radius: 18px ;
  transition: transform 0.28s ease ;
}

.layout--list:hover .list-img { transform: scale(1.02); }

.list-body { display: flex; flex-direction: column; gap: 0.22rem; min-width: 0; }
.list-labels { display: flex; gap: 0.28rem; flex-wrap: wrap; }
.list-body h3 { margin: 0; font-size: 0.97rem; font-weight: 700; color: var(--ink-900); }
.list-body .desc { min-height: 1.8rem; }
.list-foot {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: auto; padding-top: 0.2rem;
}

/* ─── LAYOUT: grid ───────────────────────────── */
.layout--grid {
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.18);
  border-radius: 32px;
  box-shadow: 0 24px 56px rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  display: flex; flex-direction: column;
  transition: transform 0.24s ease, box-shadow 0.24s ease;
}
.layout--grid:hover {
  transform: translateY(-4px);
  box-shadow: 0 32px 72px rgb(var(--palette-deep-sapphire-rgb) / 0.22);
}

.grid-cover {
  position: relative; height: 190px;
  border-radius: 32px 32px 0 0; overflow: hidden;
  display: block; text-decoration: none;
}
.grid-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center;
  background: transparent;
  transition: transform 0.34s ease;
}
.layout--grid:hover .grid-img { transform: scale(1.05); }

.category-badge {
  position: absolute; top: 0.6rem; right: 0.6rem;
  border-radius: 999px; padding: 0.18rem 0.55rem;
  background: #fff;
  font-size: 0.68rem; font-weight: 600; color: var(--ink-700, #2e2820);
}

.grid-body {
  padding: 0.9rem; display: flex; flex-direction: column;
  gap: 0.28rem; flex: 1;
}
.grid-body h3 { margin: 0; font-size: 1.05rem; font-weight: 700; color: var(--ink-900); }
.grid-body .desc { flex: 1; min-height: 2.4rem; }
.grid-foot {
  display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem;
}
</style>
