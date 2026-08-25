<template>
  <div class="cal-shell">
    <!-- هدر: ناوبری ماه + تقویم بر اساس -->
    <div class="cal-header">
      <div class="cal-nav">
        <button type="button" class="cal-nav-btn" title="ماه قبل" @click="shiftMonth(-1)"><ChevronRight :size="16" /></button>
        <strong class="cal-month-label">{{ monthLabel }}</strong>
        <button type="button" class="cal-nav-btn" title="ماه بعد" @click="shiftMonth(1)"><ChevronLeft :size="16" /></button>
        <button type="button" class="cal-today-btn" @click="goToday">امروز</button>
      </div>

      <div class="cal-based-on">
        <span class="cal-based-label">تقویم بر اساس</span>
        <SearchableDropdown
          :model-value="dateField"
          :options="dateFieldOptions"
          placeholder="انتخاب فیلد تاریخ..."
          search-placeholder="جستجو..."
          @update:model-value="dateField = $event || 'custom'"
        />
      </div>
    </div>

    <div class="cal-layout">
      <!-- تقویم -->
      <div class="cal-main">
        <div class="cal-grid">
          <div v-for="d in WEEKDAYS" :key="d" class="cal-weekday">{{ d }}</div>
          <div
            v-for="(day, idx) in monthCells"
            :key="idx"
            class="cal-day"
            :class="{
              'cal-day--empty': !day,
              'cal-day--today': day && isToday(day),
              'cal-day--selected': day && isSelected(day),
              'cal-day--drop': day && dropTarget === dayKey(day),
            }"
            @dragover.prevent="day && (dropTarget = dayKey(day))"
            @dragleave="dropTarget = ''"
            @drop.prevent="day && handleDrop($event, day)"
            @click="day && selectDay(day)"
          >
            <template v-if="day">
              <span class="cal-day-num">{{ toPersianDigits(day.jd) }}</span>
              <div class="cal-day-items">
                <span
                  v-for="item in itemsOfDay(day)"
                  :key="item.name"
                  class="cal-day-pill"
                  :title="item.title"
                >{{ item.title }}</span>
                <span v-if="itemsOfDay(day).length > 3" class="cal-day-more">+{{ itemsOfDay(day).length - 3 }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- بدون تاریخ -->
      <aside class="cal-nodate">
        <div class="cal-nodate-head">
          <strong>بدون تاریخ</strong>
          <span class="cal-nodate-count">{{ noDateItems.length }}</span>
        </div>
        <p class="cal-nodate-hint">برای قرار دادن در تقویم، بکشید و روی روز رها کنید</p>
        <div class="cal-nodate-list">
          <div
            v-for="item in noDateItems"
            :key="item.name"
            class="cal-nodate-item"
            @click="openItem(item)"
          >
            <span
              class="cal-nodate-grip"
              draggable="true"
              title="برای درگ بکشید"
              @dragstart="handleDragStart($event, item)"
              @dragend="dropTarget = ''"
              @click.stop
            >⠿</span>
            <div class="cal-nodate-copy">
              <strong>{{ item.title || item.item_code || item.name }}</strong>
              <small v-if="item.category_title">{{ item.category_title }}</small>
            </div>
            <span v-if="isItemActive(item)" class="cal-dot cal-dot--on"></span>
            <span v-else class="cal-dot cal-dot--off"></span>
          </div>
          <p v-if="!noDateItems.length" class="cal-nodate-empty">همه آیتم‌ها تاریخ دارند.</p>
        </div>
      </aside>
    </div>

    <!-- آیتم‌های روز انتخاب‌شده -->
    <div v-if="selectedDay && selectedItems.length" class="cal-day-list">
      <div class="cal-day-list-head">
        <strong>آیتم‌های {{ formatDayLabel(selectedDay) }}</strong>
        <span class="cal-day-list-count">{{ selectedItems.length }} کالا</span>
      </div>
      <div class="cal-day-list-rows">
        <div
          v-for="item in selectedItems"
          :key="item.name"
          class="cal-list-row"
          @click="openItem(item)"
        >
          <span class="cal-list-grip">⠿</span>
          <div class="cal-list-body">
            <strong class="cal-list-title">{{ item.title || item.item_code || item.name }}</strong>
            <div class="cal-list-chips" v-if="hasChips(item)">
              <template v-for="pkey in orderedProps" :key="pkey">
                <span
                  v-if="isPropVisible(pkey) && chipRenderers?.[pkey]"
                  class="ng-chip"
                  :class="chipClassFor(item, pkey)"
                >{{ chipTextFor(item, pkey) }}</span>
              </template>
            </div>
          </div>
          <button type="button" class="cal-list-remove" title="حذف از این روز" @click.stop="removeFromDay(item)">
            <X :size="13" />
          </button>
        </div>
      </div>
    </div>
    <div v-else-if="selectedDay" class="cal-day-list cal-day-list--empty">
      <p>در این روز آیتمی نیست. از بخش «بدون تاریخ» بکشید و اینجا بندازید.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { ChevronLeft, ChevronRight, X } from "lucide-vue-next";
import SearchableDropdown from "@/components/SearchableDropdown.vue";
import {
  formatJalaliDisplay,
  gregorianToJalali,
  jalaliToGregorian,
  getJalaliDaysInMonth,
  toPersianDigits,
} from "@/utils/jalali";

const props = defineProps({
  rows: { type: Array, default: () => [] },
  chipRenderers: { type: Object, default: null },
  properties: { type: Object, default: null },
  propertyOrder: { type: Array, default: null },
  rowClass: { type: [String, Function], default: "" },
});

const emit = defineEmits(["open-item", "assign-date", "clear-date"]);

const WEEKDAYS = ["ش", "ی", "د", "س", "چ", "پ", "ج"];

const STORAGE_KEY = "mg-calendar-dates-v1";

// ── state ──────────────────────────────────────────────────────────────────
const dateField = ref("custom");
const nowJ = gregorianToJalali(new Date().getFullYear(), new Date().getMonth() + 1, new Date().getDate());
const viewYear = ref(nowJ.year);
const viewMonth = ref(nowJ.month);
const selectedDayKey = ref("");

const selectedDay = computed(() => {
  if (!selectedDayKey.value) return null;
  const [y, m, d] = selectedDayKey.value.split("-").map(Number);
  return { year: y, month: m, jd: d };
});
const dropTarget = ref("");
const assignedDates = ref(loadAssigned());

function loadAssigned() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch (_) {
    return {};
  }
}

function persistAssigned() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(assignedDates.value));
  } catch (_) {
    /* ignore */
  }
}

watch(assignedDates, persistAssigned, { deep: true });

const dateFieldOptions = [
  { value: "custom", label: "تاریخ اختصاصی (درگ‌انددراپ)" },
  { value: "creation", label: "تاریخ ایجاد" },
  { value: "modified", label: "تاریخ ویرایش" },
];

// ── helper: تاریخ هر آیتم ──────────────────────────────────────────────────
// همه تاریخ‌ها به «کلید شمسی» (مثل 1405-05-19) تبدیل می‌شوند تا با روزهای
// شبکه تقویم قابل مقایسه باشند.
function isoToJalaliKey(iso) {
  const [y, m, d] = String(iso || "").split("-").map(Number);
  if (!y || !m || !d) return "";
  const j = gregorianToJalali(y, m, d);
  return `${j.year}-${String(j.month).padStart(2, "0")}-${String(j.day).padStart(2, "0")}`;
}

function itemDate(item) {
  if (!item) return "";
  if (dateField.value === "custom") {
    // تاریخ سرور (calendar_date) اولویت دارد؛ localStorage فقط برای داده‌های قدیمی
    const server = item?.calendar_date;
    if (server && typeof server === "string" && /^\d{4}-\d{2}-\d{2}/.test(server)) {
      return isoToJalaliKey(server.slice(0, 10));
    }
    return assignedDates.value?.[item.name] || "";
  }
  const raw = item?.[dateField.value];
  if (raw && typeof raw === "string" && /^\d{4}-\d{2}-\d{2}/.test(raw)) {
    return isoToJalaliKey(raw.slice(0, 10));
  }
  return "";
}

function dayKey(day) {
  return `${day.year}-${String(day.month).padStart(2, "0")}-${String(day.jd).padStart(2, "0")}`;
}

function parseDayKey(key) {
  const [y, m, d] = key.split("-").map(Number);
  return { year: y, month: m, jd: d };
}

// ── آیتم‌ها ────────────────────────────────────────────────────────────────
const datedItems = computed(() =>
  (props.rows || []).map((r) => ({ ...r, _cal_date: itemDate(r) })).filter((r) => r._cal_date),
);

const noDateItems = computed(() =>
  (props.rows || []).map((r) => ({ ...r, _cal_date: itemDate(r) })).filter((r) => !r._cal_date),
);

function itemsOfDay(day) {
  const key = dayKey(day);
  return datedItems.value.filter((r) => r._cal_date === key);
}

function isItemActive(item) {
  return Number(item?.is_active) === 1 || item?.is_active === true;
}

// ── تقویم ──────────────────────────────────────────────────────────────────
const monthLabel = computed(() => {
  const names = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
  return `${names[viewMonth.value - 1]} ${toPersianDigits(viewYear.value)}`;
});

const monthCells = computed(() => {
  const daysInMonth = getJalaliDaysInMonth(viewYear.value, viewMonth.value);
  const firstGreg = jalaliToGregorian(viewYear.value, viewMonth.value, 1);
  const firstDate = new Date(firstGreg.year, firstGreg.month - 1, firstGreg.day);
  // هفته از شنبه شروع می‌شود: شنبه=0
  const leading = (firstDate.getDay() + 1) % 7;
  const cells = [];
  for (let i = 0; i < leading; i += 1) cells.push(null);
  for (let d = 1; d <= daysInMonth; d += 1) {
    cells.push({ year: viewYear.value, month: viewMonth.value, jd: d });
  }
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
});

function isToday(day) {
  return day.year === nowJ.year && day.month === nowJ.month && day.jd === nowJ.day;
}

function isSelected(day) {
  return selectedDayKey.value === dayKey(day);
}

function shiftMonth(delta) {
  let m = viewMonth.value + delta;
  let y = viewYear.value;
  if (m < 1) {
    m = 12;
    y -= 1;
  } else if (m > 12) {
    m = 1;
    y += 1;
  }
  viewMonth.value = m;
  viewYear.value = y;
}

function goToday() {
  viewYear.value = nowJ.year;
  viewMonth.value = nowJ.month;
  selectedDayKey.value = dayKey(nowJ);
}

function selectDay(day) {
  const key = dayKey(day);
  selectedDayKey.value = selectedDayKey.value === key ? "" : key;
}

function formatDayLabel(day) {
  const names = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
  return `${toPersianDigits(day.jd)} ${names[day.month - 1]} ${toPersianDigits(day.year)}`;
}

// ── درگ‌انددراپ ────────────────────────────────────────────────────────────
function handleDragStart(event, item) {
  event.dataTransfer?.setData("text/plain", String(item.name || ""));
  event.dataTransfer.effectAllowed = "move";
}

function handleDrop(event, day) {
  const itemName = (() => {
    try {
      return event?.dataTransfer?.getData("text/plain") || "";
    } catch (_) {
      return "";
    }
  })();
  dropTarget.value = "";
  if (!itemName) return;
  const key = dayKey(day);
  const next = { ...assignedDates.value, [itemName]: key };
  assignedDates.value = next;
  emit("assign-date", { name: itemName, date: key });
}

// ── لیست روز انتخاب‌شده ────────────────────────────────────────────────────
const selectedItems = computed(() => {
  if (!selectedDayKey.value) return [];
  return datedItems.value.filter((r) => r._cal_date === selectedDayKey.value);
});

const orderedProps = computed(() => {
  const order = props.propertyOrder || [];
  return order.length ? order : ["category_title", "base_price", "stock_qty", "is_active", "tags", "item_code"];
});

function isPropVisible(key) {
  return props.properties?.[key] !== false;
}

function chipTextFor(row, key) {
  try {
    return props.chipRenderers?.[key]?.(row)?.text ?? "";
  } catch (_) {
    return "";
  }
}

function chipClassFor(row, key) {
  try {
    return props.chipRenderers?.[key]?.(row)?.cls ?? "";
  } catch (_) {
    return "";
  }
}

function hasChips(row) {
  for (const key of orderedProps.value) {
    if (isPropVisible(key) && chipTextFor(row, key)) return true;
  }
  return false;
}

function removeFromDay(item) {
  const next = { ...assignedDates.value };
  delete next[item.name];
  assignedDates.value = next;
  emit("clear-date", { name: item.name });
}

function openItem(item) {
  emit("open-item", item);
}

// وقتی dateField عوض شد، انتخاب روز را پاک کن
watch(dateField, () => {
  selectedDayKey.value = "";
});
</script>

<style scoped>
.cal-shell {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

/* هدر */
.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  flex-wrap: wrap;
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: var(--mg-bg-surface);
}

.cal-nav {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.cal-nav-btn {
  width: 28px;
  height: 28px;
  border: 1px solid var(--mg-border-light);
  border-radius: 8px;
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.12s ease;
}

.cal-nav-btn:hover {
  border-color: var(--mg-primary);
  color: var(--mg-primary);
}

.cal-month-label {
  font-size: 0.86rem;
  color: var(--mg-text-main);
  min-width: 130px;
  text-align: center;
}

.cal-today-btn {
  border: 1px solid color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
  border-radius: 8px;
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
  color: var(--mg-primary);
  font-family: inherit;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  cursor: pointer;
}

.cal-today-btn:hover {
  background: color-mix(in srgb, var(--mg-primary) 14%, var(--mg-bg-surface));
}

.cal-based-on {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.cal-based-label {
  font-size: 0.74rem;
  font-weight: 700;
  color: var(--mg-text-main);
  white-space: nowrap;
}

.cal-based-on .searchable-dropdown {
  width: 220px;
}

/* چیدمان: تقویم + بدون تاریخ */
.cal-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 240px;
  gap: 0.7rem;
  align-items: start;
}

/* گرید تقویم */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  padding: 0.4rem;
  background: var(--mg-bg-surface);
}

.cal-weekday {
  text-align: center;
  font-size: 0.66rem;
  font-weight: 700;
  color: var(--mg-text-muted);
  padding: 0.25rem 0;
}

.cal-day {
  min-height: 78px;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  cursor: pointer;
  transition: all 0.12s ease;
  background: color-mix(in srgb, var(--mg-bg-page) 55%, var(--mg-bg-surface));
}

.cal-day:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
}

.cal-day--empty {
  background: transparent;
  cursor: default;
}

.cal-day--today {
  border-color: color-mix(in srgb, var(--mg-primary) 45%, var(--mg-border-light));
}

.cal-day--selected {
  border-color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
}

.cal-day--drop {
  border-color: var(--mg-success);
  background: var(--mg-success-bg);
}

.cal-day-num {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--mg-text-main);
}

.cal-day--today .cal-day-num {
  color: var(--mg-primary);
}

.cal-day-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.cal-day-pill {
  font-size: 0.58rem;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-soft) 70%, transparent);
  border-radius: 5px;
  padding: 1px 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cal-day-more {
  font-size: 0.56rem;
  color: var(--mg-primary);
  font-weight: 600;
}

/* بدون تاریخ */
.cal-nodate {
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  padding: 0.5rem;
  background: var(--mg-bg-surface);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  max-height: 480px;
}

.cal-nodate-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.cal-nodate-head strong {
  font-size: 0.8rem;
  color: var(--mg-text-main);
}

.cal-nodate-count {
  font-size: 0.66rem;
  font-weight: 700;
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-radius: 999px;
  padding: 0.1rem 0.45rem;
}

.cal-nodate-hint {
  font-size: 0.64rem;
  color: var(--mg-text-muted);
  margin: 0;
}

.cal-nodate-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  overflow-y: auto;
  flex: 1;
}

.cal-nodate-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.4rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 8px;
  background: var(--mg-bg-page);
  cursor: grab;
  transition: all 0.12s ease;
}

.cal-nodate-item:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
  box-shadow: 0 4px 12px rgb(var(--mg-primary-rgb) / 0.12);
}

.cal-nodate-grip {
  color: var(--mg-border);
  font-size: 0.8rem;
  opacity: 0.6;
  cursor: grab;
  padding: 0.2rem 0.15rem;
  border-radius: 6px;
  user-select: none;
  -webkit-user-drag: element;
  transition: all 0.12s ease;
}

.cal-nodate-grip:hover {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
  opacity: 1;
}

.cal-nodate-grip:active {
  cursor: grabbing;
}

.cal-nodate-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.cal-nodate-copy strong {
  font-size: 0.72rem;
  color: var(--mg-text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cal-nodate-copy small {
  font-size: 0.62rem;
  color: var(--mg-text-muted);
}

.cal-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.cal-dot--on {
  background: var(--mg-success);
}

.cal-dot--off {
  background: #d97706;
}

.cal-nodate-empty {
  font-size: 0.68rem;
  color: var(--mg-text-muted);
  text-align: center;
  padding: 0.5rem;
}

/* لیست روز انتخاب‌شده */
.cal-day-list {
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  padding: 0.5rem;
  background: var(--mg-bg-surface);
}

.cal-day-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--mg-border-light);
  margin-bottom: 0.4rem;
}

.cal-day-list-head strong {
  font-size: 0.82rem;
  color: var(--mg-primary);
}

.cal-day-list-count {
  font-size: 0.66rem;
  color: var(--mg-text-muted);
}

.cal-day-list-rows {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.cal-list-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.45rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 8px;
  background: var(--mg-bg-page);
  cursor: pointer;
  transition: all 0.12s ease;
}

.cal-list-row:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
}

.cal-list-grip {
  color: var(--mg-border);
  opacity: 0.6;
}

.cal-list-body {
  flex: 1;
  min-width: 0;
}

.cal-list-title {
  font-size: 0.76rem;
  color: var(--mg-text-main);
  display: block;
}

.cal-list-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.15rem;
}

.cal-list-remove {
  border: 0;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
  display: inline-flex;
  padding: 0.15rem;
  border-radius: 6px;
  flex-shrink: 0;
}

.cal-list-remove:hover {
  color: var(--mg-danger);
  background: var(--mg-danger-bg);
}

.cal-day-list--empty {
  text-align: center;
  color: var(--mg-text-muted);
  font-size: 0.74rem;
  padding: 0.8rem;
}

/* چیپ‌ها (مثل لیست) */
.ng-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.62rem;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-soft) 65%, transparent);
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 70%, transparent);
  border-radius: 999px;
  padding: 0.06rem 0.4rem;
  white-space: nowrap;
}

.ng-chip--soft,
.ng-chip--on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 25%, transparent);
  font-weight: 600;
}

.ng-chip--off {
  color: #92400e;
  background: rgb(254 243 199 / 0.95);
}

.ng-chip--tag {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
}

/* ریسپانسیو */
@media (max-width: 860px) {
  .cal-layout {
    grid-template-columns: 1fr;
  }

  .cal-nodate {
    max-height: 260px;
  }
}

@media (max-width: 520px) {
  .cal-day {
    min-height: 56px;
    padding: 0.15rem;
  }

  .cal-day-pill {
    font-size: 0.52rem;
    padding: 1px 3px;
  }

  .cal-header {
    flex-direction: column;
    align-items: stretch;
  }

  .cal-based-on {
    width: 100%;
  }

  .cal-based-on .searchable-dropdown {
    flex: 1;
    width: auto;
  }

  .cal-month-label {
    min-width: 100px;
    font-size: 0.78rem;
  }
}
</style>
