<template>
  <div class="nvc" ref="rootRef">
    <div class="nvc-bar">
      <!-- فیلتر -->
      <div class="nvc-wrap">
        <button
          type="button"
          class="nvc-btn"
          :class="{ active: open === 'filter', has: view?.filters?.length }"
          @click="toggle('filter')"
        >
          <Filter :size="13" /> فیلتر <span v-if="view?.filters?.length" class="nvc-badge">{{ view.filters.length }}</span>
        </button>
        <div v-if="open === 'filter'" class="nvc-panel">
          <div class="nvc-panel-head">
            <strong><Filter :size="12" /> فیلترها</strong>
            <button type="button" class="nvc-panel-close" @click="open = ''"><X :size="13" /></button>
          </div>

          <div v-for="(f, i) in view?.filters || []" :key="i" class="nvc-filter-card">
            <div class="nvc-filter-head">
              <span v-if="i > 0" class="nvc-joiner-pill">{{ f.joiner === 'or' ? 'یا' : 'و' }}</span>
              <span class="nvc-filter-label">فیلتر {{ i + 1 }}</span>
              <button type="button" class="nvc-x" title="حذف فیلتر" @click="removeFilter(i)"><X :size="12" /></button>
            </div>
            <div class="nvc-filter-row">
              <SearchableDropdown
                :model-value="f.property"
                :options="propertyOptions"
                placeholder="انتخاب فیلد..."
                search-placeholder="جستجوی فیلد..."
                @update:model-value="onPropertyChange(f, $event)"
              />
              <SearchableDropdown
                :model-value="f.operator"
                :options="operatorOptionsForDropdown(f.property)"
                placeholder="شرط..."
                search-placeholder="جستجوی شرط..."
                @update:model-value="onOperatorChange(f, $event)"
              />
            </div>
            <div class="nvc-filter-value">
              <span class="nvc-value-label">مقدار</span>
              <div
                v-if="operatorIsMulti(f.operator) && needsValue(f.property, f.operator)"
                class="nvc-dropdown-wrap nvc-dropdown-wrap--wide"
              >
                <SearchableDropdown
                  :model-value="multiValueOf(f)"
                  :options="optionsFor(f.property)"
                  placeholder="انتخاب چند مورد..."
                  search-placeholder="جستجوی مقدار..."
                  multiple
                  clearable
                  include-empty-option
                  empty-label="همه"
                  @update:model-value="setMultiValue(f, $event)"
                />
              </div>
              <div
                v-else-if="propertyType(f.property) === 'select' && needsValue(f.property, f.operator)"
                class="nvc-dropdown-wrap nvc-dropdown-wrap--wide"
              >
                <SearchableDropdown
                  v-model="f.value"
                  :options="optionsFor(f.property)"
                  placeholder="انتخاب کنید..."
                  search-placeholder="جستجوی مقدار..."
                  clearable
                  include-empty-option
                  empty-label="همه"
                />
              </div>
              <div
                v-else-if="propertyType(f.property) === 'tags' && needsValue(f.property, f.operator)"
                class="nvc-dropdown-wrap nvc-dropdown-wrap--wide"
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
              <div v-else-if="propertyType(f.property) === 'boolean' && needsValue(f.property, f.operator)" class="nvc-bool">
                <button type="button" :class="['nvc-bool-btn', { active: f.value === 'بله' }]" @click="f.value = 'بله'">بله</button>
                <button type="button" :class="['nvc-bool-btn', { active: f.value === 'خیر' }]" @click="f.value = 'خیر'">خیر</button>
              </div>
              <input
                v-else-if="needsValue(f.property, f.operator)"
                v-model="f.value"
                class="nvc-inp nvc-inp--wide"
                :type="valueType(f.property)"
                :placeholder="'مقدار ' + propertyLabel(f.property) + '...'"
              />
            </div>
          </div>

          <div v-if="!view?.filters?.length" class="nvc-empty">هیچ فیلتری فعال نیست.</div>
          <button type="button" class="nvc-add" @click="addFilter"><Plus :size="12" /> افزودن فیلتر</button>
        </div>
      </div>

      <!-- مرتب‌سازی -->
      <div class="nvc-wrap">
        <button
          type="button"
          class="nvc-btn"
          :class="{ active: open === 'sort', has: view?.sorts?.length }"
          @click="toggle('sort')"
        >
          <ArrowUpDown :size="13" /> مرتب‌سازی <span v-if="view?.sorts?.length" class="nvc-badge">{{ view.sorts.length }}</span>
        </button>
        <div v-if="open === 'sort'" class="nvc-panel">
          <div class="nvc-panel-head">
            <strong><ArrowUpDown :size="12" /> مرتب‌سازی</strong>
            <button type="button" class="nvc-panel-close" @click="open = ''"><X :size="13" /></button>
          </div>
          <div v-for="(s, i) in view?.sorts || []" :key="i" class="nvc-row nvc-sort-row">
            <button type="button" class="nvc-grip" title="جابه‌جایی اولویت" @click="moveSort(i, -1)"><GripVertical :size="12" /></button>
            <SearchableDropdown
              :model-value="s.property"
              :options="propertyOptions"
              placeholder="فیلد..."
              search-placeholder="جستجو..."
              @update:model-value="s.property = $event || ''"
            />
            <button type="button" class="nvc-dir" :title="s.direction === 'asc' ? 'صعودی' : 'نزولی'" @click="s.direction = s.direction === 'asc' ? 'desc' : 'asc'">
              {{ s.direction === 'asc' ? '↑' : '↓' }}
            </button>
            <button type="button" class="nvc-x" title="حذف" @click="removeSort(i)"><X :size="12" /></button>
          </div>
          <div v-if="!view?.sorts?.length" class="nvc-empty">مرتب‌سازی فعالی نیست.</div>
          <button type="button" class="nvc-add" @click="addSort"><Plus :size="12" /> افزودن مرتب‌سازی</button>
        </div>
      </div>

      <!-- گروه‌بندی -->
      <div class="nvc-wrap">
        <button
          type="button"
          class="nvc-btn"
          :class="{ active: open === 'group', has: view?.groupBy }"
          @click="toggle('group')"
        >
          <Layers :size="13" /> گروه <span v-if="view?.groupBy" class="nvc-badge">1</span>
        </button>
        <div v-if="open === 'group'" class="nvc-panel">
          <div class="nvc-panel-head">
            <strong><Layers :size="12" /> گروه‌بندی</strong>
            <button type="button" class="nvc-panel-close" @click="open = ''"><X :size="13" /></button>
          </div>
          <label class="nvc-label">گروه‌بندی بر اساس</label>
          <SearchableDropdown
            :model-value="view.groupBy"
            :options="propertyOptions"
            placeholder="بدون گروه"
            search-placeholder="جستجو..."
            include-empty-option
            empty-label="بدون گروه"
            @update:model-value="view.groupBy = $event || ''"
          />
          <label class="nvc-label">زیرگروه (اختیاری)</label>
          <SearchableDropdown
            :model-value="view.subGroupBy"
            :options="propertyOptions"
            placeholder="بدون زیرگروه"
            search-placeholder="جستجو..."
            include-empty-option
            empty-label="بدون زیرگروه"
            @update:model-value="view.subGroupBy = $event || ''"
          />
        </div>
      </div>

      <!-- خواص (درگ‌انددراپ) -->
      <div class="nvc-wrap">
        <button
          type="button"
          class="nvc-btn"
          :class="{ active: open === 'props' }"
          @click="toggle('props')"
        >
          <Eye :size="13" /> خواص
        </button>
        <div v-if="open === 'props'" class="nvc-panel">
          <div class="nvc-panel-head">
            <strong><Eye :size="12" /> خواص نمایشی</strong>
            <button type="button" class="nvc-panel-close" @click="open = ''"><X :size="13" /></button>
          </div>
          <div class="nvc-hint">برای جابه‌جایی ترتیب، بکشید</div>
          <div class="nvc-prop-list">
            <div
              v-for="(p, idx) in orderedProps"
              :key="p.key"
              class="nvc-prop-row"
              :class="{ dragging: dragPropKey === p.key, over: dropOverKey === p.key }"
              draggable="true"
              @dragstart="onPropDragStart(p.key)"
              @dragend="onPropDragEnd"
              @dragover.prevent="onPropDragOver(p.key)"
              @drop.prevent="onPropDrop(p.key)"
            >
              <span class="nvc-grip" title="درگ"><GripVertical :size="12" /></span>
              <button
                type="button"
                class="nvc-prop-toggle"
                :class="{ on: isPropVisible(p.key) }"
                :aria-pressed="isPropVisible(p.key)"
                @click="toggleProp(p.key, !isPropVisible(p.key))"
              >
                <span class="nvc-prop-name">{{ p.label }}</span>
                <span class="nvc-switch" aria-hidden="true">
                  <span class="nvc-switch-dot"></span>
                </span>
              </button>
              <div class="nvc-arrows">
                <button type="button" :disabled="idx === 0" @click="moveProp(p.key, -1)">↑</button>
                <button type="button" :disabled="idx === orderedProps.length - 1" @click="moveProp(p.key, 1)">↓</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- رنگ شرطی -->
      <div class="nvc-wrap">
        <button
          type="button"
          class="nvc-btn"
          :class="{ active: open === 'color', has: view?.colors?.length }"
          @click="toggle('color')"
        >
          <Palette :size="13" /> رنگ <span v-if="view?.colors?.length" class="nvc-badge">{{ view.colors.length }}</span>
        </button>
        <div v-if="open === 'color'" class="nvc-panel">
          <div class="nvc-panel-head">
            <strong><Palette :size="12" /> رنگ شرطی</strong>
            <button type="button" class="nvc-panel-close" @click="open = ''"><X :size="13" /></button>
          </div>
          <div v-for="(c, i) in view?.colors || []" :key="i" class="nvc-row">
            <SearchableDropdown
              :model-value="c.property"
              :options="propertyOptions"
              placeholder="فیلد..."
              search-placeholder="جستجو..."
              @update:model-value="onPropertyChange(c, $event)"
            />
            <SearchableDropdown
              :model-value="c.operator"
              :options="operatorOptionsForDropdown(c.property)"
              placeholder="شرط..."
              search-placeholder="جستجو..."
              @update:model-value="onOperatorChange(c, $event)"
            />
            <div
              v-if="operatorIsMulti(c.operator) && needsValue(c.property, c.operator)"
              class="nvc-dropdown-wrap nvc-dropdown-wrap--wide"
            >
              <SearchableDropdown
                :model-value="multiValueOf(c)"
                :options="optionsFor(c.property)"
                placeholder="انتخاب چند مورد..."
                search-placeholder="جستجو..."
                multiple
                clearable
                include-empty-option
                empty-label="همه"
                @update:model-value="setMultiValue(c, $event)"
              />
            </div>
            <div
              v-else-if="propertyType(c.property) === 'select' && needsValue(c.property, c.operator)"
              class="nvc-dropdown-wrap nvc-dropdown-wrap--wide"
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
              class="nvc-dropdown-wrap nvc-dropdown-wrap--wide"
            >
              <SearchableDropdown
                v-model="c.value"
                :options="optionsFor(c.property)"
                placeholder="انتخاب تگ..."
                search-placeholder="جستجو..."
                clearable
                include-empty-option
                empty-label="همه"
              />
            </div>
            <div v-else-if="propertyType(c.property) === 'boolean' && needsValue(c.property, c.operator)" class="nvc-bool">
              <button type="button" :class="['nvc-bool-btn', { active: c.value === 'بله' }]" @click="c.value = 'بله'">بله</button>
              <button type="button" :class="['nvc-bool-btn', { active: c.value === 'خیر' }]" @click="c.value = 'خیر'">خیر</button>
            </div>
            <input v-else-if="needsValue(c.property, c.operator)" v-model="c.value" class="nvc-inp" :type="valueType(c.property)" placeholder="..." />
            <select v-model="c.color" class="nvc-color-sel" :style="{ backgroundColor: colorHex(c.color) }">
              <option v-for="opt in colorOptions" :key="opt[0]" :value="opt[0]">{{ opt[1] }}</option>
            </select>
            <button type="button" class="nvc-x" @click="removeColor(i)"><X :size="12" /></button>
          </div>
          <div v-if="!view?.colors?.length" class="nvc-empty">قانون رنگی فعال نیست.</div>
          <button type="button" class="nvc-add" @click="addColor"><Plus :size="12" /> افزودن قانون رنگ</button>
        </div>
      </div>

      <button v-if="hasActive" type="button" class="nvc-btn nvc-clear" title="پاک کردن همه تنظیمات نما" @click="clearAll"><X :size="12" /> پاک کردن</button>
    </div>

    <!-- چیپ‌های فعال -->
    <div v-if="hasActive" class="nvc-chips">
      <span v-for="(f, i) in view?.filters || []" :key="`f${i}`" class="nvc-chip">
        {{ propertyLabel(f.property) }} {{ operatorLabel(f.property, f.operator) }} {{ displayValue(f.value) }}
        <button type="button" class="nvc-chip-x" @click="removeFilter(i)">×</button>
      </span>
      <span v-for="(s, i) in view?.sorts || []" :key="`s${i}`" class="nvc-chip">
        {{ propertyLabel(s.property) }} {{ s.direction === 'asc' ? '↑' : '↓' }}
        <button type="button" class="nvc-chip-x" @click="removeSort(i)">×</button>
      </span>
      <span v-if="view?.groupBy" class="nvc-chip">
        گروه: {{ propertyLabel(view.groupBy) }}<span v-if="view.subGroupBy"> ← {{ propertyLabel(view.subGroupBy) }}</span>
        <button type="button" class="nvc-chip-x" @click="view.groupBy = ''; view.subGroupBy = ''">×</button>
      </span>
      <span v-if="view?.colors?.length" class="nvc-chip">
        رنگ: {{ view.colors.length }} قانون
        <button type="button" class="nvc-chip-x" @click="view.colors = []">×</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { ArrowUpDown, Eye, Filter, GripVertical, Layers, Palette, Plus, X } from "lucide-vue-next";
import SearchableDropdown from "@/components/SearchableDropdown.vue";
import {
  COLOR_OPTIONS,
  operatorIsMulti,
  operatorNeedsValue,
  operatorOptionsFor,
  propertyTypeFor,
} from "@/utils/viewSystem";

const props = defineProps({
  view: { type: Object, default: null },
  properties: { type: Array, default: () => [] },
  selectOptions: { type: Object, default: () => ({}) },
});

const rootRef = ref(null);
const open = ref("");
const dragPropKey = ref("");
const dropOverKey = ref("");

const colorOptions = COLOR_OPTIONS;

const orderedProps = computed(() => {
  const order = props.view?.propertyOrder || [];
  const map = new Map(props.properties.map((p) => [p.key, p]));
  const list = order.map((k) => map.get(k)).filter(Boolean);
  for (const p of props.properties) {
    if (!list.some((x) => x.key === p.key)) list.push(p);
  }
  return list;
});

const hasActive = computed(() => {
  const v = props.view;
  return Boolean(v && (v.filters?.length || v.sorts?.length || v.groupBy || v.colors?.length));
});

const propertyOptions = computed(() =>
  props.properties.map((p) => ({ value: p.key, label: p.label })),
);

function toggle(panel) {
  open.value = open.value === panel ? "" : panel;
}

function operatorsFor(propertyKey) {
  return operatorOptionsFor(propertyKey, props.properties);
}

function operatorOptionsForDropdown(propertyKey) {
  return operatorsFor(propertyKey).map(([value, label]) => ({ value, label }));
}

function optionsFor(propertyKey) {
  return props.selectOptions?.[propertyKey] || [];
}

function propertyType(propertyKey) {
  return propertyTypeFor(propertyKey, props.properties);
}

function needsValue(propertyKey, operator) {
  return operatorNeedsValue(propertyKey, operator, props.properties);
}

function valueType(propertyKey) {
  const p = props.properties.find((x) => x.key === propertyKey);
  return p?.type === "number" ? "number" : "text";
}

function resetOperator(filter) {
  const type = propertyType(filter.property);
  if (type === "boolean") {
    filter.operator = "equals";
  } else {
    const ops = operatorsFor(filter.property);
    if (ops.length) filter.operator = ops[0][0];
  }
  filter.value = "";
}

function onPropertyChange(filter, value) {
  filter.property = value || props.properties[0]?.key || "";
  resetOperator(filter);
}

function onOperatorChange(filter, value) {
  filter.operator = value || "";
  if (operatorIsMulti(filter.operator)) {
    filter.value = Array.isArray(filter.value) ? filter.value : [];
  }
}

function multiValueOf(filter) {
  if (Array.isArray(filter.value)) return filter.value;
  if (!filter.value) return [];
  return String(filter.value).split(",").map((v) => v.trim()).filter(Boolean);
}

function setMultiValue(filter, value) {
  filter.value = Array.isArray(value) ? value : [];
}

function displayValue(value) {
  if (Array.isArray(value)) return value.join("، ");
  return value || "";
}

function propertyLabel(key) {
  return props.properties.find((p) => p.key === key)?.label || key;
}

function operatorLabel(propertyKey, operator) {
  return operatorsFor(propertyKey).find((o) => o[0] === operator)?.[1] || operator;
}

function addFilter() {
  if (!props.view) return;
  if (!props.view.filters) props.view.filters = [];
  props.view.filters.push({ joiner: "and", property: props.properties[0]?.key, operator: "equals", value: "" });
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

function addColor() {
  if (!props.view) return;
  if (!props.view.colors) props.view.colors = [];
  props.view.colors.push({ property: props.properties[0]?.key, operator: "equals", value: "", color: "red" });
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

function clearAll() {
  const v = props.view;
  if (!v) return;
  v.filters = [];
  v.sorts = [];
  v.groupBy = "";
  v.subGroupBy = "";
  v.colors = [];
}

function onOutsideClick(event) {
  if (rootRef.value && !rootRef.value.contains(event.target)) {
    open.value = "";
  }
}

onMounted(() => document.addEventListener("click", onOutsideClick));
onBeforeUnmount(() => document.removeEventListener("click", onOutsideClick));
</script>

<style scoped>
.nvc {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.nvc-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.nvc-wrap {
  position: relative;
}

.nvc-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
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

.nvc-btn:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 55%, var(--mg-border));
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 5%, var(--mg-bg-surface));
}

.nvc-btn.active {
  border-color: var(--mg-primary);
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
}

.nvc-btn.has {
  border-color: color-mix(in srgb, var(--mg-primary) 55%, var(--mg-border-light));
  color: var(--mg-primary);
}

.nvc-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--mg-success);
  color: #fff;
  font-size: 0.62rem;
  font-weight: 700;
}

.nvc-clear {
  border-color: color-mix(in srgb, var(--mg-danger) 35%, var(--mg-border-light));
  color: var(--mg-danger);
}

/* پنل اصلی — dropdown ها باید بیرونش باز شوند */
.nvc-panel {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 65;
  min-width: 360px;
  max-width: 420px;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: 14px;
  box-shadow: var(--mg-shadow-md);
  padding: 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 480px;
  overflow-y: auto;
  overflow-x: visible;
  scrollbar-width: thin;
}

.nvc-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--mg-border-light);
  flex-shrink: 0;
}

.nvc-panel-head strong {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.76rem;
  color: var(--mg-text-main);
}

.nvc-panel-close {
  border: 0;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
  display: inline-flex;
  padding: 0.15rem;
  border-radius: 6px;
}

.nvc-panel-close:hover {
  background: color-mix(in srgb, var(--mg-bg-soft) 70%, transparent);
  color: var(--mg-text-main);
}

/* کارت فیلتر */
.nvc-filter-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.45rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: color-mix(in srgb, var(--mg-bg-soft) 30%, var(--mg-bg-surface));
  flex-shrink: 0;
}

.nvc-filter-head {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.nvc-filter-label {
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--mg-text-muted);
  flex: 1;
}

.nvc-joiner-pill {
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
}

.nvc-filter-row {
  display: flex;
  gap: 0.35rem;
  align-items: center;
}

.nvc-filter-row .nvc-dropdown-wrap,
.nvc-filter-value .nvc-dropdown-wrap {
  flex: 1;
  min-width: 0;
  max-width: none;
}

.nvc-filter-value {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.nvc-value-label {
  font-size: 0.64rem;
  color: var(--mg-text-muted);
  flex-shrink: 0;
  min-width: 34px;
}

.nvc-dropdown-wrap {
  flex: 1;
  min-width: 0;
  max-width: 140px;
}

.nvc-dropdown-wrap--wide {
  flex: 1;
  max-width: none;
}

.nvc-dropdown-wrap :deep(.searchable-dropdown) {
  width: 100%;
}

.nvc-dropdown-wrap :deep(.searchable-dropdown .select) {
  min-height: 28px;
  padding: 0.18rem 0.45rem;
  font-size: 0.7rem;
  border-color: var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  border-radius: 8px;
}

.nvc-dropdown-wrap :deep(.searchable-dropdown .select:hover) {
  border-color: color-mix(in srgb, var(--mg-primary) 45%, var(--mg-border));
}

.nvc-dropdown-wrap :deep(.searchable-dropdown .selected-label) {
  color: var(--mg-text-main);
  font-size: 0.7rem;
}

.nvc-dropdown-wrap :deep(.searchable-dropdown .dropdown-panel) {
  max-width: 260px;
  min-width: 180px;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  box-shadow: var(--mg-shadow-md);
}

.nvc-dropdown-wrap :deep(.searchable-dropdown .option-btn) {
  color: var(--mg-text-main);
  font-size: 0.72rem;
  border-radius: 7px;
}

.nvc-dropdown-wrap :deep(.searchable-dropdown .option-btn:hover),
.nvc-dropdown-wrap :deep(.searchable-dropdown .option-btn.selected) {
  background: color-mix(in srgb, var(--mg-primary) 10%, var(--mg-bg-surface));
  color: var(--mg-primary);
}

.nvc-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: nowrap;
}

.nvc-sel {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  border-radius: 7px;
  padding: 0.2rem 0.3rem;
  font-size: 0.68rem;
  font-family: inherit;
  min-width: 0;
  flex: 1;
}

.nvc-joiner {
  flex: 0 0 auto;
  width: 54px;
  font-weight: 700;
  color: var(--mg-primary);
}

.nvc-sel-wide {
  flex: 1;
}

.nvc-inp {
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

.nvc-inp--wide {
  flex: 1;
  width: auto;
}

.nvc-x {
  border: 0;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
  display: inline-flex;
  padding: 0.15rem;
  flex-shrink: 0;
}

.nvc-x:hover {
  color: var(--mg-danger);
}

.nvc-grip {
  border: 0;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: grab;
  display: inline-flex;
  padding: 0.1rem;
  opacity: 0.55;
  flex-shrink: 0;
}

.nvc-grip:hover {
  opacity: 1;
  color: var(--mg-primary);
}

.nvc-dir {
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

.nvc-add {
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

.nvc-add:hover {
  border-color: var(--mg-primary);
  color: var(--mg-primary);
}

.nvc-empty {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
  padding: 0.2rem 0;
}

.nvc-label {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
  font-weight: 600;
}

.nvc-hint {
  font-size: 0.66rem;
  color: var(--mg-text-muted);
  padding-bottom: 0.15rem;
}

.nvc-bool {
  display: flex;
  gap: 0.2rem;
  flex-shrink: 0;
}

.nvc-bool-btn {
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

.nvc-bool-btn.active {
  background: color-mix(in srgb, var(--mg-success) 15%, var(--mg-bg-surface));
  border-color: var(--mg-success);
  color: var(--mg-success);
  font-weight: 600;
}

.nvc-prop-list {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.nvc-prop-row {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.14rem 0.25rem;
  border-radius: 7px;
  border: 1px solid transparent;
  cursor: grab;
  transition: background 0.1s ease, border-color 0.1s ease, opacity 0.1s ease;
}

.nvc-prop-row:hover {
  background: color-mix(in srgb, var(--mg-bg-soft) 60%, transparent);
}

.nvc-prop-row.dragging {
  opacity: 0.4;
  border-color: var(--mg-primary);
}

.nvc-prop-row.over {
  border-color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
}

.nvc-prop-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex: 1;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  border-radius: 8px;
  padding: 0.26rem 0.45rem;
  font-family: inherit;
  font-size: 0.72rem;
  cursor: pointer;
  transition: all 0.12s ease;
  min-width: 0;
}

.nvc-prop-toggle:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
}

.nvc-prop-toggle.on {
  border-color: color-mix(in srgb, var(--mg-success) 45%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-success) 7%, var(--mg-bg-surface));
  color: var(--mg-success);
  font-weight: 600;
}

.nvc-prop-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nvc-switch {
  position: relative;
  width: 30px;
  height: 17px;
  border-radius: 999px;
  background: var(--mg-border);
  transition: background 0.15s ease;
  flex-shrink: 0;
}

.nvc-prop-toggle.on .nvc-switch {
  background: var(--mg-success);
}

.nvc-switch-dot {
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

.nvc-prop-toggle.on .nvc-switch-dot {
  transform: translateX(-13px);
}

.nvc-arrows {
  display: flex;
  gap: 2px;
}

.nvc-arrows button {
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  border-radius: 5px;
  width: 20px;
  height: 20px;
  font-size: 0.65rem;
  cursor: pointer;
}

.nvc-arrows button:disabled {
  opacity: 0.3;
  cursor: default;
}

.nvc-color-sel {
  border: 1px solid var(--mg-border-light);
  border-radius: 6px;
  padding: 0.15rem 0.25rem;
  font-size: 0.65rem;
  font-family: inherit;
  color: #fff;
  flex-shrink: 0;
  width: 74px;
}

.nvc-chips {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.nvc-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.66rem;
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border: 1px solid color-mix(in srgb, var(--mg-success) 28%, var(--mg-border-light));
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
  white-space: nowrap;
}

.nvc-chip-x {
  border: 0;
  background: transparent;
  color: inherit;
  font-size: 0.8rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
</style>
