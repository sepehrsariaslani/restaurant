<template>
  <div class="rail-stack">
    <!-- دسته‌بندی‌های اصلی -->
    <div class="rail-wrap">
      <div class="rail">
        <button
          v-for="category in categories"
          :key="category.slug"
          class="pill"
          :class="{ active: selectedCategory === category.slug }"
          @click="$emit('select-category', category.slug)"
        >
          <strong>{{ category.title }}</strong>
          <small>{{ category.item_count || 0 }} آیتم</small>
        </button>
      </div>
    </div>

    <!-- زیردسته‌ها -->
    <transition name="slide-down">
      <div class="rail-wrap sub-rail-wrap" v-if="subcategories.length">
        <div class="rail">
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
</script>

<style scoped>
.rail-stack {
  gap: 0.55rem;
  margin-bottom: 0.8rem;
}

.sub-rail-wrap{
  border-radius: 0px 0px 20px 20px !important ;
}

.rail-wrap {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 20px 20px 0px 0px;
  padding: 0.55rem;
  width:100%;
  background: #fff;
  box-shadow: 0 8px 24px rgb(var(--palette-deep-sapphire-rgb) / 0.12);
}

.rail {
  display: flex;
  gap: 0.42rem;
  overflow-x: auto;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}
.rail::-webkit-scrollbar { display: none; }

/* ── دسته اصلی ── */
.pill {
  border: 1px solid rgb(var(--palette-deep-sapphire-rgb) / 0.2);
  border-radius: 14px;
  background: #fff;
  min-width: 100px;
  padding: 0.42rem 0.65rem;
  text-align: right;
  display: grid; gap: 0.12rem;
  flex-shrink: 0;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.18s ease;
}

.pill:hover { background: rgb(var(--palette-eggshell-rgb) / 0.9); transform: translateY(-1px); }

.pill strong { font-size: 0.83rem; color: var(--ink-900, #141210); }
.pill small  { color: var(--text-muted, #7a6e64); font-size: 0.69rem; }

.pill.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.5);
}
.pill.active strong { color: var(--accent-green); }

/* ── زیردسته ── */
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
  transition: background 0.2s ease, border-color 0.2s ease;
}

.sub-pill:hover { background: rgb(var(--palette-eggshell-rgb) / 0.88); }

.sub-pill.active {
  background: rgb(var(--palette-deep-sapphire-rgb) / 0.1);
  border-color: rgb(var(--palette-deep-sapphire-rgb) / 0.46);
  color: var(--accent-green);
  font-weight: 600;
}

/* انیمیشن ظاهر شدن زیردسته */
.slide-down-enter-active { animation: slideDown 0.28s ease; }
.slide-down-leave-active { animation: slideDown 0.2s ease reverse; }
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
