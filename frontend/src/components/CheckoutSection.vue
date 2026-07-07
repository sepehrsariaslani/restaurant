<template>
  <GlassCard class="checkout">
    <h3 class="section-title">ثبت سفارش</h3>

    <div class="fields">
      <label>
        <span>نام مشتری</span>
        <input class="input" :value="form.customer_name" @input="setField('customer_name', $event.target.value)" />
      </label>

      <label>
        <span>موبایل</span>
        <input class="input" :value="form.mobile" @input="setField('mobile', $event.target.value)" />
      </label>

      <label>
        <span>نوع سفارش</span>
        <select class="select" :value="form.order_type" @change="setField('order_type', $event.target.value)">
          <option value="takeaway">بیرون بر</option>
          <option value="dine_in">داخل سالن</option>
          <option value="delivery">ارسال</option>
        </select>
      </label>

      <label v-if="form.order_type === 'delivery'">
        <span>آدرس</span>
        <textarea class="textarea" :value="form.address" @input="setField('address', $event.target.value)" />
      </label>

      <label>
        <span>توضیحات سفارش</span>
        <textarea class="textarea" :value="form.note" @input="setField('note', $event.target.value)" />
      </label>

      <label class="inline-toggle">
        <input
          type="checkbox"
          :checked="form.include_service_items !== false"
          @change="setField('include_service_items', $event.target.checked)"
        />
        <span>اقلام همراه سفارش (مثل قاشق و چنگال) اضافه شود</span>
      </label>
    </div>

    <p class="error" v-if="error">{{ error }}</p>

    <button class="primary-btn" :disabled="submitting" @click="$emit('submit')">
      {{ submitting ? 'در حال ثبت...' : 'ثبت سفارش' }}
    </button>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'
import GlassCard from './GlassCard.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      customer_name: '',
      mobile: '',
      order_type: 'takeaway',
      address: '',
      note: '',
      include_service_items: true,
    }),
  },
  submitting: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['update:modelValue', 'submit'])

const form = computed(() => props.modelValue || {})

function setField(field, value) {
  emit('update:modelValue', {
    ...form.value,
    [field]: value,
  })
}
</script>

<style scoped>
.checkout {
  display: grid;
  gap: 0.75rem;
}

.fields {
  display: grid;
  gap: 0.65rem;
}

label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.9rem;
}

.inline-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.error {
  margin: 0;
  color: var(--danger);
  font-size: 0.86rem;
}
</style>
