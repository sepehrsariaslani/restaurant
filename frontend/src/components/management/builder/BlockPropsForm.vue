<template>
  <div class="bpf" dir="rtl">
    <div class="bpf__field" v-for="field in fields" :key="field.key">
      <label class="bpf__label">
        {{ field.label }}
        <small v-if="field.help" class="bpf__help">{{ field.help }}</small>
      </label>

      <!-- textarea -->
      <textarea
        v-if="field.type === 'textarea'"
        class="bpf__input bpf__textarea"
        :value="value(field)"
        @input="set(field, $event.target.value)"
      />

      <!-- number -->
      <input
        v-else-if="field.type === 'number'"
        class="bpf__input"
        type="number"
        :value="value(field)"
        @input="set(field, Number($event.target.value))"
      />

      <!-- boolean -->
      <label v-else-if="field.type === 'boolean'" class="bpf__check">
        <input
          type="checkbox"
          :checked="Boolean(value(field))"
          @change="set(field, $event.target.checked)"
        />
        <span>{{ field.label }}</span>
      </label>

      <!-- select -->
      <select
        v-else-if="field.type === 'select'"
        class="bpf__input"
        :value="value(field)"
        @change="set(field, $event.target.value)"
      >
        <option v-for="opt in field.options || []" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <!-- image -->
      <div v-else-if="field.type === 'image'" class="bpf__image">
        <input
          class="bpf__input"
          type="text"
          placeholder="/files/image.jpg"
          :value="value(field)"
          @input="set(field, $event.target.value)"
        />
        <img v-if="value(field)" class="bpf__preview" :src="value(field)" alt="" />
      </div>

      <!-- features (repeatable icon/title/description) -->
      <div v-else-if="field.type === 'features'" class="bpf__features">
        <div
          v-for="(row, idx) in featureRows(field)"
          :key="idx"
          class="bpf__feature-row"
        >
          <input
            class="bpf__input bpf__input--icon"
            placeholder="icon (zap)"
            :value="row.icon"
            @input="updateFeature(field, idx, 'icon', $event.target.value)"
          />
          <input
            class="bpf__input"
            placeholder="\u0639\u0646\u0648\u0627\u0646"
            :value="row.title"
            @input="updateFeature(field, idx, 'title', $event.target.value)"
          />
          <input
            class="bpf__input"
            placeholder="\u062a\u0648\u0636\u06cc\u062d"
            :value="row.description"
            @input="updateFeature(field, idx, 'description', $event.target.value)"
          />
          <button type="button" class="bpf__icon-btn" @click="removeFeature(field, idx)">\u00d7</button>
        </div>
        <button type="button" class="bpf__add" @click="addFeature(field)">+ \u0627\u0641\u0632\u0648\u062f\u0646 \u0645\u0648\u0631\u062f</button>
      </div>

      <!-- text / link (default) -->
      <input
        v-else
        class="bpf__input"
        type="text"
        :value="value(field)"
        @input="set(field, $event.target.value)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getBlockType } from '@/utils/blockRegistry'

const props = defineProps({
  block: { type: Object, required: true },
})

const emit = defineEmits(['update'])

const def = computed(() => getBlockType(props.block?.type))
const fields = computed(() => (def.value?.props || []))

function value(field) {
  const p = props.block?.props || {}
  const v = p[field.key]
  return v === undefined ? field.default : v
}

function set(field, val) {
  emit('update', { ...(props.block.props || {}), [field.key]: val })
}

function featureRows(field) {
  const rows = value(field)
  return Array.isArray(rows) ? rows : []
}

function addFeature(field) {
  const rows = [...featureRows(field), { icon: 'sparkles', title: '', description: '' }]
  set(field, rows)
}

function removeFeature(field, idx) {
  const rows = featureRows(field).slice()
  rows.splice(idx, 1)
  set(field, rows)
}

function updateFeature(field, idx, key, val) {
  const rows = featureRows(field).map((row, i) => (i === idx ? { ...row, [key]: val } : row))
  set(field, rows)
}
</script>

<style scoped>
.bpf {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.bpf__field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.bpf__label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary, #2a211b);
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.bpf__help {
  font-weight: 400;
  font-size: 0.72rem;
  color: var(--text-muted, #8a7867);
}

.bpf__input {
  width: 100%;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  border: 1px solid var(--border, #ddd0c2);
  background: #fff;
  font: inherit;
  font-size: 0.85rem;
  color: inherit;
}

.bpf__textarea {
  min-height: 84px;
  resize: vertical;
}

.bpf__check {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
}

.bpf__image {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bpf__preview {
  width: 100%;
  max-height: 120px;
  object-fit: cover;
  border-radius: 10px;
}

.bpf__features {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bpf__feature-row {
  display: grid;
  grid-template-columns: 90px 1fr 1.4fr auto;
  gap: 0.4rem;
  align-items: center;
}

.bpf__input--icon {
  text-align: center;
}

.bpf__icon-btn {
  border: 0;
  cursor: pointer;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: #f3e7e0;
  color: #b84f4f;
  font-size: 1.1rem;
  line-height: 1;
}

.bpf__add {
  align-self: flex-start;
  border: 1px dashed var(--border, #ddd0c2);
  background: transparent;
  cursor: pointer;
  padding: 0.45rem 0.9rem;
  border-radius: 10px;
  font: inherit;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary, #2a211b);
}
</style>
