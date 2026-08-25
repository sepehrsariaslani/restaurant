<template>
  <div class="nvs" ref="rootRef">
    <!-- دکمه باز کردن تنظیمات نما -->
    <button type="button" class="nvs-trigger" :class="{ active: open, has: hasActive }" @click="open = !open">
      <Settings :size="14" :stroke-width="2.2" />
      <span>تنظیمات نما</span>
      <ChevronDown :size="13" :class="['nvs-chev', { open }]" />
    </button>

    <!-- پنل کامل تنظیمات -->
    <div v-if="open" class="nvs-panel">
      <div class="nvs-head">
        <div class="nvs-head-title">
          <strong>تنظیمات نما</strong>
          <span class="nvs-view-name">{{ view?.name }}</span>
        </div>
        <button type="button" class="nvs-close" title="بستن" @click="open = false"><X :size="15" /></button>
      </div>

      <!-- ۱) چیدمان -->
      <div class="nvs-section">
        <div class="nvs-section-title"><LayoutList :size="13" /> چیدمان</div>
        <div class="nvs-layouts">
          <button
            v-for="l in layouts"
            :key="l.value"
            type="button"
            class="nvs-layout"
            :class="{ active: view?.layout === l.value }"
            @click="update({ layout: l.value })"
          >
            <component :is="l.icon" :size="15" :stroke-width="1.8" />
            <span>{{ l.label }}</span>
          </button>
        </div>
      </div>

      <!-- ۲) فیلترها -->
      <div class="nvs-section">
        <div class="nvs-section-title"><Filter :size="13" /> فیلترها <span v-if="view?.filters?.length" class="nvs-count">{{ view.filters.length }}</span></div>
        <div v-for="(f, i) in view?.filters || []" :key="i" class="nvs-row">
          <select v-if="i > 0" v-model="f.joiner" class="nvs-select nvs-joiner">
            <option value="and">AND</option>
            <option value="or">OR</option>
          </select>
          <select v-model="f.property" class="nvs-select" @change="resetOperator(f)">
            <option v-for="p in properties" :key="p.key" :value="p.key">{{ p.label }}</option>
          </select>
          <select v-model="f.operator" class="nvs-select">
            <option v-for="op in operatorsFor(f.property)" :key="op[0]" :value="op[0]">{{ op[1] }}</option>
          </select>
          <div
            v-if="propertyType(f.property) === 'select' && needsValue(f.property, f.operator)"
            class="nvs-dropdown-wrap"
          >
            <SearchableDropdown
              v-model="f.value"
              :options="optionsFor(f.property)"
              placeholder="انتخاب..."
              search-placeholder="جستجو..."
              clearable
              include-empty-option
              empty-label="همه"
            />
          </div>
          <div
            v-else-if="propertyType(f.property) === 'tags' && needsValue(f.property, f.operator)"
            class="nvs-dropdown-wrap"
          >
            <SearchableDropdown
              v-model="f.value"
              :options="optionsFor(f.property)"
              placeholder="انتخاب تگ..."
              search-placeholder="جستجوی تگ..."
              clearable
              include-empty-option
              empty-label="همه"
            />
          </div>
          <div v-else-if="propertyType(f.property) === 'boolean' && needsValue(f.property, f.operator)" class="nvs-bool">
            <button type="button" :class="['nvs-bool-btn', { active: f.value === 'بله' }]" @click="f.value = 'بله'">بله</button>
            <button type="button" :class="['nvs-bool-btn', { active: f.value === 'خیر' }]" @click="f.value = 'خیر'">خیر</button>
          </div>
          <input
            v-else-if="needsValue(f.property, f.operator)"
            v-model="f.value"
            class="nvs-input"
            :type="valueType(f.property)"
            placeholder="..."
          />
          <button type="button" class="nvs-x" @click="removeFilter(i)"><X :size="13" /></button>
        </div>
        <div v-if="!view?.filters?.length" class="nvs-empty">هیچ فیلتری فعال نیست.</div>
        <button type="button" class="nvs-add" @click="addFilter"><Plus :size="13" /> افزودن فیلتر</button>
      </div>

      <!-- ۳) مرتب‌سازی‌ها -->
      <div class="nvs-section">
        <div class="nvs-section-title"><ArrowUpDown :size="13" /> مرتب‌سازی <span v-if="view?.sorts?.length" class="nvs-count">{{ view.sorts.length }}</span></div>
        <div v-for="(s, i) in view?.sorts || []" :key="i" class="nvs-row">
          <button type="button" class="nvs-grip" title="جابه‌جایی اولویت" @click="moveSort(i, -1)"><GripVertical :size="13" /></button>
          <select v-model="s.property" class="nvs-select">
            <option v-for="p in properties" :key="p.key" :value="p.key">{{ p.label }}</option>
          </select>
          <button type="button" class="nvs-dir" :title="s.direction === 'asc' ? 'صعودی' : 'نزولی'" @click="s.direction = s.direction === 'asc' ? 'desc' : 'asc'">
            {{ s.direction === 'asc' ? '↑' : '↓' }}
          </button>
          <button type="button" class="nvs-x" @click="removeSort(i)"><X :size="13" /></button>
        </div>
        <div v-if="!view?.sorts?.length" class="nvs-empty">مرتب‌سازی فعالی نیست.</div>
        <button type="button" class="nvs-add" @click="addSort"><Plus :size="13" /> افزودن مرتب‌سازی</button>
      </div>

      <!-- ۴) گروه‌بندی -->
      <div class="nvs-section">
        <div class="nvs-section-title"><Layers :size="13" /> گروه‌بندی <span v-if="view?.groupBy" class="nvs-count">1</span></div>
        <label class="nvs-label">گروه‌بندی بر اساس</label>
        <select v-model="view.groupBy" class="nvs-select nvs-sel-wide">
          <option value="">بدون گروه</option>
          <option v-for="p in properties" :key="p.key" :value="p.key">{{ p.label }}</option>
        </select>
        <label class="nvs-label">زیرگروه (اختیاری)</label>
        <select v-model="view.subGroupBy" class="nvs-select nvs-sel-wide">
          <option value="">بدون زیرگروه</option>
          <option v-for="p in properties" :key="p.key" :value="p.key" :disabled="p.key === view.groupBy">{{ p.label }}</option>
        </select>
      </div>

      <!-- ۵) خواص نمایشی (درگ‌انددراپ) -->
      <div class="nvs-section">
        <div class="nvs-section-title"><Eye :size="13" /> خواص نمایشی</div>
        <div class="nvs-prop-list">
          <div
            v-for="(p, idx) in orderedProps"
            :key="p.key"
            class="nvs-prop-row"
            :class="{ dragging: dragPropKey === p.key, over: dropOverKey === p.key }"
            draggable="true"
            @dragstart="onPropDragStart(p.key)"
            @dragend="onPropDragEnd"
            @dragover.prevent="onPropDragOver(p.key)"
            @drop.prevent="onPropDrop(p.key)"
          >
            <span class="nvs-grip" title="درگ برای جابه‌جایی"><GripVertical :size="13" /></span>
            <button
              type="button"
              class="nvs-prop-toggle"
              :class="{ on: isPropVisible(p.key) }"
              :aria-pressed="isPropVisible(p.key)"
              @click="toggleProp(p.key, !isPropVisible(p.key))"
            >
              <span class="nvs-prop-name">{{ p.label }}</span>
              <span class="nvs-switch" aria-hidden="true">
                <span class="nvs-switch-dot"></span>
              </span>
            </button>
            <div class="nvs-prop-arrows">
              <button type="button" :disabled="idx === 0" @click="moveProp(p.key, -1)">↑</button>
              <button type="button" :disabled="idx === orderedProps.length - 1" @click="moveProp(p.key, 1)">↓</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ۶) رنگ شرطی -->
      <div class="nvs-section">
        <div class="nvs-section-title"><Palette :size="13" /> رنگ شرطی <span v-if="view?.colors?.length" class="nvs-count">{{ view.colors.length }}</span></div>
        <div v-for="(c, i) in view?.colors || []" :key="i" class="nvs-row">
          <select v-model="c.property" class="nvs-select" @change="resetOperator(c)">
            <option v-for="p in properties" :key="p.key" :value="p.key">{{ p.label }}</option>
          </select>
          <select v-model="c.operator" class="nvs-select">
            <option v-for="op in operatorsFor(c.property)" :key="op[0]" :value="op[0]">{{ op[1] }}</option>
          </select>
          <div
            v-if="propertyType(c.property) === 'select' && needsValue(c.property, c.operator)"
            class="nvs-dropdown-wrap"
          >
            <SearchableDropdown
              v-model="c.value"
              :options="optionsFor(c.property)"
              placeholder="انتخاب..."
              search-placeholder="جستجو..."
              clearable
              include-empty-option
              empty-label="همه"
            />
          </div>
          <div
            v-else-if="propertyType(c.property) === 'tags' && needsValue(c.property, c.operator)"
            class="nvs-dropdown-wrap"
          >
            <SearchableDropdown
              v-model="c.value"
              :options="optionsFor(c.property)"
              placeholder="انتخاب تگ..."
              search-placeholder="جستجوی تگ..."
              clearable
              include-empty-option
              empty-label="همه"
            />
          </div>
          <div v-else-if="propertyType(c.property) === 'boolean' && needsValue(c.property, c.operator)" class="nvs-bool">
            <button type="button" :class="['nvs-bool-btn', { active: c.value === 'بله' }]" @click="c.value = 'بله'">بله</button>
            <button type="button" :class="['nvs-bool-btn', { active: c.value === 'خیر' }]" @click="c.value = 'خیر'">خیر</button>
          </div>
          <input v-else-if="needsValue(c.property, c.operator)" v-model="c.value" class="nvs-input" :type="valueType(c.property)" placeholder="..." />
          <select v-model="c.color" class="nvs-color-sel" :style="{ backgroundColor: colorHex(c.color) }">
            <option v-for="opt in colorOptions" :key="opt[0]" :value="opt[0]">{{ opt[1] }}</option>
          </select>
          <button type="button" class="nvs-x" @click="removeColor(i)"><X :size="13" /></button>
        </div>
        <div v-if="!view?.colors?.length" class="nvs-empty">قانون رنگی فعال نیست.</div>
        <button type="button" class="nvs-add" @click="addColor"><Plus :size="13" /> افزودن قانون رنگ</button>
      </div>

      <!-- ۷) جستجو و بازنشانی -->
      <div class="nvs-section">
        <div class="nvs-section-title"><Search :size="13" /> جستجو</div>
        <input
          v-model="searchQuery"
          class="nvs-search"
          placeholder="جستجو در نما..."
          @input="$emit('search', searchQuery)"
        />
      </div>

      <div class="nvs-footer">
        <button type="button" class="nvs-reset" @click="$emit('reset', view?.id)">
          <RotateCcw :size="13" /> بازنشانی نما
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ArrowUpDown,
  Calendar,
  Table,
  ChevronDown,
  Eye,
  Filter,
  GripVertical,
  Layers,
  LayoutGrid,
  LayoutList,
  List,
  Palette,
  Plus,
  RotateCcw,
  Search,
  Settings,
  X,
  Kanban,
} from "lucide-vue-next";
import SearchableDropdown from "@/components/SearchableDropdown.vue";
import { COLOR_OPTIONS, operatorNeedsValue, operatorOptionsFor, propertyTypeFor } from "@/utils/viewSystem";

const props = defineProps({
  view: { type: Object, default: null },
  properties: { type: Array, default: () => [] },
  selectOptions: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["reset", "search", "update"]);

const open = ref(false);
const rootRef = ref(null);
const searchQuery = ref("");
const dragPropKey = ref("");
const dropOverKey = ref("");

const layouts = [
  { value: "list", label: "لیست", icon: List },
  { value: "gallery", label: "گالری", icon: LayoutGrid },
  { value: "tree", label: "درخت", icon: LayoutList },
  { value: "calendar", label: "تقویم", icon: Calendar },
  { value: "sheet", label: "جدول", icon: Table },
  { value: "kanban", label: "کانبان", icon: Kanban },
];

const colorOptions = COLOR_OPTIONS;

const hasActive = computed(() => {
  const v = props.view;
  return Boolean(v && (v.filters?.length || v.sorts?.length || v.groupBy || v.colors?.length));
});

const orderedProps = computed(() => {
  const order = props.view?.propertyOrder || [];
  const map = new Map(props.properties.map((p) => [p.key, p]));
  const list = order.map((k) => map.get(k)).filter(Boolean);
  for (const p of props.properties) {
    if (!list.some((x) => x.key === p.key)) list.push(p);
  }
  return list;
});

function update(patch) {
  // مستقیم روی view اعمال کن (reactive است) + emit برای سازگاری
  if (props.view && patch && typeof patch === "object") {
    Object.assign(props.view, patch);
  }
  emit("update", patch);
}

function isPropVisible(key) {
  return props.view?.properties?.[key] !== false;
}

function toggleProp(key, visible) {
  if (!props.view) return;
  if (!props.view.properties) props.view.properties = {};
  props.view.properties[key] = visible;
  if (visible && !props.view.propertyOrder.includes(key)) {
    props.view.propertyOrder.push(key);
  }
}

function moveProp(key, delta) {
  const order = props.view?.propertyOrder || [];
  const idx = order.indexOf(key);
  const target = idx + delta;
  if (idx < 0 || target < 0 || target >= order.length) return;
  const [item] = order.splice(idx, 1);
  order.splice(target, 0, item);
}

// ── درگ‌انددراپ ترتیب خواص ──────────────────────────────────────────────────
function onPropDragStart(key) {
  dragPropKey.value = key;
}

function onPropDragEnd() {
  dragPropKey.value = "";
  dropOverKey.value = "";
}

function onPropDragOver(key) {
  if (key !== dragPropKey.value) dropOverKey.value = key;
}

function onPropDrop(targetKey) {
  const order = props.view?.propertyOrder || [];
  const from = order.indexOf(dragPropKey.value);
  const to = order.indexOf(targetKey);
  if (from < 0 || to < 0 || from === to) {
    onPropDragEnd();
    return;
  }
  const [item] = order.splice(from, 1);
  order.splice(to, 0, item);
  onPropDragEnd();
}

function operatorsFor(propertyKey) {
  return operatorOptionsFor(propertyKey, props.properties);
}

function needsValue(propertyKey, operator) {
  return operatorNeedsValue(propertyKey, operator, props.properties);
}

function valueType(propertyKey) {
  const p = props.properties.find((x) => x.key === propertyKey);
  return p?.type === "number" ? "number" : "text";
}

function resetOperator(filter) {
  const type = propertyTypeFor(filter.property, props.properties);
  if (type === "boolean") {
    filter.operator = "equals";
  } else {
    const ops = operatorsFor(filter.property);
    if (ops.length) filter.operator = ops[0][0];
  }
  filter.value = "";
}

function optionsFor(propertyKey) {
  return props.selectOptions?.[propertyKey] || [];
}

function propertyType(propertyKey) {
  return propertyTypeFor(propertyKey, props.properties);
}

function addFilter() {
  if (!props.view) return;
  if (!props.view.filters) props.view.filters = [];
  props.view.filters.push({ joiner: "and", property: props.properties[0]?.key, operator: "contains", value: "" });
}

function removeFilter(index) {
  props.view?.filters?.splice(index, 1);
}

function addSort() {
  if (!props.view) return;
  if (!props.view.sorts) props.view.sorts = [];
  props.view.sorts.push({ property: props.properties[0]?.key, direction: "asc" });
}

function removeSort(index) {
  props.view?.sorts?.splice(index, 1);
}

function moveSort(index, delta) {
  const sorts = props.view?.sorts;
  if (!sorts) return;
  const target = index + delta;
  if (target < 0 || target >= sorts.length) return;
  const [item] = sorts.splice(index, 1);
  sorts.splice(target, 0, item);
}

function addColor() {
  if (!props.view) return;
  if (!props.view.colors) props.view.colors = [];
  props.view.colors.push({ property: props.properties[0]?.key, operator: "contains", value: "", color: "red" });
}

function removeColor(index) {
  props.view?.colors?.splice(index, 1);
}

const COLOR_HEX = {
  red: "#ef4444",
  orange: "#f97316",
  yellow: "#eab308",
  green: "#22c55e",
  blue: "#3b82f6",
  gray: "#6b7280",
};

function colorHex(color) {
  return COLOR_HEX[color] || "#6b7280";
}

function onOutsideClick(event) {
  if (rootRef.value && !rootRef.value.contains(event.target)) {
    open.value = false;
  }
}

onMounted(() => document.addEventListener("click", onOutsideClick));
onBeforeUnmount(() => document.removeEventListener("click", onOutsideClick));
</script>

<style scoped>
.nvs-bool {
  display: flex;
  gap: 0.2rem;
  flex-shrink: 0;
}

.nvs-bool-btn {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  font-family: inherit;
  font-size: 0.66rem;
  border-radius: 6px;
  padding: 0.2rem 0.45rem;
  cursor: pointer;
  transition: all 0.12s ease;
}

.nvs-bool-btn.active {
  background: color-mix(in srgb, var(--mg-primary) 15%, var(--mg-bg-surface));
  border-color: var(--mg-primary);
  color: var(--mg-primary);
  font-weight: 600;
}

.nvs {
  position: relative;
}

.nvs-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.24rem 0.6rem;
  border-radius: 8px;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  color: var(--mg-text-muted);
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.12s ease;
}

.nvs-trigger:hover,
.nvs-trigger.active {
  border-color: color-mix(in srgb, var(--mg-primary) 55%, var(--mg-border));
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 5%, var(--mg-bg-surface));
}

.nvs-trigger.has {
  border-color: color-mix(in srgb, var(--mg-primary) 55%, var(--mg-border-light));
  color: var(--mg-primary);
}

.nvs-chev {
  transition: transform 0.15s ease;
}

.nvs-chev.open {
  transform: rotate(180deg);
}

.nvs-panel {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 70;
  width: 380px;
  max-width: calc(100vw - 1.5rem);
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: 14px;
  box-shadow: var(--mg-shadow-md);
  padding: 0.7rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  max-height: min(640px, 85vh);
  overflow-y: auto;
  scrollbar-width: thin;
}

.nvs-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding-bottom: 0.45rem;
  border-bottom: 1px solid var(--mg-border-light);
}

.nvs-head-title {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.nvs-head strong {
  font-size: 0.84rem;
  color: var(--mg-text-main);
}

.nvs-view-name {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
}

.nvs-close {
  border: 0;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
  display: inline-flex;
  padding: 0.2rem;
  border-radius: 6px;
}

.nvs-close:hover {
  background: color-mix(in srgb, var(--mg-bg-soft) 70%, transparent);
  color: var(--mg-text-main);
}

.nvs-section {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.nvs-section-title {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--mg-text-muted);
}

.nvs-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--mg-primary) 15%, transparent);
  color: var(--mg-primary);
  font-size: 0.6rem;
  font-weight: 700;
}

.nvs-layouts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
}

.nvs-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.45rem 0.3rem;
  border-radius: 9px;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  font-family: inherit;
  font-size: 0.66rem;
  cursor: pointer;
  transition: all 0.12s ease;
}

.nvs-layout:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
  color: var(--mg-primary);
}

.nvs-layout.active {
  border-color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 9%, var(--mg-bg-surface));
  color: var(--mg-primary);
  font-weight: 600;
}

.nvs-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: nowrap;
}

.nvs-select {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  border-radius: 7px;
  padding: 0.2rem 0.3rem;
  font-size: 0.68rem;
  font-family: inherit;
  flex: 1;
  min-width: 0;
}

.nvs-joiner {
  flex: 0 0 auto;
  width: 54px;
  font-weight: 700;
  color: var(--mg-primary);
}

.nvs-sel-wide {
  flex: 1;
}

.nvs-input {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  border-radius: 7px;
  padding: 0.2rem 0.35rem;
  font-size: 0.68rem;
  font-family: inherit;
  width: 72px;
  flex: 1;
}

.nvs-x {
  border: 0;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
  display: inline-flex;
  padding: 0.15rem;
  flex-shrink: 0;
}

.nvs-x:hover {
  color: var(--mg-danger);
}

.nvs-grip {
  border: 0;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: grab;
  display: inline-flex;
  padding: 0.1rem;
  opacity: 0.55;
  flex-shrink: 0;
}

.nvs-grip:hover {
  opacity: 1;
  color: var(--mg-primary);
}

.nvs-dir {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-primary);
  border-radius: 6px;
  width: 28px;
  height: 24px;
  font-size: 0.75rem;
  cursor: pointer;
  flex-shrink: 0;
}

.nvs-add {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  border: 1px dashed var(--mg-border);
  background: transparent;
  color: var(--mg-text-muted);
  border-radius: 7px;
  padding: 0.28rem 0.5rem;
  font-size: 0.68rem;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.12s ease;
}

.nvs-add:hover {
  border-color: var(--mg-primary);
  color: var(--mg-primary);
}

.nvs-empty {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
  padding: 0.2rem 0;
}

.nvs-label {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
  font-weight: 600;
}

.nvs-prop-list {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.nvs-prop-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.14rem 0.25rem;
  border-radius: 7px;
  border: 1px solid transparent;
  cursor: grab;
  transition: background 0.1s ease, border-color 0.1s ease, opacity 0.1s ease;
}

.nvs-prop-row:hover {
  background: color-mix(in srgb, var(--mg-bg-soft) 60%, transparent);
}

.nvs-prop-row.dragging {
  opacity: 0.4;
  border-color: var(--mg-primary);
}

.nvs-prop-row.over {
  border-color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
}

.nvs-prop-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex: 1;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  border-radius: 8px;
  padding: 0.28rem 0.5rem;
  font-family: inherit;
  font-size: 0.74rem;
  cursor: pointer;
  transition: all 0.12s ease;
  min-width: 0;
}

.nvs-prop-toggle:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
}

.nvs-prop-toggle.on {
  border-color: color-mix(in srgb, var(--mg-primary) 45%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-primary) 7%, var(--mg-bg-surface));
  color: var(--mg-primary);
  font-weight: 600;
}

.nvs-prop-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nvs-switch {
  position: relative;
  width: 30px;
  height: 17px;
  border-radius: 999px;
  background: var(--mg-border);
  transition: background 0.15s ease;
  flex-shrink: 0;
}

.nvs-prop-toggle.on .nvs-switch {
  background: var(--mg-success);
}

.nvs-switch-dot {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: #fff;
  transition: transform 0.15s ease;
  box-shadow: 0 1px 3px rgb(0 0 0 / 0.25);
}

.nvs-prop-toggle.on .nvs-switch-dot {
  transform: translateX(-13px);
}

.nvs-prop-arrows {
  display: flex;
  gap: 2px;
}

.nvs-prop-arrows button {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  border-radius: 5px;
  width: 20px;
  height: 20px;
  font-size: 0.65rem;
  cursor: pointer;
}

.nvs-prop-arrows button:disabled {
  opacity: 0.3;
  cursor: default;
}

.nvs-color-sel {
  border: 1px solid var(--mg-border-light);
  border-radius: 6px;
  padding: 0.15rem 0.25rem;
  font-size: 0.65rem;
  font-family: inherit;
  color: #fff;
  flex-shrink: 0;
  width: 74px;
}

.nvs-search {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  border-radius: 8px;
  padding: 0.3rem 0.5rem;
  font-size: 0.72rem;
  font-family: inherit;
  width: 100%;
  outline: none;
}

.nvs-search:focus {
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
}

.nvs-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.4rem;
  border-top: 1px solid var(--mg-border-light);
}

.nvs-reset {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border: 0;
  background: transparent;
  color: var(--mg-danger);
  font-family: inherit;
  font-size: 0.7rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.25rem 0.4rem;
  border-radius: 7px;
}

.nvs-reset:hover {
  background: var(--mg-danger-bg);
}
</style>
