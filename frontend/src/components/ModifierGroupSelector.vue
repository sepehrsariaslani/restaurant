<template>
  <div class="section">
    <h3 class="section-title">انتخاب افزودنی ها</h3>

    <div class="stack" v-if="groups.length">
      <div class="group-box" v-for="group in groups" :key="group.group_name">
        <header>
          <h4>{{ group.title }}</h4>
          <p class="muted">
            حداقل {{ group.min_select }} و حداکثر {{ group.max_select }}
            <span v-if="Number(group.required) === 1">(اجباری)</span>
          </p>
        </header>

        <div class="options">
          <label v-for="option in group.options" :key="option.name" class="option-row">
            <input
              v-if="group.selection_mode === 'single'"
              type="radio"
              :name="group.group_name"
              :checked="isSelected(group.group_name, option.name)"
              @change="selectSingle(group, option.name)"
            />

            <input
              v-else
              type="checkbox"
              :checked="isSelected(group.group_name, option.name)"
              :disabled="isMultiDisabled(group, option.name)"
              @change="toggleMulti(group, option.name)"
            />

            <span>
              {{ option.name }}
              <small class="muted" v-if="Number(option.price_delta)">
                (+{{ formatMoney(option.price_delta, currency) }})
              </small>
            </span>
          </label>
        </div>
      </div>
    </div>

    <p v-else class="muted">برای این آیتم Modifier تعریف نشده است.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '@/utils/format'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  groups: {
    type: Array,
    default: () => [],
  },
  currency: {
    type: String,
    default: 'TOMAN',
  },
})

const emit = defineEmits(['update:modelValue'])

const selections = computed(() =>
  Array.isArray(props.modelValue)
    ? props.modelValue.filter((row) => row && row.group && row.option)
    : [],
)

function apply(next) {
  emit('update:modelValue', next)
}

function isSelected(groupName, optionName) {
  return selections.value.some((row) => row.group === groupName && row.option === optionName)
}

function countByGroup(groupName) {
  return selections.value.filter((row) => row.group === groupName).length
}

function selectSingle(group, optionName) {
  const next = selections.value.filter((row) => row.group !== group.group_name)
  next.push({ group: group.group_name, option: optionName, qty: 1 })
  apply(next)
}

function toggleMulti(group, optionName) {
  const selected = isSelected(group.group_name, optionName)

  if (selected) {
    apply(selections.value.filter((row) => !(row.group === group.group_name && row.option === optionName)))
    return
  }

  if (countByGroup(group.group_name) >= Number(group.max_select || 1)) {
    return
  }

  apply([...selections.value, { group: group.group_name, option: optionName, qty: 1 }])
}

function isMultiDisabled(group, optionName) {
  if (isSelected(group.group_name, optionName)) {
    return false
  }
  return countByGroup(group.group_name) >= Number(group.max_select || 1)
}
</script>

<style scoped>
.section {
  display: grid;
  gap: 0.7rem;
}

.stack {
  display: grid;
  gap: 0.75rem;
}

.group-box {
  padding: 0.7rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.45);
}

.group-box h4 {
  margin: 0;
}

.group-box p {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
}

.options {
  margin-top: 0.5rem;
  display: grid;
  gap: 0.42rem;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}
</style>
