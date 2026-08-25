<template>
  <div class="nvt" ref="rootRef">
    <!-- دراپ‌داون انتخاب نمایه -->
    <div class="nvt-dropdown">
      <button type="button" class="nvt-trigger" @click="dropdownOpen = !dropdownOpen">
        <component :is="viewIcon(currentView?.icon)" :size="14" :stroke-width="2" />
        <span class="nvt-trigger-name">{{ currentView?.name || 'انتخاب نما' }}</span>
        <span v-if="isDirty(currentView?.id)" class="nvt-dirty-dot" title="تغییرات ذخیره‌نشده"></span>
        <ChevronDown :size="14" :class="['nvt-chev', { open: dropdownOpen }]" />
      </button>

      <div v-if="dropdownOpen" class="nvt-menu">
        <div class="nvt-menu-head">
          <strong>نمایه‌ها</strong>
          <button type="button" class="nvt-menu-add" title="نمای جدید" @click="onAdd"><Plus :size="14" /></button>
        </div>
        <div
          v-for="v in views"
          :key="v.id"
          class="nvt-item"
          :class="{ active: v.id === currentViewId }"
          @click="selectView(v.id)"
        >
          <component :is="viewIcon(v.icon)" :size="13" :stroke-width="2" class="nvt-item-icon" />
          <span class="nvt-item-name">{{ v.name }}</span>
          <span v-if="isDirty(v.id)" class="nvt-dirty-dot" title="تغییرات ذخیره‌نشده"></span>
          <button
            type="button"
            class="nvt-item-more"
            title="مدیریت نما"
            @click.stop="toggleMenu(v.id)"
          >
            <MoreHorizontal :size="13" />
          </button>
        </div>
      </div>
    </div>

    <!-- منوی مدیریت نما -->
    <div v-if="menuViewId" class="nvt-pop">
      <button type="button" @click="rename"><Pencil :size="12" /> تغییر نام</button>
      <button type="button" @click="duplicate"><Copy :size="12" /> تکراری‌سازی</button>
      <button type="button" @click="copyLink"><Link :size="12" /> کپی لینک</button>
      <button type="button" @click="reset"><RotateCcw :size="12" /> بازنشانی نما</button>
      <button type="button" class="nvt-danger" @click="remove"><Trash2 :size="12" /> حذف نما</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import {
  ChevronDown,
  Copy,
  Link,
  List,
  LayoutGrid,
  MoreHorizontal,
  Pencil,
  Plus,
  RotateCcw,
  Trash2,
} from "lucide-vue-next";

const props = defineProps({
  views: { type: Array, default: () => [] },
  currentViewId: { type: String, default: "" },
  isDirty: { type: Function, default: () => false },
});

const emit = defineEmits(["select", "add", "rename", "duplicate", "delete", "reset", "copy-link"]);

const rootRef = ref(null);
const dropdownOpen = ref(false);
const menuViewId = ref("");

const ICON_MAP = {
  list: List,
  gallery: LayoutGrid,
  tree: LayoutGrid,
};

const currentView = computed(
  () => props.views.find((v) => v.id === props.currentViewId) || props.views[0] || null,
);

function viewIcon(iconName) {
  return ICON_MAP[String(iconName || "").toLowerCase()] || List;
}

function selectView(id) {
  emit("select", id);
  dropdownOpen.value = false;
}

function toggleMenu(id) {
  menuViewId.value = menuViewId.value === id ? "" : id;
}

function onAdd() {
  const name = window.prompt("نام نمای جدید:", "");
  if (name === null) return;
  emit("add", name);
  dropdownOpen.value = false;
}

function rename() {
  const view = props.views.find((v) => v.id === menuViewId.value);
  if (!view) return;
  const name = window.prompt("نام جدید:", view.name);
  if (name === null) return;
  emit("rename", view.id, name);
  menuViewId.value = "";
}

function duplicate() {
  emit("duplicate", menuViewId.value);
  menuViewId.value = "";
  dropdownOpen.value = false;
}

function copyLink() {
  emit("copy-link", menuViewId.value);
  menuViewId.value = "";
}

function reset() {
  if (window.confirm("تنظیمات این نما به حالت ذخیره‌شده برگردد؟")) {
    emit("reset", menuViewId.value);
  }
  menuViewId.value = "";
}

function remove() {
  if (window.confirm("این نما حذف شود؟ (داده‌ها حذف نمی‌شوند)")) {
    emit("delete", menuViewId.value);
  }
  menuViewId.value = "";
}

function onOutsideClick(event) {
  if (rootRef.value && !rootRef.value.contains(event.target)) {
    dropdownOpen.value = false;
    menuViewId.value = "";
  }
}

onMounted(() => document.addEventListener("click", onOutsideClick));
onBeforeUnmount(() => document.removeEventListener("click", onOutsideClick));
</script>

<style scoped>
.nvt {
  position: relative;
  display: flex;
  flex-direction: column;
}

.nvt-dropdown {
  position: relative;
  display: inline-flex;
}

.nvt-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.32rem 0.7rem;
  border-radius: 9px;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.12s ease;
  min-width: 160px;
  justify-content: flex-start;
}

.nvt-trigger:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 55%, var(--mg-border));
  color: var(--mg-primary);
  background: color-mix(in srgb, var(--mg-primary) 5%, var(--mg-bg-surface));
}

.nvt-trigger-name {
  flex: 1;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nvt-chev {
  transition: transform 0.15s ease;
  color: var(--mg-text-muted);
}

.nvt-chev.open {
  transform: rotate(180deg);
}

.nvt-dirty-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--mg-primary);
  flex-shrink: 0;
}

.nvt-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 65;
  min-width: 220px;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  box-shadow: var(--mg-shadow-md);
  padding: 0.35rem;
  display: flex;
  flex-direction: column;
  gap: 1px;
  max-height: 320px;
  overflow-y: auto;
}

.nvt-menu-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.3rem 0.5rem 0.4rem;
  border-bottom: 1px solid var(--mg-border-light);
  margin-bottom: 0.2rem;
}

.nvt-menu-head strong {
  font-size: 0.72rem;
  color: var(--mg-text-muted);
}

.nvt-menu-add {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  border: 1px dashed var(--mg-border);
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
}

.nvt-menu-add:hover {
  border-color: var(--mg-primary);
  color: var(--mg-primary);
}

.nvt-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.42rem 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.1s ease;
}

.nvt-item:hover {
  background: color-mix(in srgb, var(--mg-bg-soft) 65%, transparent);
}

.nvt-item.active {
  background: color-mix(in srgb, var(--mg-primary) 10%, var(--mg-bg-surface));
  color: var(--mg-primary);
}

.nvt-item-icon {
  color: var(--mg-text-muted);
  flex-shrink: 0;
}

.nvt-item.active .nvt-item-icon {
  color: var(--mg-primary);
}

.nvt-item-name {
  flex: 1;
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--mg-text-main);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nvt-item.active .nvt-item-name {
  color: var(--mg-primary);
}

.nvt-item-more {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: 0;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
  border-radius: 5px;
  opacity: 0;
  flex-shrink: 0;
}

.nvt-item:hover .nvt-item-more {
  opacity: 1;
}

.nvt-item-more:hover {
  background: color-mix(in srgb, var(--mg-primary) 14%, transparent);
  color: var(--mg-primary);
}

.nvt-pop {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  z-index: 66;
  min-width: 180px;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: 12px;
  box-shadow: var(--mg-shadow-md);
  padding: 0.3rem;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nvt-pop button {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  border: 0;
  background: transparent;
  color: var(--mg-text-main);
  font-family: inherit;
  font-size: 0.76rem;
  text-align: right;
  padding: 0.42rem 0.6rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.1s ease;
}

.nvt-pop button:hover {
  background: color-mix(in srgb, var(--mg-bg-soft) 70%, transparent);
}

.nvt-pop .nvt-danger {
  color: var(--mg-danger);
}

.nvt-pop .nvt-danger:hover {
  background: var(--mg-danger-bg);
}
</style>
