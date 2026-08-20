<template>
  <div v-if="visible" class="nsb">
    <div class="nsb-content">
      <span class="nsb-icon"><Save :size="14" /></span>
      <span class="nsb-text">
        تغییرات <strong>{{ viewName }}</strong> هنوز ذخیره نشده‌اند.
      </span>
    </div>
    <div class="nsb-actions">
      <button type="button" class="nsb-btn" @click="$emit('save-self')">
        <User :size="13" /> ذخیره برای خودم
      </button>
      <button type="button" class="nsb-btn nsb-btn--success" @click="$emit('save-all')">
        <Users :size="13" /> ذخیره برای همه
      </button>
      <button type="button" class="nsb-btn nsb-btn--ghost" @click="$emit('discard')">انصراف</button>
    </div>
  </div>
</template>

<script setup>
import { Save, User, Users } from "lucide-vue-next";

defineProps({
  visible: { type: Boolean, default: false },
  viewName: { type: String, default: "" },
});

defineEmits(["save-self", "save-all", "discard"]);
</script>

<style scoped>
.nsb {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
  flex-wrap: wrap;
  padding: 0.5rem 0.7rem;
  border-radius: 10px;
  background: color-mix(in srgb, var(--mg-primary) 8%, var(--mg-bg-surface));
  border: 1px solid color-mix(in srgb, var(--mg-primary) 30%, var(--mg-border-light));
}

.nsb-content {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.74rem;
  color: var(--mg-text-main);
}

.nsb-icon {
  display: inline-flex;
  color: var(--mg-primary);
}

.nsb-text strong {
  color: var(--mg-primary);
}

.nsb-actions {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.nsb-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  color: var(--mg-text-muted);
  font-family: inherit;
  font-size: 0.7rem;
  font-weight: 600;
  border-radius: 8px;
  padding: 0.28rem 0.55rem;
  cursor: pointer;
  transition: all 0.12s ease;
}

.nsb-btn:hover {
  border-color: color-mix(in srgb, var(--mg-primary) 40%, var(--mg-border-light));
  color: var(--mg-primary);
}

.nsb-btn--success {
  background: var(--mg-success);
  border-color: var(--mg-success);
  color: #fff;
}

.nsb-btn--success:hover {
  background: color-mix(in srgb, var(--mg-success) 85%, #000);
  color: #fff;
}

.nsb-btn--ghost {
  background: transparent;
  border-color: transparent;
  color: var(--mg-text-muted);
}
</style>
