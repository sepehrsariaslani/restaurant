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
          <div class="img-copy">
            <span class="img-label">{{ category.title }}</span>
            <small v-if="category.item_count" class="img-count">{{ category.item_count }} آیتم</small>
          </div>
          <div class="img-circle" :class="{ 'has-image': category.image }">
            <img
              v-if="category.image"
              :src="category.image"
              :alt="category.title"
              class="cat-img"
            />
            <component v-else :is="getCategoryIcon(category)" class="cat-icon" :size="19" stroke-width="1.9" />
          </div>
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
import { Beef, CakeSlice, Coffee, CupSoda, Drumstick, Fish, GlassWater, Pizza, Salad, Sandwich, Soup, Utensils, Wheat } from 'lucide-vue-next'
import { getMenuIconComponent } from '@/utils/menuIcons'

defineProps({
  categories:          { type: Array,  default: () => [] },
  selectedCategory:    { type: String, default: '' },
  subcategories:       { type: Array,  default: () => [] },
  selectedSubcategory: { type: String, default: '' },
  activeCategoryTitle: { type: String, default: 'دسته' },
})
defineEmits(['select-category', 'select-subcategory'])

const ICON_RULES = [
  { keys: ['نوشیدنی', 'drink', 'سردنوش', 'آبمیوه'], icon: CupSoda },
  { keys: ['قهوه', 'coffee', 'کافه', 'بار'], icon: Coffee },
  { keys: ['چای', 'دمنوش', 'tea'], icon: GlassWater },
  { keys: ['ساندویچ', 'sandwich'], icon: Sandwich },
  { keys: ['کیک', 'دسر', 'شیرینی', 'dessert', 'cake', 'میان وعده'], icon: CakeSlice },
  { keys: ['سالاد', 'salad', 'پیش غذا', 'پیشغذا'], icon: Salad },
  { keys: ['سوپ', 'آش', 'soup'], icon: Soup },
  { keys: ['پیتزا', 'pizza'], icon: Pizza },
  { keys: ['مرغ', 'chicken', 'ناگت'], icon: Drumstick },
  { keys: ['گوشت', 'استیک', 'کباب', 'beef', 'steak', 'kebab'], icon: Beef },
  { keys: ['ماهی', 'میگو', 'fish', 'sea'], icon: Fish },
  { keys: ['نان', 'غلات', 'bread', 'wheat'], icon: Wheat },
]

function getCategoryIcon(category) {
  // Prefer stored icon from management
  const stored = getMenuIconComponent(category.menu_icon || '', null)
  if (stored) return stored

  // Fallback: infer from title
  const title = String(category.title || category.name || '').toLowerCase()
  const matched = ICON_RULES.find((row) => row.keys.some((key) => title.includes(String(key).toLowerCase())))
  return matched?.icon || Utensils
}
</script>

<style scoped>
.img-rail-stack {
  margin-bottom: 0;
}

.img-rail-wrap {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  border-radius: 0 0 15px 15px;
  padding: 0.28rem 0.34rem 0.32rem;
  box-shadow: 0 6px 16px rgb(var(--palette-deep-sapphire-rgb) / 0.06);
}

.img-sub-wrap {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  border-top: none;
  border-radius: 0 0 15px 15px;
  padding: 0.24rem 0.34rem 0.34rem;
}

.img-rail {
  display: flex;
  gap: 0.3rem;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  scroll-snap-type: x mandatory;
  padding: 0.02rem 0.02rem 0.08rem;
}
.img-rail::-webkit-scrollbar { display: none; }

.img-pill {
  display: grid;
  grid-template-columns: minmax(56px, 1fr) 34px;
  align-items: center;
  gap: 0.28rem;
  flex-shrink: 0;
  cursor: pointer;
  background: #fff;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.10);
  padding: 0.34rem 0.4rem;
  border-radius: 13px;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
  scroll-snap-align: start;
  min-width: 112px;
  min-height: 54px;
  box-shadow: 0 5px 12px rgba(16, 24, 40, 0.03);
  font-family: inherit;
  text-align: right;
}
.img-pill:hover { transform: translateY(-2px); }
.img-pill.active {
  background: linear-gradient(180deg, var(--accent-green), var(--accent-green80));
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.7);
  box-shadow: 0 12px 26px rgb(var(--palette-deep-sapphire-rgb) / 0.20);
}

.img-circle {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: var(--accent-green20, var(--theme-surface-alt));
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.08);
  transition: border-color 0.2s, background 0.2s, transform 0.2s;
  font-size: 1rem;
}

.img-circle.has-image {
  background: transparent;
  border-color: transparent;
}

.img-pill.active .img-circle {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.28);
  transform: scale(1.03);
}

.img-pill.active .img-circle.has-image {
  background: rgba(255, 255, 255, 0.12);
}

.cat-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 11px;
}

.cat-icon {
  color: var(--accent-green);
}

.img-pill.active .cat-icon {
  color: #fff;
}

.img-copy {
  display: grid;
  gap: 0.16rem;
  min-width: 0;
}

.img-label {
  font-size: 0.68rem;
  color: var(--text-primary);
  font-weight: 900;
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
  line-height: 1.35;
}

.img-count {
  font-size: 0.55rem;
  color: var(--text-muted);
  line-height: 1;
  white-space: nowrap;
  text-align: right;
}

.img-pill.active .img-label,
.img-pill.active .img-count {
  color: #fff;
}

.sub-pill {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.14);
  border-radius: 999px;
  background: #fff;
  padding: 0.22rem 0.52rem;
  white-space: nowrap;
  font-size: 0.64rem;
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s, border-color 0.2s, color 0.2s;
  font-family: inherit;
}
.sub-pill:hover { background: var(--accent-green20, var(--theme-surface-alt)); }
.sub-pill.active {
  background: var(--accent-green);
  border-color: var(--accent-green);
  color: #fff;
  font-weight: 800;
}

.slide-down-enter-active { animation: slideDown 0.28s ease; }
.slide-down-leave-active { animation: slideDown 0.2s ease reverse; }
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
