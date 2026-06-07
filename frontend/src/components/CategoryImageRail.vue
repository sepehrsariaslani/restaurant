<template>
  <div class="img-rail-stack">
    <div class="img-rail-wrap">
      <div class="img-rail">
        <button
          v-for="category in categories"
          :key="category.slug"
          class="img-pill"
          :class="{ active: selectedCategory === category.slug }"
          @click="$emit('select-category', category.slug)"
        >
          <div class="img-circle">
            <img
              v-if="category.image"
              :src="category.image"
              :alt="category.title"
              class="cat-img"
            />
            <span v-else class="cat-emoji">{{ getCategoryEmoji(category) }}</span>
          </div>
          <span class="img-label">{{ category.title }}</span>
        </button>
      </div>
    </div>

    <transition name="slide-down">
      <div class="img-sub-wrap" v-if="subcategories.length">
        <div class="img-rail">
          <button
            class="sub-pill"
            :class="{ active: !selectedSubcategory }"
            @click="$emit('select-subcategory', '')"
          >
            همه {{ activeCategoryTitle }}
          </button>
          <button
            v-for="sub in subcategories"
            :key="sub.slug"
            class="sub-pill"
            :class="{ active: selectedSubcategory === sub.slug }"
            @click="$emit('select-subcategory', sub.slug)"
          >
            {{ sub.title }}
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
defineProps({
  categories:          { type: Array,  default: () => [] },
  selectedCategory:    { type: String, default: '' },
  subcategories:       { type: Array,  default: () => [] },
  selectedSubcategory: { type: String, default: '' },
  activeCategoryTitle: { type: String, default: 'دسته' },
})
defineEmits(['select-category', 'select-subcategory'])

const EMOJI_MAP = {
  burger: '🍔', hamburger: '🍔', pizza: '🍕', chicken: '🍗', مرغ: '🍗',
  kebab: '🥙', کباب: '🥙', sandwich: '🥪', ساندویچ: '🥪', salad: '🥗',
  سالاد: '🥗', pasta: '🍝', پاستا: '🍝', soup: '🍜', سوپ: '🍜',
  drink: '🥤', نوشیدنی: '🥤', coffee: '☕', قهوه: '☕', tea: '🍵',
  dessert: '🍰', دسر: '🍰', ice: '🍦', بستنی: '🍦', cake: '🎂',
  sushi: '🍣', سوشی: '🍣', noodle: '🍜', rice: '🍚', برنج: '🍚',
  snack: '🍟', سنک: '🍟', fries: '🍟', fish: '🐟', ماهی: '🐟',
  sea: '🦐', میگو: '🦐', steak: '🥩', استیک: '🥩', wrap: '🌯',
  breakfast: '🥞', صبحانه: '🥞', waffle: '🧇',
}

function getCategoryEmoji(category) {
  const title = String(category.title || category.name || '').toLowerCase()
  for (const [key, emoji] of Object.entries(EMOJI_MAP)) {
    if (title.includes(key)) return emoji
  }
  return '🍽️'
}
</script>

<style scoped>
.img-rail-stack {
  margin-bottom: 0.8rem;
}

.img-rail-wrap {
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.15);
  border-radius: 20px 20px 0 0;
  padding: 0.8rem 0.6rem;
  box-shadow: 0 8px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.1);
}

.img-sub-wrap {
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.15);
  border-top: none;
  border-radius: 0 0 20px 20px;
  padding: 0.5rem 0.6rem;
}

.img-rail {
  display: flex;
  gap: 0.6rem;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.img-rail::-webkit-scrollbar { display: none; }

.img-pill {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
  cursor: pointer;
  background: none;
  border: none;
  padding: 0.3rem;
  border-radius: 14px;
  transition: transform 0.18s ease;
}
.img-pill:hover { transform: translateY(-2px); }

.img-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--theme-surface-alt, #f1e7db);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 2px solid transparent;
  transition: border-color 0.2s, background 0.2s;
  font-size: 1.6rem;
}

.img-pill.active .img-circle {
  background: var(--accent-green, #6f4a31);
  border-color: var(--accent-green, #6f4a31);
}

.cat-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.cat-emoji {
  font-size: 1.7rem;
  line-height: 1;
}

.img-pill.active .cat-emoji {
  filter: brightness(0) invert(1);
}

.img-label {
  font-size: 0.74rem;
  color: var(--text-primary, #3f2a1d);
  font-weight: 500;
  white-space: nowrap;
  max-width: 72px;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center;
}

.img-pill.active .img-label {
  color: var(--accent-green, #6f4a31);
  font-weight: 700;
}

.sub-pill {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 999px;
  background: #fff;
  padding: 0.3rem 0.72rem;
  white-space: nowrap;
  font-size: 0.77rem;
  color: var(--ink-600, #4a4038);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s, border-color 0.2s;
}
.sub-pill:hover { background: var(--theme-surface-alt, #f1e7db); }
.sub-pill.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.46);
  color: var(--accent-green);
  font-weight: 600;
}

.slide-down-enter-active { animation: slideDown 0.28s ease; }
.slide-down-leave-active { animation: slideDown 0.2s ease reverse; }
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
