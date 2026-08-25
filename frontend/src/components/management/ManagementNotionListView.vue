<template>
  <div class="notion-list">
    <article
      v-for="row in rows"
      :key="rowKeyOf(row)"
      class="notion-row"
      :class="rowClassNames(row)"
      @click="handleRowClick(row)"
    >
      <span class="notion-row__grip" aria-hidden="true">⠿</span>

      <div class="notion-row__body">
        <div class="notion-row__title-line">
          <span class="notion-row__title">{{ titleOf(row) }}</span>
          <span v-if="showCode && codeOf(row)" class="notion-row__code">{{ codeOf(row) }}</span>
        </div>

        <div v-if="hasMeta(row)" class="notion-row__meta">
          <template v-for="pkey in orderedProperties" :key="pkey">
            <span
              v-if="isPropVisible(pkey) && chipRenderers?.[pkey]"
              class="notion-chip"
              :class="chipClassFor(row, pkey)"
            >{{ chipTextFor(row, pkey) }}</span>
          </template>
          <template v-if="showTags">
            <span v-for="t in tagsOf(row)" :key="t" class="notion-chip notion-chip--tag">{{ t }}</span>
            <span v-if="moreTagsOf(row)" class="notion-chip notion-chip--tag">+{{ moreTagsOf(row) }}</span>
          </template>
        </div>
      </div>

    </article>

    <div v-if="!rows.length" class="notion-list__empty">
      <slot name="empty">داده‌ای برای نمایش وجود ندارد.</slot>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  rows: { type: Array, default: () => [] },
  rowKey: { type: [String, Function], default: "name" },
  rowClickable: { type: Boolean, default: false },
  titleKey: { type: String, default: "title" },
  codeKey: { type: String, default: "item_code" },
  showCode: { type: Boolean, default: true },
  showTags: { type: Boolean, default: true },
  properties: { type: Object, default: null },
  propertyOrder: { type: Array, default: null },
  chipRenderers: { type: Object, default: null },
  rowClass: { type: [String, Function], default: "" },
});

const emit = defineEmits(["row-click"]);

const DEFAULT_ORDER = ["category_title", "base_price", "stock_qty", "is_active", "tags", "item_code"];

const orderedProperties = props.propertyOrder?.length ? props.propertyOrder : DEFAULT_ORDER;

function valueOf(row, key) {
  if (!row) return null;
  if (typeof key === "function") return key(row);
  return row[key] ?? row[key.replace(/_/g, "")] ?? null;
}

function rowKeyOf(row) {
  if (typeof props.rowKey === "function") return props.rowKey(row);
  return valueOf(row, props.rowKey) ?? JSON.stringify(row);
}

function titleOf(row) {
  return valueOf(row, props.titleKey) || valueOf(row, "name") || valueOf(row, "item_name") || "—";
}

function codeOf(row) {
  return valueOf(row, props.codeKey) || "";
}

function tagsOf(row) {
  const tags = Array.isArray(row?.tags) ? row.tags : [];
  return tags.slice(0, 4);
}

function moreTagsOf(row) {
  const tags = Array.isArray(row?.tags) ? row.tags : [];
  return tags.length > 4 ? tags.length - 4 : 0;
}

function isPropVisible(key) {
  return props.properties?.[key] !== false;
}

function chipTextFor(row, key) {
  try {
    const result = props.chipRenderers?.[key]?.(row);
    return result?.text ?? "";
  } catch (_) {
    return "";
  }
}

function chipClassFor(row, key) {
  try {
    const result = props.chipRenderers?.[key]?.(row);
    return result?.cls ?? "";
  } catch (_) {
    return "";
  }
}

function hasMeta(row) {
  if (props.showTags && tagsOf(row).length) return true;
  for (const key of orderedProperties) {
    if (isPropVisible(key) && chipTextFor(row, key)) return true;
  }
  return false;
}

function rowClassNames(row) {
  const base = typeof props.rowClass === "function" ? props.rowClass(row) : props.rowClass || "";
  return [base, props.rowClickable ? "notion-row--clickable" : ""].filter(Boolean).join(" ");
}

function handleRowClick(row) {
  if (!props.rowClickable) return;
  emit("row-click", row);
}
</script>

<style scoped>
.notion-list {
  display: flex;
  flex-direction: column;
}

.notion-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.45rem 0.55rem;
  border-bottom: 1px solid color-mix(in srgb, var(--mg-border-light) 60%, transparent);
  border-radius: 6px;
  transition: background 0.12s ease;
}

.notion-row:last-child {
  border-bottom: none;
}

.notion-row--clickable {
  cursor: pointer;
}

.notion-row--clickable:hover {
  background: color-mix(in srgb, var(--mg-primary) 7%, var(--mg-bg-surface));
  box-shadow: inset 3px 0 0 0 var(--mg-primary);
}

.notion-row--clickable:active {
  background: color-mix(in srgb, var(--mg-primary) 12%, var(--mg-bg-surface));
}

.notion-row__grip {
  color: var(--mg-border);
  font-size: 0.85rem;
  opacity: 0.55;
  user-select: none;
  flex-shrink: 0;
}

.notion-row__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.notion-row__title-line {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  min-width: 0;
}

.notion-row__title {
  font-size: 0.86rem;
  font-weight: 650;
  color: var(--mg-text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notion-row__code {
  font-size: 0.66rem;
  color: var(--mg-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  direction: ltr;
}

.notion-row__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.notion-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.66rem;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-soft) 65%, transparent);
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 70%, transparent);
  border-radius: 999px;
  padding: 0.08rem 0.45rem;
  white-space: nowrap;
}

.notion-chip--soft {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 25%, transparent);
  font-weight: 600;
}

.notion-chip--code {
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-page) 80%, var(--mg-bg-soft) 20%);
  border-color: var(--mg-border-light);
  font-family: ui-monospace, monospace;
  direction: ltr;
}

.notion-chip--warn {
  color: #92400e;
  background: rgb(254 243 199 / 0.95);
  border-color: transparent;
}

.notion-chip--on {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 30%, transparent);
  font-weight: 600;
}

.notion-chip--off {
  color: #92400e;
  background: rgb(254 243 199 / 0.95);
  border-color: transparent;
}

.notion-chip--tag {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 10%, transparent);
  border-color: transparent;
}

.notion-list__empty {
  padding: 1.5rem 0.75rem;
  text-align: center;
  color: var(--mg-text-muted);
  font-size: 0.8rem;
}

/* Conditional colors */
.notion-row.nrow-red {
  background: color-mix(in srgb, #ef4444 9%, transparent);
}
.notion-row.nrow-orange {
  background: color-mix(in srgb, #f97316 9%, transparent);
}
.notion-row.nrow-yellow {
  background: color-mix(in srgb, #eab308 10%, transparent);
}
.notion-row.nrow-green {
  background: color-mix(in srgb, #22c55e 9%, transparent);
}
.notion-row.nrow-blue {
  background: color-mix(in srgb, #3b82f6 9%, transparent);
}
.notion-row.nrow-gray {
  background: color-mix(in srgb, #6b7280 9%, transparent);
}

</style>
