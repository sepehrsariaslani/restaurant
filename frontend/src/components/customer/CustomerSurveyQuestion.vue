<template>
  <fieldset class="survey-question">
    <legend>{{ question.question }}</legend>
    <div v-if="question.answer_type === 'امتیاز ۱ تا ۱۰'" class="survey-question__score" role="radiogroup" :aria-label="question.question">
      <label v-for="score in 10" :key="score" class="survey-question__score-choice" :class="{ selected: Number(modelValue) === score }">
        <input
          type="radio"
          :name="groupName"
          :value="score"
          :checked="Number(modelValue) === score"
          @change="update(score)"
        />
        <span>{{ score.toLocaleString('fa-IR') }}</span>
      </label>
    </div>
    <div v-else-if="question.answer_type === 'بله/خیر'" class="survey-question__choices">
      <button v-for="choice in yesNoChoices" :key="choice" type="button" class="survey-question__choice" :class="{ selected: modelValue === choice }" :aria-pressed="modelValue === choice" @click="update(choice)">
        {{ choice }}
      </button>
    </div>
    <div v-else-if="question.answer_type === 'ویژگی خوب/بد'" class="survey-question__choices">
      <button
        v-for="choice in featureChoices"
        :key="choice"
        type="button"
        class="survey-question__choice"
        :class="[{ selected: modelValue === choice }, choice === 'نقطه قوت' ? 'is-positive' : 'is-improvement']"
        :aria-pressed="modelValue === choice"
        @click="update(modelValue === choice ? '' : choice)"
      >
        {{ choice === 'نقطه قوت' ? 'خوب بود' : 'نیاز به بهبود' }}
      </button>
    </div>
    <textarea
      v-else
      class="survey-question__textarea"
      :value="modelValue || ''"
      rows="2"
      maxlength="500"
      :aria-label="question.question"
      placeholder="پاسخ شما (اختیاری)"
      @input="update($event.target.value)"
    ></textarea>
  </fieldset>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  question: { type: Object, required: true },
  modelValue: { type: [String, Number], default: '' },
  groupName: { type: String, required: true },
  featureChoices: { type: Array, default: () => ['نقطه قوت', 'نیاز به بهبود'] },
})
const emit = defineEmits(['update:modelValue'])
const yesNoChoices = computed(() => ['بله', 'خیر'])
function update(value) {
  emit('update:modelValue', value)
}
</script>

<style scoped>
.survey-question { min-width: 0; margin: 0; padding: .75rem 0 0; border: 0; border-top: 1px solid var(--ds-color-border); }
.survey-question legend { margin-bottom: .55rem; color: var(--ds-color-text-secondary); font-size: .83rem; font-weight: 750; line-height: 1.65; }
.survey-question__score { display: grid; grid-template-columns: repeat(10, minmax(0, 1fr)); gap: .3rem; }
.survey-question__score-choice { position: relative; display: grid; min-height: 40px; place-items: center; border: 1px solid var(--ds-color-border); border-radius: 10px; color: var(--ds-color-text-secondary); font-size: .75rem; font-weight: 750; cursor: pointer; }
.survey-question__score-choice input { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0; cursor: pointer; }
.survey-question__score-choice:has(input:focus-visible) { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
.survey-question__score-choice.selected { border-color: var(--ds-color-action-accent); background: var(--ds-color-action-accent-soft); color: var(--ds-color-text-primary); }
.survey-question__choices { display: flex; flex-wrap: wrap; gap: .45rem; }
.survey-question__choice { min-height: 42px; padding: .5rem .85rem; border: 1px solid var(--ds-color-border); border-radius: 999px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font: inherit; font-size: .8rem; font-weight: 700; cursor: pointer; }
.survey-question__choice.selected { border-color: var(--ds-color-action-primary); background: var(--ds-color-action-primary-soft); color: var(--ds-color-action-primary); }
.survey-question__choice.is-improvement.selected { border-color: var(--ds-color-status-warning); background: var(--ds-color-status-warning-soft); color: var(--ds-color-status-warning); }
.survey-question__textarea { width: 100%; box-sizing: border-box; resize: vertical; border: 1px solid var(--ds-color-border); border-radius: 12px; padding: .65rem .75rem; background: var(--ds-color-surface); color: var(--ds-color-text-primary); font: inherit; font-size: .85rem; }
.survey-question__textarea:focus-visible { outline: 3px solid var(--ds-color-focus-ring); outline-offset: 2px; }
@media (max-width: 420px) {
  .survey-question__score { gap: .2rem; }
  .survey-question__score-choice { min-height: 36px; border-radius: 8px; font-size: .68rem; }
}
</style>
