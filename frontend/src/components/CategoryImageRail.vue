<template>
  <div class="img-rail-stack">
    <div class="img-rail-wrap">
      <div class="img-rail" role="group" aria-label="دسته‌بندی‌های منو">
        <button
          v-for="category in categories"
          :key="category.slug"
          class="img-pill"
          type="button"
          :class="{ active: selectedCategory === category.slug }"
          :aria-pressed="selectedCategory === category.slug"
          @click="$emit('select-category', category.slug)"
        >
          <div class="img-copy">
            <span class="img-label">{{ category.title }}</span>
            <small v-if="category.item_count" class="img-count">{{ toFaCount(category.item_count) }} آیتم</small>
          </div>
          <div class="img-circle">
            <component :is="getCategoryIcon(category)" class="cat-icon" :size="19" stroke-width="1.9" />
          </div>
        </button>
      </div>
    </div>

    <transition name="slide-down">
      <div class="img-sub-wrap" v-if="subcategories.length">
        <div class="img-rail" role="group" :aria-label="`زیرگروه‌های ${activeCategoryTitle}`">
          <button
            class="sub-pill"
            type="button"
            :class="{ active: !selectedSubcategory }"
            :aria-pressed="!selectedSubcategory"
            @click="$emit('select-subcategory', '')"
          >
            همه {{ activeCategoryTitle }}
          </button>
          <button
            v-for="sub in subcategories"
            :key="sub.slug"
            class="sub-pill"
            type="button"
            :class="{ active: selectedSubcategory === sub.slug }"
            :aria-pressed="selectedSubcategory === sub.slug"
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

function toFaCount(value) {
  const count = Number(value || 0)
  return Number.isFinite(count) ? count.toLocaleString('fa-IR') : '۰'
}
</script>

<style scoped>
.img-rail-stack { max-width: 1140px; margin: auto; padding: .45rem 1rem; background: var(--ds-color-bg-page); }
.img-rail-wrap, .img-sub-wrap { padding: .25rem 0; }
.img-rail { display: flex; gap: .5rem; overflow-x: auto; scrollbar-width: none; scroll-snap-type: x proximity; padding: .25rem; }
.img-rail::-webkit-scrollbar { display: none; }
.img-pill { display: inline-flex; flex-direction: row-reverse; align-items: center; gap: .5rem; flex: 0 0 auto; min-height: 48px; padding: .5rem .85rem; border: 1px solid var(--ds-color-border); border-radius: var(--ds-radius-md); background: var(--ds-color-surface-raised); font: inherit; color: var(--ds-color-text-secondary); scroll-snap-align: start; cursor: pointer; }
.img-copy { display: flex; align-items: center; gap: .5rem; }
.img-label { font-size: .88rem; font-weight: 700; white-space: nowrap; }
.img-count { display: none; }
.img-circle { display: flex; align-items: center; }
.img-pill.active { background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); border-color: var(--ds-color-action-primary); }
.sub-pill { flex: 0 0 auto; min-height: 44px; border: 0; border-bottom: 2px solid transparent; background: transparent; color: var(--ds-color-text-muted); font: inherit; font-size: .82rem; padding: .5rem .8rem; white-space: nowrap; cursor: pointer; }
.sub-pill.active { color: var(--ds-color-action-primary); border-bottom-color: var(--ds-color-action-primary); font-weight: 800; }
.img-rail-stack button:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
</style>
