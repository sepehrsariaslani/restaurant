<template>
  <article class="item-card glass-card stagger-item" :style="cardStyle">
    <a class="cover-wrap" :href="`/item/${item.slug}`">
      <img :src="resolvedImage" :alt="item.title" class="cover" />
    </a>

    <div class="content">
      <div class="labels">
        <span class="mini-pill">{{ item.category_title || 'منو' }}</span>
        <span class="mini-pill sub" v-if="item.subcategory_title">{{ item.subcategory_title }}</span>
      </div>

      <h3>{{ item.title }}</h3>
      <p class="muted">{{ item.short_desc || 'شرح این آیتم در حال تکمیل است.' }}</p>

      <div class="foot">
        <strong>{{ formatMoney(item.base_price, currency) }}</strong>
        <button class="add-btn" @click="$emit('quick-add', item)">
          <span>+</span>
        </button>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
  delay: {
    type: Number,
    default: 0,
  },
})

defineEmits(['quick-add'])

const resolvedImage = computed(
  () => props.item.image || 'https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?w=900&auto=format&fit=crop&q=60',
)

const cardStyle = computed(() => ({
  animationDelay: `${props.delay}ms`,
}))
</script>

<style scoped>
.item-card {
  padding: 0.8rem;
  display: grid;
  grid-template-columns: 92px 1fr;
  gap: 0.75rem;
  border-radius: 20px;
}

.cover-wrap {
  display: block;
}

.cover {
  width: 92px;
  height: 92px;
  border-radius: 22px;
  object-fit: contain;
  object-position: center;
  background: transparent;
  box-shadow: 0 10px 18px rgba(29, 33, 26, 0.18);
}

.content {
  display: grid;
  gap: 0.36rem;
}

.labels {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.mini-pill {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.58);
  padding: 0.18rem 0.5rem;
  font-size: 0.68rem;
  color: var(--ink-700);
}

.mini-pill.sub {
  background: rgba(79, 126, 84, 0.16);
}

h3 {
  margin: 0;
  font-size: 1rem;
}

p {
  margin: 0;
  font-size: 0.79rem;
  line-height: 1.45;
  min-height: 2.2rem;
}

.foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.08rem;
}

.foot strong {
  font-size: 0.96rem;
}

.add-btn {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  border: 0;
  background: var(--accent-green80);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 20px rgba(26, 34, 24, 0.25);
}

.add-btn span {
  font-size: 1.35rem;
  line-height: 1;
}
</style>
