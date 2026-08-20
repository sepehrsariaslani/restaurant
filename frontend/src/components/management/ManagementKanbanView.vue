<template>
  <div class="kb-shell">
    <div class="kb-scroll">
      <div class="kb-board">
        <section
          v-for="(column, index) in groups"
          :key="`kb-col-${column.value || 'none'}`"
          class="kb-col"
          :data-col-value="column.value || '__none__'"
          :class="{ 'kb-col--over': dragOverCol === (column.value || '__none__') && dragRow }"
        >
          <header class="kb-col-head">
            <span class="kb-dot" :style="{ background: dotColor(index) }"></span>
            <strong class="kb-col-title" :title="column.label">{{ column.label }}</strong>
            <span class="kb-col-count">{{ column.rows.length }}</span>
          </header>

          <div class="kb-col-body">
            <article
              v-for="row in column.rows"
              :key="rowKey(row)"
              class="kb-card"
              :class="[cardClasses(row), { 'kb-card--drag': dragRow && rowKey(dragRow) === rowKey(row) }]"
              @pointerdown="onCardPointerDown($event, row)"
              @click="handleCardClick(row)"
            >
              <div class="kb-card-top">
                <div class="kb-card-media">
                  <img v-if="imageOf(row)" :src="imageOf(row)" loading="lazy" alt="" />
                  <span v-else class="kb-card-fallback">{{ initials(row) }}</span>
                </div>
                <div class="kb-card-main">
                  <strong class="kb-card-title">{{ row[titleField] || '—' }}</strong>
                  <span class="kb-card-code">{{ row.item_code || '' }}</span>
                </div>
                <span v-if="statusBadge(row)" class="kb-status" :class="statusClass(row)">
                  {{ statusBadge(row) }}
                </span>
              </div>

              <div class="kb-card-chips">
                <span v-if="priceOf(row) > 0" class="kb-chip kb-chip--price">{{ priceText(row) }}</span>
                <span v-if="groupBy !== 'category_title' && row.category_title" class="kb-chip">
                  {{ row.category_title }}
                </span>
                <span
                  v-for="tag in (row.tags || []).slice(0, 3)"
                  :key="`${rowKey(row)}-${tag}`"
                  class="kb-chip kb-chip--tag"
                >
                  {{ tag }}
                </span>
              </div>
            </article>

            <p v-if="!column.rows.length" class="kb-empty">بدون مورد — اینجا رها کنید</p>
          </div>
        </section>
      </div>
    </div>

    <p v-if="!groups.length" class="kb-no-data">{{ emptyText }}</p>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  rows: { type: Array, default: () => [] },
  groupBy: { type: String, default: "category_title" },
  groupOptions: { type: Array, default: () => [] },
  rowKey: { type: [String, Function], default: "name" },
  imageField: { type: String, default: "image" },
  secondaryImageField: { type: String, default: "website_image" },
  titleField: { type: String, default: "title" },
  priceFormatter: { type: Function, default: null },
  rowClass: { type: [String, Function], default: "" },
  clickable: { type: Boolean, default: false },
  emptyText: { type: String, default: "محصولی برای نمایش وجود ندارد." },
});

const emit = defineEmits(["row-click", "move-row"]);

const DOT_COLORS = ["#C97852", "#6F7B56", "#8A8B63", "#B98A5E", "#9C7B5B", "#7A8B6F", "#C79A6B", "#A8765A"];

function rowKey(row) {
  if (typeof props.rowKey === "function") return props.rowKey(row);
  return row?.[props.rowKey] ?? row?.name ?? JSON.stringify(row);
}

function groupValue(row) {
  const raw = row?.[props.groupBy];
  if (raw === null || raw === undefined || raw === "") return "";
  if (typeof raw === "boolean" || raw === 1 || raw === 0 || String(raw).trim() === "1" || String(raw).trim() === "0") {
    return Number(raw) === 1 || raw === true ? "بله" : "خیر";
  }
  if (Array.isArray(raw)) return "";
  return String(raw).trim();
}

const groups = computed(() => {
  const map = new Map();
  const ungrouped = [];
  for (const row of props.rows || []) {
    const value = groupValue(row);
    if (!value) {
      ungrouped.push(row);
      continue;
    }
    if (!map.has(value)) map.set(value, []);
    map.get(value).push(row);
  }
  const labels = new Map((props.groupOptions || []).map((o) => [String(o.value), String(o.label || o.value)]));
  const columns = Array.from(map.entries())
    .map(([value, rows]) => ({ value, label: labels.get(value) || value, rows }))
    .sort((a, b) => a.label.localeCompare(b.label, "fa"));
  if (ungrouped.length) {
    columns.unshift({ value: "", label: "بدون گروه", rows: ungrouped });
  }
  return columns;
});

function imageOf(row) {
  return String(row?.[props.imageField] || row?.[props.secondaryImageField] || "").trim() || "";
}

function initials(row) {
  const title = String(row?.[props.titleField] || row?.item_code || row?.name || "").trim();
  return [...title].slice(0, 1).join("") || "؟";
}

function priceOf(row) {
  return Number(row?.base_price || 0);
}

function priceText(row) {
  const value = priceOf(row);
  if (props.priceFormatter) return props.priceFormatter(value);
  try {
    return new Intl.NumberFormat("fa-IR").format(value);
  } catch (_) {
    return String(value);
  }
}

function statusBadge(row) {
  if (Number(row?.out_of_stock)) return "ناموجود";
  if (Number(row?.coming_soon)) return "به‌زودی";
  if (!Number(row?.is_active)) return "غیرفعال";
  return "";
}

function statusClass(row) {
  if (Number(row?.out_of_stock)) return "kb-status--warn";
  if (Number(row?.coming_soon)) return "kb-status--soon";
  return "kb-status--off";
}

function cardClasses(row) {
  const list = [];
  const custom = props.rowClass;
  if (typeof custom === "function") {
    const value = custom(row);
    if (value) list.push(value);
  } else if (custom) {
    list.push(custom);
  }
  if (props.clickable) list.push("kb-card--clickable");
  return list;
}

function dotColor(index) {
  return DOT_COLORS[index % DOT_COLORS.length];
}

// ── درگ و دراپ (pointer-based: موش + لمس) ───────────────────────────────────
// به‌جای HTML5 DnD از pointer events با لیسنرهای سطح document استفاده می‌شود
// تا روی همه دستگاه‌ها (از جمله صفحه‌های لمسی و داخل iframe پیش‌نمایش) کار کند؛
// به setPointerCapture وابسته نیست. یک «کارت شناور» (ghost) دنبال اشاره‌گر
// حرکت می‌کند و ستون زیر اشاره‌گر هایلایت می‌شود.
const dragRow = ref(null);
const dragOverCol = ref("");
const suppressClick = ref(false);

let dragCandidate = null;
let dragActive = false;
let pointerStart = { x: 0, y: 0 };
let ghostEl = null;
let activePointerId = null;

const DRAG_THRESHOLD = 6;

function onCardPointerDown(event, row) {
  if (event.pointerType === "mouse" && event.button !== 0) return;
  if (activePointerId !== null) return; // درگ دیگری در جریان است
  activePointerId = event.pointerId;
  dragCandidate = row;
  dragActive = false;
  pointerStart = { x: event.clientX, y: event.clientY };
  document.addEventListener("pointermove", onDocPointerMove);
  document.addEventListener("pointerup", onDocPointerUp);
  document.addEventListener("pointercancel", onDocPointerCancel);
  window.addEventListener("blur", onWindowBlur);
  // best-effort: اگر مرورگر کپچر را پشتیبانی نکند، لیسنرهای document کافی‌اند
  try {
    event.currentTarget.setPointerCapture(event.pointerId);
  } catch (_) {
    /* ignore */
  }
}

function onDocPointerMove(event) {
  if (event.pointerId !== activePointerId) return;
  if (!dragCandidate) return;
  if (!dragActive) {
    const dx = event.clientX - pointerStart.x;
    const dy = event.clientY - pointerStart.y;
    if (Math.abs(dx) + Math.abs(dy) < DRAG_THRESHOLD) return;
    startDrag(event);
    return;
  }
  updateGhost(event);
}

function startDrag(event) {
  const row = dragCandidate;
  if (!row) return;
  const cardEl = event.target && typeof event.target.closest === "function"
    ? event.target.closest(".kb-card")
    : null;
  const rect = cardEl ? cardEl.getBoundingClientRect() : { width: 220 };

  dragRow.value = row;
  dragActive = true;
  suppressClick.value = true;
  document.body.style.userSelect = "none";
  document.body.style.cursor = "grabbing";

  const ghost = document.createElement("div");
  ghost.className = "kb-ghost";
  ghost.textContent = String(row?.[props.titleField] || row?.item_code || row?.name || "").trim();
  ghost.style.position = "fixed";
  ghost.style.width = `${Math.max(rect.width, 200)}px`;
  ghost.style.pointerEvents = "none";
  ghost.style.zIndex = "20000";
  ghost.style.margin = "0";
  ghost.style.padding = "0.6rem 0.7rem";
  ghost.style.borderRadius = "12px";
  ghost.style.border = "1px solid color-mix(in srgb, var(--mg-primary) 45%, var(--mg-border-light))";
  ghost.style.background = "var(--mg-bg-surface)";
  ghost.style.color = "var(--mg-text-main)";
  ghost.style.boxShadow = "0 18px 40px rgb(52 38 31 / 0.28)";
  ghost.style.transform = "rotate(2deg)";
  ghost.style.fontSize = "0.76rem";
  ghost.style.fontWeight = "700";
  ghost.style.opacity = "0.92";
  document.body.appendChild(ghost);
  ghostEl = ghost;
  updateGhost(event);
}

function updateGhost(event) {
  if (!ghostEl) return;
  ghostEl.style.top = `${event.clientY - 16}px`;
  ghostEl.style.left = `${event.clientX - ghostEl.offsetWidth / 2}px`;

  // ستون زیر اشاره‌گر را پیدا کن
  let targetValue = "";
  try {
    const el = document.elementFromPoint(event.clientX, event.clientY);
    const col = el && typeof el.closest === "function" ? el.closest(".kb-col") : null;
    if (col) targetValue = col.getAttribute("data-col-value") || "";
  } catch (_) {
    /* ignore */
  }
  dragOverCol.value = targetValue;
}

function onDocPointerUp(event) {
  if (event.pointerId !== activePointerId) return;
  const row = dragRow.value;
  const targetValue = dragOverCol.value;
  const wasDragging = dragActive;
  cleanupDrag(wasDragging);
  // کلیک ساده (بدون درگ) → بدون جابه‌جایی؛ خود کلیک کارت را باز می‌کند
  if (!row || !wasDragging) return;
  // رها کردن بیرون از هر ستون → بدون تغییر
  if (targetValue === "") return;
  const normalized = targetValue === "__none__" ? "" : targetValue;
  if (String(normalized ?? "") === groupValue(row)) return;
  emit("move-row", { row, field: props.groupBy, value: normalized });
}

function onDocPointerCancel(event) {
  if (event.pointerId !== activePointerId) return;
  cleanupDrag(true);
}

function onWindowBlur() {
  if (activePointerId !== null) cleanupDrag(true);
}

function cleanupDrag(wasDragging = false) {
  if (ghostEl) {
    ghostEl.remove();
    ghostEl = null;
  }
  document.body.style.userSelect = "";
  document.body.style.cursor = "";
  dragRow.value = null;
  dragOverCol.value = "";
  dragCandidate = null;
  dragActive = false;
  activePointerId = null;
  document.removeEventListener("pointermove", onDocPointerMove);
  document.removeEventListener("pointerup", onDocPointerUp);
  document.removeEventListener("pointercancel", onDocPointerCancel);
  window.removeEventListener("blur", onWindowBlur);
  // فقط بعد از یک درگ واقعی، کلیکِ بعدی را نادیده بگیر؛
  // کلیک ساده باید همیشه کار کند (باز شدن صفحه محصول)
  if (wasDragging) {
    suppressClick.value = true;
    setTimeout(() => { suppressClick.value = false; }, 250);
  } else {
    suppressClick.value = false;
  }
}

function handleCardClick(row) {
  if (suppressClick.value) {
    suppressClick.value = false;
    return;
  }
  if (!props.clickable) return;
  emit("row-click", row);
}
</script>

<style scoped>
.kb-shell {
  width: 100%;
  min-width: 0;
}

.kb-scroll {
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 0.35rem;
}

.kb-board {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  min-width: max-content;
  padding: 0.2rem 0.15rem;
}

.kb-col {
  width: 235px;
  min-width: 235px;
  display: flex;
  flex-direction: column;
  max-height: 62vh;
  border: 1px solid var(--mg-border-light);
  border-radius: 14px;
  background: color-mix(in srgb, var(--mg-bg-page) 55%, var(--mg-bg-surface));
  transition: border-color 0.15s ease, background 0.15s ease;
}

.kb-col--over {
  border-color: color-mix(in srgb, var(--mg-primary) 55%, var(--mg-border-light));
  background: color-mix(in srgb, var(--mg-primary) 6%, var(--mg-bg-surface));
}

.kb-col-head {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.55rem;
  border-bottom: 1px solid var(--mg-border-light);
  background: color-mix(in srgb, var(--mg-bg-soft) 40%, var(--mg-bg-surface));
  border-radius: 14px 14px 0 0;
}

.kb-dot {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  flex-shrink: 0;
}

.kb-col-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.74rem;
  font-weight: 800;
  color: var(--mg-text-main);
  flex: 1;
}

.kb-col-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 20px;
  padding: 0 0.35rem;
  border-radius: 999px;
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
  color: var(--mg-primary);
  font-size: 0.64rem;
  font-weight: 800;
}

.kb-col-body {
  overflow-y: auto;
  padding: 0.45rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  flex: 1;
}

.kb-empty {
  margin: 0;
  padding: 0.7rem 0.4rem;
  text-align: center;
  font-size: 0.66rem;
  color: var(--mg-text-muted);
  border: 1px dashed var(--mg-border-light);
  border-radius: 10px;
}

.kb-card {
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  background: var(--mg-bg-surface);
  padding: 0.5rem 0.55rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  box-shadow: 0 1px 3px rgb(52 38 31 / 0.05);
  transition: box-shadow 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
}

.kb-card--clickable {
  cursor: grab;
}

.kb-card--clickable:active {
  cursor: grabbing;
}

.kb-card {
  touch-action: none;
}

.kb-card:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 30%, var(--mg-border-light));
  box-shadow: 0 6px 16px rgb(52 38 31 / 0.09);
}

.kb-card--drag {
  opacity: 0.4;
}

/* کارت شناور هنگام درگ (به body منتقل می‌شود) */
.kb-ghost {
  opacity: 0.92;
  pointer-events: none;
  border: 1px solid color-mix(in srgb, var(--mg-primary) 45%, var(--mg-border-light)) !important;
}

.kb-card-top {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.kb-card-media {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border: 1px solid var(--mg-border-light);
  background: color-mix(in srgb, var(--mg-bg-soft) 60%, var(--mg-bg-surface));
}

.kb-card-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.kb-card-fallback {
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--mg-primary);
}

.kb-card-main {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.kb-card-title {
  font-size: 0.76rem;
  font-weight: 800;
  color: var(--mg-text-main);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kb-card-code {
  font-size: 0.62rem;
  color: var(--mg-text-muted);
  direction: ltr;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-status {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 0.1rem 0.45rem;
  font-size: 0.58rem;
  font-weight: 800;
  white-space: nowrap;
}

.kb-status--warn {
  color: #92400e;
  background: rgb(254 243 199 / 0.95);
}

.kb-status--soon {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 12%, transparent);
}

.kb-status--off {
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-text-muted) 10%, transparent);
}

.kb-card-chips {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.kb-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.08rem 0.45rem;
  font-size: 0.6rem;
  font-weight: 600;
  color: var(--mg-text-muted);
  background: color-mix(in srgb, var(--mg-bg-soft) 65%, transparent);
  border: 1px solid color-mix(in srgb, var(--mg-border-light) 70%, transparent);
  white-space: nowrap;
}

.kb-chip--price {
  color: var(--mg-success);
  background: var(--mg-success-bg);
  border-color: color-mix(in srgb, var(--mg-success) 25%, transparent);
}

.kb-chip--tag {
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 9%, transparent);
}

.kb-no-data {
  margin: 0;
  padding: 1rem;
  text-align: center;
  font-size: 0.76rem;
  color: var(--mg-text-muted);
}

/* موبایل */
@media (max-width: 640px) {
  .kb-col {
    width: 210px;
    min-width: 210px;
    max-height: 56vh;
  }
}
</style>
