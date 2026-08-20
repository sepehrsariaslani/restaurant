<template>
  <div ref="shellRef" class="gs-shell">
    <!-- تولبار -->
    <div class="gs-toolbar">
      <button type="button" class="gs-add-row" @click="addRow"><Plus :size="13" /> افزودن ردیف</button>
      <span class="gs-hint">برای ویرایش روی سلول کلیک کنید</span>

      <span class="gs-toolbar-grow"></span>

      <SearchableDropdown
        class="gs-cols-dropdown"
        :model-value="visibleColumnKeys"
        :options="allColumnOptions"
        placeholder="ستون‌ها"
        search-placeholder="جستجوی ستون..."
        multiple
        fixed-panel
        @update:model-value="onColumnsToggle"
      />

      <span v-if="hiddenCols.size" class="gs-hidden-count">
        <EyeOff :size="11" /> {{ hiddenCols.size }} ستون مخفی
      </span>

      <button type="button" class="gs-icon-btn" title="خروجی اکسل همه ردیف‌های فیلترشده" @click="exportExcel('filtered')">
        <FileSpreadsheet :size="13" />
      </button>

      <button type="button" class="gs-icon-btn" title="خروجی CSV همه ردیف‌های فیلترشده" @click="exportCsv('filtered')">
        <Download :size="13" />
      </button>

      <button type="button" class="gs-icon-btn" title="بازنشانی جدول (فیلتر، مرتب‌سازی، فریز و ستون‌های مخفی)" @click="resetSheet">
        <RotateCcw :size="13" />
      </button>
    </div>

    <!-- نوار عملیات گروهی — وقتی ردیف‌هایی انتخاب شده باشند -->
    <div v-if="selectedRows.length" class="gs-bulk-bar">
      <span class="gs-bulk-count"><CheckSquare :size="13" /> {{ selectedRows.length }} ردیف انتخاب شده</span>
      <button type="button" class="gs-bulk-btn gs-bulk-btn--edit" @click="openBulkEdit"><PenLine :size="12" /> ویرایش گروهی</button>
      <button type="button" class="gs-bulk-btn" @click="exportExcel('selected')"><FileSpreadsheet :size="12" /> خروجی اکسل</button>
      <button type="button" class="gs-bulk-btn" @click="exportCsv('selected')"><Download :size="12" /> خروجی CSV</button>
      <button type="button" class="gs-bulk-btn gs-bulk-btn--ghost" @click="clearSelection"><X :size="12" /> انصراف</button>
    </div>

    <!-- جدول -->
    <div class="gs-scroll" :style="{ maxHeight: maxScrollHeight }">
      <table class="gs-table">
        <thead>
          <tr class="gs-head-labels">
            <th
              class="gs-rowhead gs-select-head"
              data-col-key="__select"
              :style="frozenStyle('__select')"
              title="انتخاب همه ردیف‌ها"
            >
              <input
                ref="selectAllRef"
                type="checkbox"
                class="gs-check"
                :checked="allFilteredSelected"
                @click="toggleSelectAll"
              />
            </th>
            <th class="gs-rowhead gs-head-rowhead" :style="frozenStyle('#')">#</th>
            <th
              class="gs-rowhead gs-actions-head"
              data-col-key="__open"
              :style="frozenStyle('__open')"
              title="باز کردن صفحه جزئیات"
            >
              <ExternalLink :size="11" />
            </th>
            <th
              v-for="col in visibleColumns"
              :key="col.key"
              class="gs-th"
              :class="{ 'gs-th--narrow': col.type === 'boolean', 'gs-frozen': isFrozen(col.key) }"
              :data-col-key="col.key"
              :style="frozenStyle(col.key)"
            >
              <div class="gs-th-inner" @click="handleSort(col)">
                <span class="gs-th-label">{{ col.label }}</span>
                <span v-if="sortCol === col.key" class="gs-sort-ind">
                  <ArrowUp v-if="sortDir === 'asc'" :size="11" />
                  <ArrowDown v-else :size="11" />
                </span>
                <span v-else class="gs-sort-ind gs-sort-ind--idle"><ArrowUpDown :size="10" /></span>
                <span v-if="isFrozen(col.key)" class="gs-pin-ind" title="فریز شده"><Pin :size="10" /></span>
                <button
                  type="button"
                  class="gs-col-menu-btn"
                  title="گزینه‌های ستون"
                  @click.stop="openColMenu($event, col)"
                >
                  <MoreHorizontal :size="13" />
                </button>
              </div>
              <!-- فیلتر زیر هدر -->
              <div class="gs-filter-row" @click.stop>
                <SearchableDropdown
                  v-if="col.type === 'select' || col.type === 'tags'"
                  :model-value="filterArrayValue(col.key)"
                  :options="optionsFor(col.key)"
                  :placeholder="col.type === 'tags' ? 'تگ‌ها...' : 'فیلتر...'"
                  search-placeholder="جستجو..."
                  clearable
                  multiple
                  fixed-panel
                  @update:model-value="onFilterChange(col, $event)"
                />
                <select v-else-if="col.type === 'boolean'" v-model="filters[col.key]" class="gs-filter-input" @change="applyFilters">
                  <option value="">همه</option>
                  <option value="1">بله</option>
                  <option value="0">خیر</option>
                </select>
                <input
                  v-else
                  v-model="filters[col.key]"
                  class="gs-filter-input"
                  :placeholder="'فیلتر...'"
                  @input="applyFilters"
                />
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, rIdx) in filteredRows"
            :key="rowKey(row)"
            class="gs-tr"
            :class="{ 'gs-tr--active': activeRow === rIdx }"
          >
            <td class="gs-rowhead gs-select-cell gs-frozen" :style="frozenStyle('__select')">
              <input
                type="checkbox"
                class="gs-check"
                :checked="selectedKeys.has(rowKey(row))"
                @click.stop="toggleRowSelect(row)"
              />
            </td>
            <td class="gs-rowhead gs-frozen" :style="frozenStyle('#')" @click="activeRow = rIdx">{{ rIdx + 1 }}</td>
            <td class="gs-rowhead gs-actions-cell gs-frozen" :style="frozenStyle('__open')">
              <button
                type="button"
                class="gs-open-btn"
                :title="`باز کردن صفحه جزئیات «${row.title || row.item_code || ''}»`"
                @click.stop="openRow(row)"
              >
                <ExternalLink :size="13" />
              </button>
            </td>
            <td
              v-for="col in visibleColumns"
              :key="col.key"
              class="gs-td"
              :class="{
                'gs-td--active': activeRow === rIdx && activeCol === col.key,
                'gs-td--edited': editedCells.has(`${rowKey(row)}:${col.key}`),
                'gs-frozen': isFrozen(col.key),
              }"
              :style="frozenStyle(col.key)"
              @click="startEdit(rIdx, col)"
            >
              <!-- حالت ویرایش -->
              <template v-if="editing === `${rowKey(row)}:${col.key}`">
                <SearchableDropdown
                  v-if="col.type === 'select' || col.type === 'tags'"
                  :model-value="row[col.key]"
                  :options="optionsFor(col.key)"
                  placeholder="..."
                  search-placeholder="جستجو..."
                  clearable
                  include-empty-option
                  empty-label="—"
                  :multiple="col.type === 'tags' && col.multi"
                  fixed-panel
                  @update:model-value="commitEdit(row, col, $event)"
                />
                <div v-else-if="col.type === 'boolean'" class="gs-bool">
                  <button
                    type="button"
                    class="gs-bool-btn"
                    :class="{ on: truthy(row[col.key]) }"
                    @click="commitEdit(row, col, !truthy(row[col.key]) ? 1 : 0)"
                  >{{ truthy(row[col.key]) ? 'بله' : 'خیر' }}</button>
                </div>
                <PersianNumberInput
                  v-else-if="col.type === 'number'"
                  ref="cellInputRef"
                  :model-value="draftValue"
                  input-class="gs-input gs-input--num"
                  @update:model-value="draftValue = $event"
                  @blur="commitEdit(row, col, draftValue)"
                  @enter="commitEdit(row, col, draftValue)"
                  @esc="cancelEdit"
                />
                <input
                  v-else
                  ref="cellInputRef"
                  class="gs-input"
                  type="text"
                  :value="row[col.key]"
                  @input="draftValue = $event.target.value"
                  @blur="commitEdit(row, col, draftValue)"
                  @keydown.enter.prevent="commitEdit(row, col, draftValue)"
                  @keydown.esc="cancelEdit"
                />
              </template>

              <!-- حالت نمایش -->
              <template v-else>
                <span v-if="col.type === 'boolean'" :class="['gs-pill', truthy(row[col.key]) ? 'gs-pill--on' : 'gs-pill--off']">
                  {{ truthy(row[col.key]) ? 'بله' : 'خیر' }}
                </span>
                <span v-else-if="col.type === 'select'" class="gs-select-pill">{{ row[col.key] || '—' }}</span>
                <span v-else-if="col.type === 'tags'">{{ formatTags(row[col.key]) || '—' }}</span>
                <span v-else class="gs-cell-text">{{ formatCell(row, col) }}</span>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- افزودن ردیف پایین جدول -->
    <div class="gs-bottom-add">
      <button type="button" class="gs-add-row" @click="addRow"><Plus :size="13" /> افزودن ردیف</button>
    </div>

    <!-- مودال ویرایش گروهی -->
    <ManagementPopup
      v-model:open="bulkEditOpen"
      title="ویرایش گروهی ردیف‌ها"
      :subtitle="`${selectedRows.length} ردیف انتخاب شده — فیلد و مقدار جدید را انتخاب کنید`"
      size="sm"
    >
      <div class="gs-bulk-edit-form">
        <div class="gs-be-quick">
          <span class="gs-be-label">عملیات سریع</span>
          <div class="gs-be-quick-grid">
            <button type="button" class="gs-be-quick-btn gs-be-quick-btn--on" @click="runBulkFromModal('activate')">
              <Check :size="13" /> فعال‌سازی
            </button>
            <button type="button" class="gs-be-quick-btn gs-be-quick-btn--off" @click="runBulkFromModal('deactivate')">
              <Ban :size="13" /> غیرفعال‌سازی
            </button>
            <button type="button" class="gs-be-quick-btn" @click="runBulkFromModal('mark_out_of_stock')">
              <PackageX :size="13" /> ناموجود
            </button>
            <button type="button" class="gs-be-quick-btn" @click="runBulkFromModal('mark_in_stock')">
              <PackageCheck :size="13" /> موجود
            </button>
          </div>
        </div>

        <div class="gs-be-divider"></div>

        <label class="gs-be-field">
          <span class="gs-be-label">فیلد موردنظر</span>
          <SearchableDropdown
            :model-value="bulkEditField"
            :options="bulkEditFieldOptions"
            placeholder="انتخاب فیلد..."
            search-placeholder="جستجو..."
            fixed-panel
            @update:model-value="onBulkFieldChange"
          />
        </label>

        <label class="gs-be-field">
          <span class="gs-be-label">مقدار جدید</span>
          <SearchableDropdown
            v-if="bulkEditValueOptions"
            :model-value="bulkEditValue"
            :options="bulkEditValueOptions"
            placeholder="انتخاب مقدار..."
            search-placeholder="جستجو..."
            fixed-panel
            @update:model-value="bulkEditValue = $event"
          />
          <PersianNumberInput
            v-else
            :model-value="bulkEditValue"
            input-class="gs-be-input"
            placeholder="مثلاً 150000"
            @update:model-value="bulkEditValue = $event"
          />
        </label>

        <p class="gs-be-hint">
          این تغییر روی {{ selectedRows.length }} ردیف انتخاب‌شده اعمال و روی سرور ذخیره می‌شود.
        </p>
      </div>
      <template #footer>
        <div class="gs-be-actions">
          <button type="button" class="secondary-btn" @click="bulkEditOpen = false">انصراف</button>
          <button
            type="button"
            class="primary-btn"
            :disabled="!bulkEditCanApply"
            @click="applyBulkEdit"
          >
            اعمال روی {{ selectedRows.length }} ردیف
          </button>
        </div>
      </template>
    </ManagementPopup>

    <!-- منوی گزینه‌های ستون -->
    <Teleport to="body">
      <div
        v-if="colMenu"
        ref="colMenuRef"
        class="gs-col-menu"
        :style="colMenuStyle"
        @mousedown.stop
      >
        <div class="gs-col-menu-title">{{ colMenu.label }}</div>
        <button
          type="button"
          class="gs-menu-item"
          :class="{ active: sortCol === colMenu.key && sortDir === 'asc' }"
          @click="menuAction('sort-asc')"
        >
          <ArrowUp :size="12" /> مرتب‌سازی صعودی
        </button>
        <button
          type="button"
          class="gs-menu-item"
          :class="{ active: sortCol === colMenu.key && sortDir === 'desc' }"
          @click="menuAction('sort-desc')"
        >
          <ArrowDown :size="12" /> مرتب‌سازی نزولی
        </button>
        <button v-if="sortCol === colMenu.key" type="button" class="gs-menu-item" @click="menuAction('sort-clear')">
          <X :size="12" /> حذف مرتب‌سازی
        </button>
        <div class="gs-menu-sep"></div>
        <button
          type="button"
          class="gs-menu-item"
          :class="{ active: isFrozen(colMenu.key) }"
          @click="menuAction('freeze')"
        >
          <Pin v-if="!isFrozen(colMenu.key)" :size="12" />
          <PinOff v-else :size="12" />
          {{ isFrozen(colMenu.key) ? 'لغو فریز ستون' : 'فریز کردن ستون' }}
        </button>
        <button type="button" class="gs-menu-item" @click="menuAction('hide')">
          <EyeOff :size="12" /> مخفی کردن ستون
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch, watchEffect } from "vue";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Ban,
  Check,
  CheckSquare,
  Download,
  ExternalLink,
  EyeOff,
  FileSpreadsheet,
  MoreHorizontal,
  PackageCheck,
  PackageX,
  PenLine,
  Pin,
  PinOff,
  Plus,
  RotateCcw,
  X,
} from "lucide-vue-next";
import SearchableDropdown from "@/components/SearchableDropdown.vue";
import ManagementPopup from "@/components/management/ManagementPopup.vue";
import PersianNumberInput from "@/components/PersianNumberInput.vue";

const STORAGE_FROZEN = "mg-sheet-frozen-cols-v1";
const STORAGE_HIDDEN = "mg-sheet-hidden-cols-v1";

const props = defineProps({
  rows: { type: Array, default: () => [] },
  columns: { type: Array, default: () => [] },
  selectOptions: { type: Object, default: () => ({}) },
  rowKey: { type: [String, Function], default: "name" },
  cellFormatters: { type: Object, default: null },
  frozenColumns: { type: Array, default: () => ["item_code", "title"] },
});

const emit = defineEmits(["cell-change", "add-row", "row-open", "bulk-action", "export-excel", "bulk-edit"]);

const editing = ref("");
const draftValue = ref("");
const activeRow = ref(-1);
const activeCol = ref("");
const editedCells = ref(new Set());
const cellInputRef = ref(null);
const filters = ref({});
const sortCol = ref("");
const sortDir = ref("asc");

const shellRef = ref(null);
const maxScrollHeight = ref("");
const frozenLefts = ref({});

// ── ذخیره‌سازی محلی ─────────────────────────────────────────────────────────
function readStored(key) {
  try {
    const raw = window.localStorage.getItem(key);
    if (raw === null) return null;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : null;
  } catch (_) {
    return null;
  }
}

function writeStored(key, arr) {
  try {
    window.localStorage.setItem(key, JSON.stringify(arr));
  } catch (_) {
    /* ignore */
  }
}

const storedFrozen = readStored(STORAGE_FROZEN);
const frozenCols = ref(new Set(storedFrozen !== null ? storedFrozen : props.frozenColumns || []));
const storedHidden = readStored(STORAGE_HIDDEN);
const hiddenCols = ref(new Set(storedHidden || []));

// ── انتخاب ردیف‌ها ─────────────────────────────────────────────────────────
const selectedKeys = ref(new Set());
const selectAllRef = ref(null);

const selectedRows = computed(() =>
  (props.rows || []).filter((row) => selectedKeys.value.has(rowKey(row))),
);

const allFilteredSelected = computed(
  () => filteredRows.value.length > 0 && filteredRows.value.every((row) => selectedKeys.value.has(rowKey(row))),
);

const someFilteredSelected = computed(() =>
  filteredRows.value.some((row) => selectedKeys.value.has(rowKey(row))),
);

// حالت «چندتایی» چک‌باکس انتخاب همه
watchEffect(() => {
  if (selectAllRef.value) {
    selectAllRef.value.indeterminate = someFilteredSelected.value && !allFilteredSelected.value;
  }
});

// پاک‌سازی کلیدهای منسوخ وقتی لیست ردیف‌ها عوض می‌شود
watch(
  () => props.rows,
  () => {
    const valid = new Set((props.rows || []).map(rowKey));
    const next = new Set([...selectedKeys.value].filter((key) => valid.has(key)));
    if (next.size !== selectedKeys.value.size) selectedKeys.value = next;
  },
);

function toggleRowSelect(row) {
  const next = new Set(selectedKeys.value);
  const key = rowKey(row);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  selectedKeys.value = next;
}

function toggleSelectAll() {
  const next = new Set(selectedKeys.value);
  const keys = filteredRows.value.map(rowKey);
  if (allFilteredSelected.value) {
    keys.forEach((key) => next.delete(key));
  } else {
    keys.forEach((key) => next.add(key));
  }
  selectedKeys.value = next;
}

function clearSelection() {
  selectedKeys.value = new Set();
}

function runBulk(action) {
  const rows = selectedRows.value;
  if (!rows.length) return;
  emit("bulk-action", { rows, action });
}

function runBulkFromModal(action) {
  runBulk(action);
  bulkEditOpen.value = false;
}

// ── ویرایش گروهی ───────────────────────────────────────────────────────────
const bulkEditOpen = ref(false);
const bulkEditField = ref("is_active");
const bulkEditValue = ref("بله");

const bulkEditFieldOptions = [
  { value: "is_active", label: "وضعیت نمایش" },
  { value: "coming_soon", label: "به‌زودی" },
  { value: "out_of_stock", label: "ناموجود" },
  { value: "category_title", label: "دسته" },
  { value: "subcategory_title", label: "زیردسته" },
  { value: "base_price", label: "قیمت پایه" },
];

const bulkEditValueOptions = computed(() => {
  const field = bulkEditField.value;
  if (field === "category_title" || field === "subcategory_title") {
    return optionsFor(field) || [];
  }
  if (field === "base_price") return null;
  return [
    { value: "بله", label: "بله" },
    { value: "خیر", label: "خیر" },
  ];
});

const bulkEditCanApply = computed(() => {
  if (bulkEditField.value === "base_price") {
    return selectedRows.value.length > 0 && String(bulkEditValue.value ?? "").trim() !== "";
  }
  return selectedRows.value.length > 0 && Boolean(bulkEditValue.value);
});

function openBulkEdit() {
  bulkEditField.value = "is_active";
  bulkEditValue.value = "بله";
  bulkEditOpen.value = true;
}

function onBulkFieldChange(field) {
  bulkEditField.value = field || "is_active";
  bulkEditValue.value = field === "base_price" ? "" : "بله";
}

function applyBulkEdit() {
  const rows = selectedRows.value;
  if (!rows.length || !bulkEditCanApply.value) return;
  emit("bulk-edit", {
    rows,
    field: bulkEditField.value,
    value: bulkEditField.value === "base_price" ? Number(bulkEditValue.value || 0) : bulkEditValue.value,
  });
  bulkEditOpen.value = false;
}

// ── خروجی اکسل (ساخت فایل xlsx در سرور) ────────────────────────────────────
function exportExcel(scope = "selected") {
  const rows = scope === "filtered" ? filteredRows.value : selectedRows.value;
  if (!rows.length) return;
  emit("export-excel", { rows });
}

// ── خروجی CSV ──────────────────────────────────────────────────────────────
function csvEscape(value) {
  const s = String(value ?? "");
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

function exportCsv(scope = "selected") {
  const rows = scope === "filtered" ? filteredRows.value : selectedRows.value;
  if (!rows.length) return;
  const cols = visibleColumns.value;
  const lines = [["#", ...cols.map((col) => col.label)].map(csvEscape).join(",")];
  rows.forEach((row, idx) => {
    const values = [idx + 1];
    for (const col of cols) {
      values.push(col.type === "tags" ? formatTags(row[col.key]) : formatCell(row, col));
    }
    lines.push(values.map(csvEscape).join(","));
  });
  const csv = "\uFEFF" + lines.join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  const now = new Date();
  const stamp = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  anchor.href = url;
  anchor.download = `products-export-${stamp}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ── ستون‌ها ─────────────────────────────────────────────────────────────────
const visibleColumns = computed(() =>
  (props.columns || []).filter((col) => !hiddenCols.value.has(col.key)),
);

const visibleColumnKeys = computed(() => visibleColumns.value.map((col) => col.key));

const allColumnOptions = computed(() =>
  (props.columns || []).map((col) => ({ value: col.key, label: col.label })),
);

const colByKey = computed(() => {
  const map = {};
  for (const col of props.columns || []) map[col.key] = col;
  return map;
});

function onColumnsToggle(keys) {
  const next = new Set();
  for (const col of props.columns || []) {
    if (!keys.includes(col.key)) next.add(col.key);
  }
  hiddenCols.value = next;
  writeStored(STORAGE_HIDDEN, Array.from(next));
}

function isFrozen(key) {
  return frozenCols.value.has(key);
}

function toggleFrozen(key) {
  const next = new Set(frozenCols.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  frozenCols.value = next;
  writeStored(STORAGE_FROZEN, Array.from(next));
  nextTick(computeFrozenLefts);
}

// ── افست ستون‌های فریز (اندازه‌گیری واقعی؛ منطقی RTL/LTR) ───────────────────
function computeFrozenLefts() {
  const shell = shellRef.value;
  if (!shell) return;
  const cells = shell.querySelectorAll(".gs-head-labels th");
  const next = { "#": 0 };
  let acc = 0;
  cells.forEach((cell) => {
    const key = cell.getAttribute("data-col-key") || "#";
    const frozen = key === "#" || key === "__open" || key === "__select" || frozenCols.value.has(key);
    if (frozen) {
      next[key] = acc;
      acc += cell.offsetWidth;
    }
  });
  frozenLefts.value = next;
}

function frozenStyle(key) {
  const px = frozenLefts.value[key];
  if (px === undefined) return {};
  return { insetInlineStart: `${px}px` };
}

// ── حداکثر ارتفاع کادر اسکرول: جدول کوتاه = بدون فضای خالی؛
//    جدول بلند = اسکرول داخل کادر و هدر چسبان ────────────────────────────────
function measureScrollHeight() {
  const shell = shellRef.value;
  if (!shell || typeof window === "undefined") return;
  const top = shell.getBoundingClientRect().top;
  const h = Math.max(240, Math.round(window.innerHeight - Math.max(top, 0) - 122));
  maxScrollHeight.value = `${h}px`;
}

let measureRaf = 0;
function scheduleMeasure() {
  if (measureRaf) return;
  measureRaf = requestAnimationFrame(() => {
    measureRaf = 0;
    measureScrollHeight();
  });
}

let shellObserver = null;
onMounted(() => {
  if (typeof ResizeObserver !== "undefined" && shellRef.value) {
    shellObserver = new ResizeObserver(() => scheduleMeasure());
    shellObserver.observe(shellRef.value);
  }
  window.addEventListener("resize", scheduleMeasure);
  window.addEventListener("scroll", scheduleMeasure, { passive: true, capture: true });
  scheduleMeasure();
  nextTick(computeFrozenLefts);
});

onBeforeUnmount(() => {
  shellObserver?.disconnect();
  shellObserver = null;
  window.removeEventListener("resize", scheduleMeasure);
  window.removeEventListener("scroll", scheduleMeasure, { capture: true });
  closeColMenu();
});

watch(
  () => props.columns,
  () => {
    nextTick(computeFrozenLefts);
  },
  { deep: false },
);

watch(frozenCols, () => {
  nextTick(computeFrozenLefts);
});

// ── توابع کمکی ──────────────────────────────────────────────────────────────
function rowKey(row) {
  if (typeof props.rowKey === "function") return props.rowKey(row);
  return row?.[props.rowKey] ?? row?.name ?? JSON.stringify(row);
}

function optionsFor(key) {
  return props.selectOptions?.[key] || [];
}

function truthy(v) {
  return Number(v) === 1 || v === true;
}

function formatTags(v) {
  if (Array.isArray(v)) return v.join("، ");
  return String(v || "");
}

function formatCell(row, col) {
  const fmt = props.cellFormatters?.[col.key];
  if (fmt) return fmt(row);
  const v = row?.[col.key];
  if (v === null || v === undefined || v === "") return "—";
  return String(v);
}

function normalizeSelectValue(v) {
  const s = String(v ?? "").trim();
  if (s === "1" || s.toLowerCase() === "true") return "بله";
  if (s === "0" || s.toLowerCase() === "false") return "خیر";
  return s;
}

function rowTags(v) {
  if (Array.isArray(v)) return v.map((t) => String(t ?? "").trim()).filter(Boolean);
  return String(v ?? "")
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
}

// ── مرتب‌سازی (سه‌حالته) ────────────────────────────────────────────────────
function handleSort(col) {
  if (sortCol.value === col.key) {
    if (sortDir.value === "asc") {
      sortDir.value = "desc";
    } else {
      sortCol.value = "";
      sortDir.value = "asc";
    }
  } else {
    sortCol.value = col.key;
    sortDir.value = "asc";
  }
}

// ── فیلتر ───────────────────────────────────────────────────────────────────
function onFilterChange(col, value) {
  if (col.type === "select" || col.type === "tags") {
    filters.value[col.key] = Array.isArray(value) ? value : value === "" || value == null ? [] : [value];
  } else {
    filters.value[col.key] = value;
  }
  applyFilters();
}

function filterArrayValue(key) {
  const v = filters.value[key];
  if (Array.isArray(v)) return v;
  if (v === "" || v === null || v === undefined) return [];
  return [v];
}

function applyFilters() {
  // reactive است؛ computed خودش آپدیت می‌شود
}

const filteredRows = computed(() => {
  let rows = [...props.rows];

  for (const [key, value] of Object.entries(filters.value)) {
    const col = colByKey.value[key];
    if (!col) continue;

    if (col.type === "select") {
      const selected = filterArrayValue(key)
        .map((v) => String(v ?? ""))
        .filter(Boolean);
      if (!selected.length) continue;
      rows = rows.filter((row) => selected.includes(normalizeSelectValue(row[key])));
      continue;
    }

    if (col.type === "tags") {
      const selected = filterArrayValue(key)
        .map((v) => String(v ?? ""))
        .filter(Boolean);
      if (!selected.length) continue;
      rows = rows.filter((row) => {
        const tags = rowTags(row[key]);
        return selected.some((s) => tags.includes(s));
      });
      continue;
    }

    if (col.type === "boolean") {
      const q = String(value ?? "").trim();
      if (!q) continue;
      rows = rows.filter((row) => String(Number(row[key]) === 1 ? "1" : "0") === q);
      continue;
    }

    const q = String(value ?? "").trim().toLowerCase();
    if (!q) continue;
    rows = rows.filter((row) => String(row?.[key] ?? "").toLowerCase().includes(q));
  }

  if (sortCol.value) {
    const key = sortCol.value;
    const dir = sortDir.value === "asc" ? 1 : -1;
    rows.sort((a, b) => {
      const va = a?.[key];
      const vb = b?.[key];
      const na = Number(va);
      const nb = Number(vb);
      if (
        Number.isFinite(na) &&
        Number.isFinite(nb) &&
        String(va ?? "").trim() !== "" &&
        String(vb ?? "").trim() !== ""
      ) {
        return (na - nb) * dir;
      }
      return String(va ?? "").localeCompare(String(vb ?? ""), "fa") * dir;
    });
  }

  return rows;
});

// ── منوی گزینه‌های ستون ─────────────────────────────────────────────────────
const colMenu = ref(null);
const colMenuStyle = ref({});
const colMenuRef = ref(null);

function openColMenu(event, col) {
  const rect = event.currentTarget.getBoundingClientRect();
  const dir = typeof getComputedStyle !== "undefined"
    ? getComputedStyle(document.body).direction || "rtl"
    : "rtl";
  const menuWidth = 200;
  const menuHeight = 250;
  const spaceBelow = window.innerHeight - rect.bottom;
  const openUp = spaceBelow < menuHeight && rect.top > spaceBelow;

  let start = dir === "rtl" ? window.innerWidth - rect.right : rect.left;
  start = Math.max(8, Math.min(start, window.innerWidth - menuWidth - 8));

  colMenuStyle.value = {
    position: "fixed",
    top: openUp ? `${Math.max(8, rect.top - menuHeight)}px` : `${rect.bottom + 4}px`,
    insetInlineStart: `${start}px`,
    width: `${menuWidth}px`,
    zIndex: 14000,
  };
  colMenu.value = col;
  document.addEventListener("mousedown", onDocMouseDown);
  document.addEventListener("keydown", onDocKeyDown);
  window.addEventListener("scroll", closeColMenu, { capture: true });
}

function onDocMouseDown(event) {
  if (!colMenuRef.value?.contains(event.target)) closeColMenu();
}

function onDocKeyDown(event) {
  if (event.key === "Escape") closeColMenu();
}

function closeColMenu() {
  if (!colMenu.value) return;
  colMenu.value = null;
  document.removeEventListener("mousedown", onDocMouseDown);
  document.removeEventListener("keydown", onDocKeyDown);
  window.removeEventListener("scroll", closeColMenu, { capture: true });
}

function menuAction(action) {
  const col = colMenu.value;
  if (!col) return;
  if (action === "sort-asc") {
    sortCol.value = col.key;
    sortDir.value = "asc";
  } else if (action === "sort-desc") {
    sortCol.value = col.key;
    sortDir.value = "desc";
  } else if (action === "sort-clear") {
    if (sortCol.value === col.key) {
      sortCol.value = "";
      sortDir.value = "asc";
    }
  } else if (action === "freeze") {
    toggleFrozen(col.key);
  } else if (action === "hide") {
    const next = new Set(hiddenCols.value);
    next.add(col.key);
    hiddenCols.value = next;
    writeStored(STORAGE_HIDDEN, Array.from(next));
  }
  closeColMenu();
}

function resetSheet() {
  filters.value = {};
  sortCol.value = "";
  sortDir.value = "asc";
  frozenCols.value = new Set(props.frozenColumns || []);
  hiddenCols.value = new Set();
  selectedKeys.value = new Set();
  writeStored(STORAGE_FROZEN, Array.from(frozenCols.value));
  writeStored(STORAGE_HIDDEN, []);
  nextTick(computeFrozenLefts);
}

// ── ویرایش ──────────────────────────────────────────────────────────────────
function startEdit(rIdx, col) {
  activeRow.value = rIdx;
  activeCol.value = col.key;
  if (col.type === "boolean") return;
  const row = filteredRows.value[rIdx];
  if (!row) return;
  editing.value = `${rowKey(row)}:${col.key}`;
  draftValue.value = row[col.key] ?? "";
  nextTick(() => {
    const ref = cellInputRef.value;
    const el = ref?.$el?.querySelector?.("input") || ref;
    if (el && typeof el.focus === "function") {
      el.focus();
      el.select?.();
    }
  });
}

function commitEdit(row, col, value) {
  if (!row) return;
  const key = `${rowKey(row)}:${col.key}`;
  // جلوگیری از کامیت دوباره: بعد از Enter/Esc اینپوت حذف می‌شود و blur
  // دوباره صدا زده می‌شود — اگر قبلاً کامیت شده، نادیده بگیر (مقدار خالی ننویس)
  if (editing.value !== key) return;
  const prev = row[col.key];
  if (String(prev ?? "") !== String(value ?? "")) {
    emit("cell-change", { row, column: col.key, value, prev });
    editedCells.value.add(key);
  }
  editing.value = "";
  draftValue.value = "";
}

function cancelEdit() {
  editing.value = "";
  draftValue.value = "";
}

function addRow() {
  emit("add-row");
}

function openRow(row) {
  emit("row-open", row);
}
</script>

<style scoped>
.gs-shell {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
  min-width: 0;
}

.gs-toolbar {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.3rem 0.4rem;
  flex-wrap: wrap;
}

.gs-toolbar-grow {
  flex: 1;
}

.gs-add-row {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
  border-radius: 8px;
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
  color: var(--mg-primary);
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.3rem 0.6rem;
  cursor: pointer;
  white-space: nowrap;
}

.gs-add-row:hover {
  background: color-mix(in srgb, var(--mg-primary) 14%, var(--mg-bg-surface));
}

.gs-hint {
  font-size: 0.66rem;
  color: var(--mg-text-muted);
  white-space: nowrap;
}

/* افزودن ردیف پایین */
.gs-bottom-add {
  display: flex;
  justify-content: center;
  padding: 0.4rem 0;
}

/* ابزارک ستون‌ها */
.gs-cols-dropdown {
  width: 150px;
}

.gs-cols-dropdown :deep(.select) {
  min-height: 26px;
  max-height: 26px;
  padding: 0.1rem 0.4rem;
  font-size: 0.68rem;
  border-radius: 8px;
  border-color: var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
}

.gs-cols-dropdown :deep(.selected-label) {
  font-size: 0.68rem;
}

.gs-hidden-count {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.64rem;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-text-muted) 8%, var(--mg-bg-surface));
  border: 1px solid var(--mg-border-light);
  border-radius: 999px;
  padding: 0.14rem 0.5rem;
  white-space: nowrap;
}

.gs-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 1px solid var(--mg-border-light);
  border-radius: 8px;
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  cursor: pointer;
}

.gs-icon-btn:hover {
  color: var(--mg-primary);
  border-color: color-mix(in srgb, var(--mg-primary) 35%, var(--mg-border-light));
}

/* اسکرول افقی و عمودی داخل کادر — نه بیرون.
   ارتفاع کادر «حداکثر» است: وقتی جدول کوتاه است کادر دقیقاً به‌اندازه
   محتوا می‌شود (بدون فضای خالی) و وقتی جدول بلندتر از صفحه است،
   داخل همین کادر اسکرول می‌شود تا هدرها بالای کادر بمانند. */
.gs-scroll {
  overflow-x: auto;
  overflow-y: auto;
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  width: 100%;
  max-width: 100%;
}

.gs-table {
  width: max-content;
  min-width: 100%;
  max-width: none;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 0.74rem;
  table-layout: auto;
}

/* عرض ثابت ستون‌ها تا جدول کش نیاید */
.gs-th,
.gs-td {
  width: 130px;
}

.gs-th--narrow,
.gs-td.gs-th--narrow {
  width: 80px;
}

/* هدر: همیشه بالای کادر می‌ماند */
.gs-th {
  text-align: right;
  padding: 0;
  font-size: 0.68rem;
  font-weight: 700;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-soft) 55%, var(--mg-bg-surface));
  border-bottom: 1px solid var(--mg-border-light);
  border-inline-end: 1px solid var(--mg-border-light);
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 6;
  min-width: 120px;
}

.gs-th--narrow {
  min-width: 80px;
}

.gs-th.gs-frozen {
  z-index: 7;
}

.gs-th-inner {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.3rem;
  padding: 0.4rem 0.5rem 0.2rem;
  min-height: 26px;
  cursor: pointer;
}

.gs-th-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.gs-sort-ind {
  color: var(--mg-primary);
  display: inline-flex;
  align-items: center;
}

.gs-sort-ind--idle {
  color: var(--mg-text-muted);
  opacity: 0.35;
}

.gs-pin-ind {
  display: inline-flex;
  align-items: center;
  color: var(--mg-primary);
}

.gs-col-menu-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex: 0 0 20px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
  padding: 0;
}

.gs-col-menu-btn:hover {
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
  color: var(--mg-primary);
}

.gs-filter-row {
  padding: 0.15rem 0.4rem 0.4rem;
}

.gs-filter-input {
  width: 100%;
  border: 1px solid var(--mg-border-light);
  border-radius: 6px;
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.64rem;
  padding: 0.18rem 0.35rem;
  outline: none;
  min-height: 24px;
}

.gs-filter-input:focus {
  border-color: var(--mg-primary);
}

/* dropdown فیلتر — کوچک و هماهنگ */
.gs-th :deep(.searchable-dropdown) {
  min-width: 0;
  max-width: 100%;
  width: 100%;
}

.gs-th :deep(.searchable-dropdown .select) {
  min-height: 24px;
  max-height: 24px;
  padding: 0.08rem 0.3rem;
  font-size: 0.62rem;
  border-radius: 5px;
  border-color: var(--mg-border-light);
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  line-height: 1;
}

.gs-th :deep(.searchable-dropdown .selected-label) {
  font-size: 0.62rem;
  line-height: 1.2;
}

.gs-th :deep(.searchable-dropdown .chevron) {
  font-size: 0.6rem;
}

.gs-th :deep(.searchable-dropdown .dropdown-panel) {
  max-width: 220px;
  min-width: 170px;
  font-size: 0.66rem;
}

/* ستون فریز */
.gs-frozen {
  position: sticky;
  z-index: 4;
  background: color-mix(in srgb, var(--mg-bg-soft) 55%, var(--mg-bg-surface));
}

.gs-td.gs-frozen {
  background: var(--mg-bg-surface);
}

.gs-rowhead {
  text-align: center;
  padding: 0.4rem 0.45rem;
  font-size: 0.68rem;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-soft) 40%, var(--mg-bg-surface));
  border-bottom: 1px solid var(--mg-border-light);
  border-inline-end: 1px solid var(--mg-border-light);
  cursor: pointer;
  white-space: nowrap;
  width: 36px;
  min-width: 36px;
  max-width: 36px;
}

.gs-head-rowhead {
  position: sticky;
  top: 0;
  z-index: 7;
}

/* ستون انتخاب ردیف */
.gs-select-head {
  width: 36px;
  min-width: 36px;
  max-width: 36px;
  position: sticky;
  top: 0;
  z-index: 7;
  vertical-align: middle;
}

.gs-select-cell {
  width: 36px;
  min-width: 36px;
  max-width: 36px;
  padding: 0.12rem 0.15rem;
  text-align: center;
}

.gs-check {
  width: 14px;
  height: 14px;
  accent-color: var(--mg-primary);
  cursor: pointer;
  margin: 0;
  vertical-align: middle;
  flex-shrink: 0;
}

/* نوار عملیات گروهی */
.gs-bulk-bar {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
  padding: 0.35rem 0.5rem;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 30%, var(--mg-border-light));
  border-radius: 10px;
  background: color-mix(in srgb, var(--mg-primary) 7%, var(--mg-bg-surface));
}

.gs-bulk-count {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--mg-primary);
  white-space: nowrap;
}

.gs-bulk-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border: 1px solid var(--mg-border-light);
  border-radius: 8px;
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.26rem 0.55rem;
  cursor: pointer;
  white-space: nowrap;
}

.gs-bulk-btn:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
  color: var(--mg-primary);
}

.gs-bulk-btn--on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 30%, var(--mg-border-light));
}

.gs-bulk-btn--off {
  color: var(--mg-danger, #a6543f);
  background: color-mix(in srgb, var(--mg-danger, #a6543f) 8%, var(--mg-bg-surface));
  border-color: color-mix(in srgb, var(--mg-danger, #a6543f) 30%, var(--mg-border-light));
}

.gs-bulk-btn--ghost {
  background: transparent;
  border-color: transparent;
  color: var(--mg-text-muted);
}

.gs-bulk-btn--edit {
  color: var(--mg-text-main);
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-primary) 9%, var(--mg-bg-surface));
}

.gs-bulk-btn--edit:hover {
  color: var(--mg-primary);
}

/* فرم مودال ویرایش گروهی */
.gs-bulk-edit-form {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
  min-width: 0;
}

.gs-be-quick {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.gs-be-quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.4rem;
}

.gs-be-quick-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  min-height: 34px;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.72rem;
  font-weight: 700;
  cursor: pointer;
  padding: 0.35rem 0.5rem;
  white-space: nowrap;
}

.gs-be-quick-btn:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 45%, var(--mg-border-light));
  color: var(--mg-primary);
}

.gs-be-quick-btn--on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 30%, var(--mg-border-light));
}

.gs-be-quick-btn--off {
  color: var(--mg-danger, #a6543f);
  background: color-mix(in srgb, var(--mg-danger, #a6543f) 8%, var(--mg-bg-surface));
  border-color: color-mix(in srgb, var(--mg-danger, #a6543f) 30%, var(--mg-border-light));
}

.gs-be-divider {
  height: 1px;
  background: var(--mg-border-light);
  margin: 0.1rem 0;
}

.gs-be-field {
  display: grid;
  gap: 0.3rem;
  min-width: 0;
}

.gs-be-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--mg-text-muted);
}

.gs-be-input {
  width: 100%;
  min-height: 38px;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.8rem;
  padding: 0.4rem 0.6rem;
  outline: none;
}

.gs-be-input:focus {
  border-color: var(--mg-primary);
}

/* ورودی عددی فارسی در مودال ویرایش گروهی */
.gs-bulk-edit-form :deep(.gs-be-input) {
  width: 100%;
  min-height: 38px;
  border: 1px solid var(--mg-border-light);
  border-radius: 10px;
  background: var(--mg-bg-page);
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.8rem;
  padding: 0.4rem 0.6rem;
  outline: none;
}

.gs-bulk-edit-form :deep(.gs-be-input:focus) {
  border-color: var(--mg-primary);
}

.gs-be-hint {
  margin: 0;
  font-size: 0.68rem;
  color: var(--mg-text-muted);
  line-height: 1.7;
}

.gs-be-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* ستون دکمه باز کردن جزئیات */
.gs-actions-head {
  width: 40px;
  min-width: 40px;
  max-width: 40px;
  position: sticky;
  top: 0;
  z-index: 7;
  color: var(--mg-text-muted);
  display: table-cell;
  vertical-align: middle;
}

.gs-actions-cell {
  width: 40px;
  min-width: 40px;
  max-width: 40px;
  padding: 0.12rem 0.15rem;
  text-align: center;
}

.gs-open-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
  padding: 0;
}

.gs-open-btn:hover {
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
  color: var(--mg-primary);
}

/* حالت زبرا — ردیف‌های یک‌درمیان */
.gs-tr:nth-child(even) .gs-td,
.gs-tr:nth-child(even) .gs-rowhead {
  background: color-mix(in srgb, var(--mg-bg-soft) 34%, var(--mg-bg-surface));
}

.gs-tr:nth-child(even) .gs-td.gs-frozen {
  background: color-mix(in srgb, var(--mg-bg-soft) 34%, var(--mg-bg-surface));
}

.gs-tr:nth-child(even) .gs-td:hover {
  background: color-mix(in srgb, var(--mg-primary) 6%, color-mix(in srgb, var(--mg-bg-soft) 34%, var(--mg-bg-surface)));
}

.gs-tr:nth-child(even) .gs-td--active {
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
}

.gs-tr:nth-child(even) .gs-td--active:hover {
  background: color-mix(in srgb, var(--mg-primary) 11%, var(--mg-bg-surface));
}

.gs-tr:nth-child(even) .gs-td--edited {
  background: color-mix(in srgb, var(--mg-success) 9%, var(--mg-bg-surface));
}

.gs-tr:nth-child(even) .gs-td--edited:hover {
  background: color-mix(in srgb, var(--mg-success) 12%, var(--mg-bg-surface));
}

/* سلول‌های فریز: hover و حالت‌های فعال/ویرایش‌شده */
.gs-td.gs-frozen:hover {
  background: color-mix(in srgb, var(--mg-primary) 5%, var(--mg-bg-surface));
}

.gs-td.gs-frozen.gs-td--active {
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
}

.gs-td.gs-frozen.gs-td--edited {
  background: color-mix(in srgb, var(--mg-success) 8%, var(--mg-bg-surface));
}

.gs-td {
  padding: 0.3rem 0.45rem;
  border-bottom: 1px solid color-mix(in srgb, var(--mg-border-light) 60%, transparent);
  border-inline-end: 1px solid color-mix(in srgb, var(--mg-border-light) 45%, transparent);
  cursor: cell;
  min-width: 110px;
  max-width: 220px;
  transition: background 0.1s ease;
}

.gs-td:hover {
  background: color-mix(in srgb, var(--mg-primary) 5%, transparent);
}

.gs-td--active {
  outline: 2px solid var(--mg-primary);
  outline-offset: -2px;
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
}

.gs-td--edited {
  background: color-mix(in srgb, var(--mg-success) 8%, var(--mg-bg-surface));
}

.gs-cell-text {
  display: block;
  min-height: 1.2em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 160px;
}

.gs-input {
  width: 100%;
  border: 1px solid var(--mg-primary);
  border-radius: 6px;
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.74rem;
  padding: 0.15rem 0.3rem;
  outline: none;
  min-height: 26px;
}

/* ورودی عددی فارسی داخل سلول — جمع‌وجور و هماهنگ */
.gs-td :deep(.persian-number-input) {
  width: 100%;
  min-width: 0;
}

.gs-td :deep(.persian-number-input .input) {
  width: 100%;
  min-height: 26px;
  border: 1px solid var(--mg-primary);
  border-radius: 6px;
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.74rem;
  padding: 0.15rem 0.3rem;
  outline: none;
}

.gs-td :deep(.persian-number-input .suffix) {
  color: var(--mg-text-muted);
  font-size: 0.66rem;
}

/* ورودی عدد فارسی داخل سلول */
.gs-td :deep(.persian-number-input) {
  width: 100%;
  min-width: 0;
}

.gs-td :deep(.persian-number-input .input-wrap) {
  width: 100%;
  display: flex;
  align-items: center;
}

.gs-td :deep(.persian-number-input .number-input) {
  min-height: 26px;
  padding: 0.15rem 0.3rem;
  font-size: 0.74rem;
  border-radius: 6px;
  border-color: var(--mg-primary);
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
}

.gs-td :deep(.persian-number-input .number-input:focus) {
  border-color: var(--mg-primary);
  box-shadow: 0 0 0 2px rgb(var(--mg-primary-rgb) / 0.15);
}

.gs-be-form-num :deep(.persian-number-input .number-input),
.gs-bulk-edit-form :deep(.persian-number-input .number-input) {
  min-height: 38px;
  font-size: 0.8rem;
  border-radius: 10px;
  border-color: var(--mg-border-light);
}

.gs-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.06rem 0.4rem;
  font-size: 0.64rem;
  font-weight: 600;
}

.gs-pill--on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
}

.gs-pill--off {
  color: #92400e;
  background: rgb(254 243 199 / 0.95);
}

.gs-select-pill {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.06rem 0.4rem;
  font-size: 0.64rem;
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
}

.gs-bool {
  display: inline-flex;
}

.gs-bool-btn {
  border: 1px solid var(--mg-border-light);
  border-radius: 6px;
  background: var(--mg-bg-page);
  color: var(--mg-text-muted);
  font-family: inherit;
  font-size: 0.68rem;
  padding: 0.15rem 0.45rem;
  cursor: pointer;
  min-height: 26px;
}

.gs-bool-btn.on {
  background: var(--mg-success-bg);
  border-color: var(--mg-success);
  color: var(--mg-success);
  font-weight: 600;
}

/* dropdown داخل سلول — خیلی کوچیک و جای درست */
.gs-td :deep(.searchable-dropdown) {
  min-width: 0;
  max-width: 100%;
  width: 100%;
}

.gs-td :deep(.searchable-dropdown .select) {
  min-height: 24px;
  max-height: 24px;
  padding: 0.08rem 0.3rem;
  font-size: 0.62rem;
  border-radius: 5px;
  border-color: var(--mg-border-light);
  background: var(--mg-bg-page);
  line-height: 1;
}

.gs-td :deep(.searchable-dropdown .selected-label) {
  font-size: 0.62rem;
  line-height: 1.2;
}

.gs-td :deep(.searchable-dropdown .chevron) {
  font-size: 0.6rem;
}

.gs-td :deep(.searchable-dropdown .dropdown-panel) {
  max-width: 200px;
  min-width: 150px;
  font-size: 0.66rem;
}

/* منوی گزینه‌های ستون */
.gs-col-menu {
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  box-shadow: 0 18px 40px rgb(30 22 17 / 0.16);
  padding: 0.3rem;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.gs-col-menu-title {
  font-size: 0.62rem;
  font-weight: 800;
  color: var(--mg-text-muted);
  padding: 0.2rem 0.5rem 0.3rem;
  border-bottom: 1px solid var(--mg-border-light);
  margin-bottom: 0.15rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gs-menu-item {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  width: 100%;
  border: none;
  background: transparent;
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.72rem;
  text-align: right;
  padding: 0.42rem 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
}

.gs-menu-item:hover {
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
  color: var(--mg-primary);
}

.gs-menu-item.active {
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
  color: var(--mg-primary);
  font-weight: 700;
}

.gs-menu-sep {
  height: 1px;
  background: var(--mg-border-light);
  margin: 0.15rem 0.3rem;
}

/* موبایل */
@media (max-width: 640px) {
  .gs-table {
    font-size: 0.68rem;
  }

  .gs-th {
    min-width: 100px;
  }

  .gs-td {
    min-width: 90px;
    max-width: 160px;
  }
}
</style>
