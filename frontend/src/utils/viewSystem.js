// ─────────────────────────────────────────────────────────────────────────────
// viewSystem.js — سیستم View به سبک Notion (مستقل از صفحه)
// هر View تنظیمات خودش را دارد: فیلتر، مرتب‌سازی، گروه‌بندی، رنگ، خواص.
// در localStorage ذخیره می‌شود.
// ─────────────────────────────────────────────────────────────────────────────
import { computed, ref, watch } from "vue";

export const PRODUCT_PROPERTIES = [
  { key: "name", label: "شناسه داخلی", type: "text" },
  { key: "item_code", label: "کد کالا", type: "text" },
  { key: "title", label: "نام کالا", type: "text" },
  { key: "short_desc", label: "توضیح کوتاه", type: "text" },
  { key: "category_title", label: "دسته", type: "select" },
  { key: "subcategory_title", label: "زیردسته", type: "select" },
  { key: "base_price", label: "قیمت پایه", type: "number" },
  { key: "stock_qty", label: "موجودی", type: "number" },
  { key: "is_active", label: "وضعیت نمایش", type: "select" },
  { key: "coming_soon", label: "به‌زودی", type: "boolean" },
  { key: "out_of_stock", label: "ناموجود", type: "boolean" },
  { key: "has_customization", label: "قابل شخصی‌سازی", type: "boolean" },
  { key: "has_bom", label: "دارای فرمول (BOM)", type: "boolean" },
  { key: "tags", label: "تگ‌ها", type: "tags" },
  { key: "nutrition_kcal", label: "کالری", type: "number" },
  { key: "nutrition_protein_g", label: "پروتئین (گرم)", type: "number" },
  { key: "nutrition_carb_g", label: "کربوهیدرات (گرم)", type: "number" },
  { key: "nutrition_fat_g", label: "چربی (گرم)", type: "number" },
  { key: "sort_order", label: "ترتیب نمایش", type: "number" },
  { key: "packaging_price", label: "قیمت بسته‌بندی", type: "number" },
  { key: "custom_snapp_code", label: "کد اسنپ‌فود", type: "text" },
  { key: "restaurant_builder_template", label: "قالب سازنده", type: "text" },
  { key: "restaurant_customize_button_label", label: "برچسب دکمه سفارشی‌سازی", type: "text" },
];

export const PROPERTY_OPERATORS = {
  text: [
    ["contains", "شامل"],
    ["not_contains", "شامل نباشد"],
    ["equals", "مساوی"],
    ["not_equals", "نامساوی"],
  ],
  number: [
    ["gt", "بزرگ‌تر از"],
    ["gte", "بزرگ‌تر یا مساوی"],
    ["lt", "کوچک‌تر از"],
    ["lte", "کوچک‌تر یا مساوی"],
    ["equals", "مساوی"],
  ],
  boolean: [
    ["is_true", "بله"],
    ["is_false", "خیر"],
  ],
  select: [
    ["equals", "مساوی"],
    ["not_equals", "نامساوی"],
    ["in", "یکی از"],
    ["not_in", "هیچکدام از"],
  ],
  tags: [
    ["tag_contains", "شامل"],
    ["not_contains", "شامل نباشد"],
    ["tag_in", "یکی از تگ‌ها"],
    ["tag_not_in", "هیچکدام از تگ‌ها"],
  ],
};

export const COLOR_OPTIONS = [
  ["red", "قرمز"],
  ["orange", "نارنجی"],
  ["yellow", "زرد"],
  ["green", "سبز"],
  ["blue", "آبی"],
  ["gray", "خاکستری"],
];

const DEFAULT_PROPERTY_ORDER = [
  "category_title",
  "base_price",
  "stock_qty",
  "is_active",
  "tags",
  "item_code",
];

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export function createDefaultView(overrides = {}) {
  return {
    id: overrides.id || `v-${Math.random().toString(36).slice(2, 9)}`,
    name: overrides.name || "نمای جدید",
    icon: "☰",
    layout: "list",
    filters: [],
    sorts: [],
    groupBy: "",
    subGroupBy: "",
    colors: [],
    properties: {
      item_code: true,
      category_title: true,
      base_price: true,
      stock_qty: true,
      is_active: true,
      tags: true,
    },
    propertyOrder: [...DEFAULT_PROPERTY_ORDER],
    openMode: "full",
    ...overrides,
  };
}

export function useViewSystem({ storageKey, defaultViews = null }) {
  const views = ref([]);
  const currentViewId = ref("");
  const loaded = ref(false);
  const savedSnapshots = ref({}); // id -> deep clone of saved (shared) state
  const dirtyViewIds = ref(new Set()); // views with unsaved changes

  function snapshotOf(view) {
    return JSON.parse(JSON.stringify(view || {}));
  }

  function load() {
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed.views) && parsed.views.length) {
          views.value = parsed.views.map((v) => ({
            ...createDefaultView(),
            ...clone(v),
            properties: { ...createDefaultView().properties, ...(v.properties || {}) },
            propertyOrder:
              Array.isArray(v.propertyOrder) && v.propertyOrder.length
                ? v.propertyOrder
                : [...DEFAULT_PROPERTY_ORDER],
          }));
          currentViewId.value = views.value.some((v) => v.id === parsed.currentViewId)
            ? parsed.currentViewId
            : views.value[0].id;
          // snapshot of saved state for dirty-tracking
          savedSnapshots.value = {};
          views.value.forEach((v) => {
            savedSnapshots.value[v.id] = snapshotOf(v);
          });
          loaded.value = true;
          return;
        }
      }
    } catch (_) {
      /* ignore storage errors */
    }
    views.value = (defaultViews || [createDefaultView({ name: "همه محصولات", id: "all" })]).map((v) =>
      createDefaultView(clone(v)),
    );
    currentViewId.value = views.value[0].id;
    savedSnapshots.value = {};
    views.value.forEach((v) => {
      savedSnapshots.value[v.id] = snapshotOf(v);
    });
    loaded.value = true;
  }

  function persist() {
    try {
      window.localStorage.setItem(
        storageKey,
        JSON.stringify({ views: views.value, currentViewId: currentViewId.value }),
      );
    } catch (_) {
      /* ignore */
    }
  }

  // Watch for changes -> mark dirty
  watch(
    views,
    (list) => {
      if (!loaded.value) return;
      const newDirty = new Set(dirtyViewIds.value);
      list.forEach((v) => {
        const saved = savedSnapshots.value[v.id];
        if (!saved) {
          newDirty.add(v.id);
          return;
        }
        if (JSON.stringify(snapshotOf(v)) !== JSON.stringify(saved)) {
          newDirty.add(v.id);
        }
      });
      dirtyViewIds.value = newDirty;
      persist();
    },
    { deep: true },
  );

  const currentView = computed(
    () => views.value.find((v) => v.id === currentViewId.value) || views.value[0] || null,
  );

  const isCurrentViewDirty = computed(() => dirtyViewIds.value.has(currentViewId.value));

  function markSaved(id) {
    const view = views.value.find((v) => v.id === id);
    if (view) {
      savedSnapshots.value[id] = snapshotOf(view);
      const next = new Set(dirtyViewIds.value);
      next.delete(id);
      dirtyViewIds.value = next;
    }
  }

  // ذخیره برای خودم (همان localStorage شخصی)
  function saveForSelf(id) {
    markSaved(id || currentViewId.value);
  }

  // ذخیره برای همه — در این محیط local است ولی snapshot را به‌روز می‌کند
  function saveForEveryone(id) {
    markSaved(id || currentViewId.value);
    persist();
  }

  function addView(name = "") {
    const view = createDefaultView({
      name: String(name || "").trim() || `نمای ${views.value.length + 1}`,
      layout: currentView.value?.layout || "list",
    });
    views.value.push(view);
    savedSnapshots.value[view.id] = snapshotOf(view);
    currentViewId.value = view.id;
    return view;
  }

  function duplicateView(id) {
    const src = views.value.find((v) => v.id === id);
    if (!src) return null;
    const copy = createDefaultView({ ...clone(src), id: undefined, name: `${src.name} (کپی)` });
    views.value.push(copy);
    savedSnapshots.value[copy.id] = snapshotOf(copy);
    currentViewId.value = copy.id;
    return copy;
  }

  function renameView(id, name) {
    const view = views.value.find((v) => v.id === id);
    if (view && String(name || "").trim()) view.name = String(name).trim();
  }

  function deleteView(id) {
    if (views.value.length <= 1) return false;
    views.value = views.value.filter((v) => v.id !== id);
    delete savedSnapshots.value[id];
    const next = new Set(dirtyViewIds.value);
    next.delete(id);
    dirtyViewIds.value = next;
    if (currentViewId.value === id) currentViewId.value = views.value[0].id;
    return true;
  }

  function updateView(id, patch) {
    const view = views.value.find((v) => v.id === id);
    if (view && patch && typeof patch === "object") Object.assign(view, patch);
  }

  function updateCurrentView(patch) {
    updateView(currentViewId.value, patch);
  }

  function resetView(id) {
    const view = views.value.find((v) => v.id === id);
    if (!view) return;
    const fresh = createDefaultView({ id: view.id, name: view.name, icon: view.icon });
    Object.keys(view).forEach((k) => delete view[k]);
    Object.assign(view, fresh);
    // reset = back to saved snapshot
    const saved = savedSnapshots.value[id];
    if (saved) {
      Object.keys(view).forEach((k) => delete view[k]);
      Object.assign(view, clone(saved));
    }
  }

  function selectView(id) {
    if (views.value.some((v) => v.id === id)) currentViewId.value = id;
  }

  function isViewDirty(id) {
    return dirtyViewIds.value.has(id);
  }

  return {
    views,
    currentViewId,
    currentView,
    loaded,
    load,
    isCurrentViewDirty,
    isViewDirty,
    saveForSelf,
    saveForEveryone,
    addView,
    duplicateView,
    renameView,
    deleteView,
    updateView,
    updateCurrentView,
    resetView,
    selectView,
  };
}

// ── عملیات خالص روی داده ─────────────────────────────────────────────────────

function rawIsTruthy(raw) {
  return raw === true || Number(raw) === 1 || String(raw ?? "").trim().toLowerCase() === "true";
}

function rawIsFalsy(raw) {
  return raw === false || Number(raw) === 0 || String(raw ?? "").trim().toLowerCase() === "false" || raw === null || raw === undefined || raw === "";
}

// مقدار «بله/خیر» فارسی را با مقدار بولی/عددی ردیف مقایسه می‌کند
function booleanValueMatches(raw, persianValue) {
  const normalized = String(persianValue ?? "").trim();
  if (normalized === "بله") return rawIsTruthy(raw);
  if (normalized === "خیر") return rawIsFalsy(raw);
  return false;
}

export function matchFilter(row, filter = {}) {
  const { property, operator, value } = filter;
  const raw = row?.[property];
  const text = String(raw ?? "").trim();
  const query = String(value ?? "").trim().toLowerCase();
  switch (operator) {
    case "contains":
      return text.toLowerCase().includes(query);
    case "not_contains":
      return !text.toLowerCase().includes(query);
    case "equals":
      // اگر مقدار «بله/خیر» بود، با مقدار بولی/عددی مقایسه کن
      if (query === "بله" || query === "خیر") {
        return booleanValueMatches(raw, value);
      }
      return text === String(value ?? "").trim();
    case "not_equals":
      if (query === "بله" || query === "خیر") {
        return !booleanValueMatches(raw, value);
      }
      return text !== String(value ?? "").trim();
    case "gt":
      return Number(raw ?? 0) > Number(value ?? 0);
    case "gte":
      return Number(raw ?? 0) >= Number(value ?? 0);
    case "lt":
      return Number(raw ?? 0) < Number(value ?? 0);
    case "lte":
      return Number(raw ?? 0) <= Number(value ?? 0);
    case "is_true":
      return rawIsTruthy(raw);
    case "is_false":
      return rawIsFalsy(raw);
    case "tag_contains":
      return (Array.isArray(raw) ? raw : []).some((t) =>
        String(t).toLowerCase().includes(query),
      );
    case "in": {
      // مقدار می‌تواند آرایه باشد (چند انتخاب) یا رشته جداشده با کاما
      const values = Array.isArray(value)
        ? value.map(String)
        : String(value ?? "").split(",").map((v) => v.trim()).filter(Boolean);
      if (!values.length) return true;
      return values.some((v) => text === String(v).trim());
    }
    case "not_in": {
      const values = Array.isArray(value)
        ? value.map(String)
        : String(value ?? "").split(",").map((v) => v.trim()).filter(Boolean);
      if (!values.length) return true;
      return !values.some((v) => text === String(v).trim());
    }
    case "tag_in": {
      const rowTags = (Array.isArray(raw) ? raw : []).map((t) => String(t).trim());
      const values = Array.isArray(value)
        ? value.map(String)
        : String(value ?? "").split(",").map((v) => v.trim()).filter(Boolean);
      if (!values.length) return true;
      return values.some((v) => rowTags.includes(String(v).trim()));
    }
    case "tag_not_in": {
      const rowTags = (Array.isArray(raw) ? raw : []).map((t) => String(t).trim());
      const values = Array.isArray(value)
        ? value.map(String)
        : String(value ?? "").split(",").map((v) => v.trim()).filter(Boolean);
      if (!values.length) return true;
      return !values.some((v) => rowTags.includes(String(v).trim()));
    }
    default:
      return true;
  }
}

export function applyViewFilters(rows, filters = []) {
  if (!filters.length) return rows;
  return rows.filter((row) => {
    let result = true;
    for (const f of filters) {
      const matched = matchFilter(row, f);
      if (String(f.joiner || "and").toLowerCase() === "or") result = result || matched;
      else result = result && matched;
    }
    return result;
  });
}

export function applyViewSorts(rows, sorts = []) {
  if (!sorts.length) return rows;
  const list = [...rows];
  list.sort((a, b) => {
    for (const s of sorts) {
      const dir = s.direction === "desc" ? -1 : 1;
      const va = a?.[s.property];
      const vb = b?.[s.property];
      const na = Number(va);
      const nb = Number(vb);
      let cmp = 0;
      if (
        Number.isFinite(na) &&
        Number.isFinite(nb) &&
        String(va ?? "").trim() !== "" &&
        String(vb ?? "").trim() !== ""
      ) {
        cmp = na - nb;
      } else {
        cmp = String(va ?? "").localeCompare(String(vb ?? ""), "fa");
      }
      if (cmp !== 0) return cmp * dir;
    }
    return 0;
  });
  return list;
}

export function groupRows(rows, groupBy, subGroupBy = "") {
  if (!groupBy) return null;
  const groups = [];
  const map = new Map();
  for (const row of rows) {
    const key = String(row?.[groupBy] ?? "").trim() || "بدون دسته";
    if (!map.has(key)) {
      map.set(key, { key, label: key, rows: [], subgroups: null });
      groups.push(map.get(key));
    }
    const group = map.get(key);
    if (subGroupBy) {
      if (!group.subgroups) group.subgroups = [];
      const subKey = String(row?.[subGroupBy] ?? "").trim() || "بدون زیرگروه";
      let sub = group.subgroups.find((s) => s.key === subKey);
      if (!sub) {
        sub = { key: subKey, label: subKey, rows: [] };
        group.subgroups.push(sub);
      }
      sub.rows.push(row);
    } else {
      group.rows.push(row);
    }
  }
  return groups;
}

export function colorForRow(row, colors = []) {
  for (const rule of colors) {
    if (matchFilter(row, { property: rule.property, operator: rule.operator, value: rule.value })) {
      return rule.color;
    }
  }
  return "";
}

export function operatorOptionsFor(propertyKey, properties = PRODUCT_PROPERTIES) {
  const prop = properties.find((p) => p.key === propertyKey);
  return PROPERTY_OPERATORS[prop?.type || "text"] || PROPERTY_OPERATORS.text;
}

// ── استخراج گزینه‌های قابل انتخاب از دیتای ردیف‌ها ───────────────────────────
// برای فیلدهای select (مثل دسته، زیردسته، وضعیت) مقادیر یکتا را از ردیف‌ها
// می‌گیرد تا با SearchableDropdown قابل انتخاب شوند.
export function buildSelectOptions(rows, propertyKey) {
  const seen = new Set();
  const options = [];
  for (const row of rows || []) {
    let raw = row?.[propertyKey];
    if (raw === null || raw === undefined || raw === "") continue;
    // اگر بولی یا 0/1 بود به «بله/خیر» ترجمه کن
    if (
      typeof raw === "boolean" ||
      raw === 1 ||
      raw === 0 ||
      String(raw).trim() === "1" ||
      String(raw).trim() === "0"
    ) {
      const label = rawIsTruthy(raw) ? "بله" : "خیر";
      if (!seen.has(label)) {
        seen.add(label);
        options.push({ value: label, label });
      }
      continue;
    }
    if (Array.isArray(raw)) {
      for (const t of raw) {
        const v = String(t ?? "").trim();
        if (!v || seen.has(v)) continue;
        seen.add(v);
        options.push({ value: v, label: v });
      }
      continue;
    }
    const value = String(raw).trim();
    if (!value || seen.has(value)) continue;
    seen.add(value);
    options.push({ value, label: value });
  }
  // ترتیب الفبایی فارسی
  options.sort((a, b) => a.label.localeCompare(b.label, "fa"));
  return options;
}

export function propertyLabelFor(propertyKey, properties = PRODUCT_PROPERTIES) {
  return properties.find((p) => p.key === propertyKey)?.label || propertyKey;
}

export function propertyTypeFor(propertyKey, properties = PRODUCT_PROPERTIES) {
  return properties.find((p) => p.key === propertyKey)?.type || "text";
}

export function operatorNeedsValue(propertyKey, operator, properties = PRODUCT_PROPERTIES) {
  const prop = properties.find((p) => p.key === propertyKey);
  if (prop?.type === "boolean") return false;
  return !["is_true", "is_false"].includes(operator);
}

export function operatorIsMulti(operator) {
  return ["in", "not_in", "tag_in", "tag_not_in"].includes(operator);
}
