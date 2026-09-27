<template>
  <section v-if="summary && (summary.can_request || summary.answered)" class="order-survey customer-glass-card" aria-label="بازخورد این سفارش">
    <header class="order-survey__header">
      <span class="order-survey__icon"><MessageCircle :size="18" aria-hidden="true" /></span>
      <div class="order-survey__heading">
        <h3>{{ summary.answered ? 'نظر شما برای این سفارش' : 'تجربهٔ این سفارش' }}</h3>
        <p>{{ summary.answered ? 'امتیازها و پاسخ‌های رستوران را اینجا ببینید.' : 'اگر فرصت کردید، تجربهٔ غذا و خدمات را با ما در میان بگذارید.' }}</p>
      </div>
      <span v-if="summary.answered" class="order-survey__state order-survey__state--done"><CheckCircle2 :size="14" /> ثبت‌شده</span>
    </header>

    <div v-if="summary.answered" class="order-survey__content">
      <div v-if="summary.service_rating" class="order-survey__service">
        <span>امتیاز خدمات</span>
        <strong>{{ formatNumber(summary.service_rating) }} <small>از ۱۰</small></strong>
      </div>
      <p v-if="summary.comment" class="order-survey__general">{{ summary.comment }}</p>

      <div v-if="summary.reviews?.length" class="order-survey__reviews">
        <article v-for="review in summary.reviews" :key="review.name" class="order-survey__review">
          <img v-if="review.image" :src="review.image" :alt="review.item_title" loading="lazy" />
          <span v-else class="order-survey__review-image"><Utensils :size="17" aria-hidden="true" /></span>
          <div class="order-survey__review-main">
            <div class="order-survey__review-title">
              <strong>{{ review.item_title }}</strong>
              <span class="order-survey__score">{{ formatNumber(review.score_10) }} از ۱۰</span>
            </div>
            <p v-if="review.comment" class="order-survey__review-comment">{{ review.comment }}</p>
            <div v-if="review.strengths?.length || review.weaknesses?.length" class="order-survey__traits">
              <span v-for="trait in review.strengths || []" :key="'good-' + trait" class="order-survey__trait order-survey__trait--good">{{ trait }}</span>
              <span v-for="trait in review.weaknesses || []" :key="'improve-' + trait" class="order-survey__trait order-survey__trait--improve">{{ trait }}</span>
            </div>
            <div class="order-survey__review-status" :class="{ 'is-approved': review.moderation_status === 'تأییدشده', 'is-rejected': review.moderation_status === 'ردشده' }">
              {{ review.moderation_status || 'در انتظار بررسی' }}
            </div>
            <blockquote v-if="review.manager_reply" class="order-survey__reply">
              <strong>پاسخ رستوران</strong>
              <span>{{ review.manager_reply }}</span>
            </blockquote>
          </div>
        </article>
      </div>
      <p v-else class="order-survey__empty">برای غذاهای این سفارش امتیازی ثبت نشده است.</p>
    </div>

    <footer class="order-survey__footer">
      <p v-if="summary.answered">می‌توانید نظر غذاها و امتیاز خدمات را ویرایش کنید.</p>
      <p v-else>ثبت نظر برای سفارش‌های تکمیل‌شده در دسترس است.</p>
      <a v-if="summary.answered && summary.invitation" class="order-survey__edit" :href="editHref">ویرایش نظرها</a>
      <button v-else-if="summary.can_request" class="order-survey__request" type="button" :disabled="requesting" @click="emit('request')">
        {{ requesting ? 'در حال آماده‌سازی…' : 'ثبت نظر این سفارش' }}
        <ChevronLeft :size="16" aria-hidden="true" />
      </button>
    </footer>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { CheckCircle2, ChevronLeft, MessageCircle, Utensils } from 'lucide-vue-next'

const props = defineProps({
  summary: { type: Object, default: null },
  requesting: { type: Boolean, default: false },
})
const emit = defineEmits(['request'])

const editHref = computed(() => `/survey?invitation=${encodeURIComponent(props.summary?.invitation || '')}&edit=1`)

function formatNumber(value) {
  return Number(value || 0).toLocaleString('fa-IR')
}
</script>

<style scoped>
.order-survey { display: grid; gap: .8rem; padding: .95rem; border-color: color-mix(in srgb, var(--ds-color-action-accent) 30%, var(--ds-color-border)); background: color-mix(in srgb, var(--ds-color-action-accent-soft) 38%, var(--ds-color-surface)); }
.order-survey__header { display: flex; align-items: center; gap: .65rem; min-width: 0; }
.order-survey__icon { display: grid; flex: 0 0 38px; width: 38px; height: 38px; place-items: center; border-radius: 13px; background: var(--ds-color-action-accent-soft); color: var(--ds-color-action-accent-foreground); }
.order-survey__heading { flex: 1; min-width: 0; }
.order-survey__heading h3 { margin: 0; color: var(--ds-color-text-primary); font-size: .88rem; }
.order-survey__heading p { margin: .18rem 0 0; color: var(--ds-color-text-muted); font-size: .73rem; line-height: 1.65; }
.order-survey__state { display: inline-flex; align-items: center; gap: .25rem; flex: 0 0 auto; padding: .32rem .52rem; border-radius: 999px; background: var(--ds-color-status-success-soft); color: var(--ds-color-status-success); font-size: .7rem; font-weight: 750; }
.order-survey__content { display: grid; gap: .6rem; }
.order-survey__service { display: flex; align-items: center; justify-content: space-between; gap: .75rem; padding: .55rem .7rem; border-radius: 12px; background: var(--ds-color-surface); color: var(--ds-color-text-secondary); font-size: .77rem; }
.order-survey__service strong { color: var(--ds-color-text-primary); }
.order-survey__service small { color: var(--ds-color-text-muted); font-size: .68rem; font-weight: 500; }
.order-survey__general, .order-survey__empty { margin: 0; color: var(--ds-color-text-secondary); font-size: .78rem; line-height: 1.8; }
.order-survey__reviews { display: grid; gap: .55rem; }
.order-survey__review { display: flex; gap: .6rem; padding: .65rem; border: 1px solid var(--ds-color-border); border-radius: 13px; background: var(--ds-color-surface); }
.order-survey__review > img, .order-survey__review-image { flex: 0 0 42px; width: 42px; height: 42px; border-radius: 12px; object-fit: cover; background: var(--ds-color-surface-muted); }
.order-survey__review-image { display: grid; place-items: center; color: var(--ds-color-action-primary); }
.order-survey__review-main { flex: 1; min-width: 0; }
.order-survey__review-title { display: flex; justify-content: space-between; align-items: flex-start; gap: .45rem; color: var(--ds-color-text-primary); font-size: .77rem; }
.order-survey__review-title strong { overflow-wrap: anywhere; }
.order-survey__score { flex: 0 0 auto; padding: .2rem .42rem; border-radius: 999px; background: var(--ds-color-action-accent-soft); color: var(--ds-color-text-primary); font-size: .68rem; font-weight: 800; }
.order-survey__review-comment { margin: .4rem 0 0; color: var(--ds-color-text-secondary); font-size: .75rem; line-height: 1.75; overflow-wrap: anywhere; }
.order-survey__traits { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .4rem; }
.order-survey__trait { padding: .18rem .42rem; border-radius: 999px; font-size: .67rem; }
.order-survey__trait--good { background: var(--ds-color-status-success-soft); color: var(--ds-color-status-success); }
.order-survey__trait--improve { background: var(--ds-color-status-warning-soft); color: var(--ds-color-text-secondary); }
.order-survey__review-status { margin-top: .4rem; color: var(--ds-color-text-muted); font-size: .67rem; }
.order-survey__review-status.is-approved { color: var(--ds-color-status-success); }
.order-survey__review-status.is-rejected { color: var(--ds-color-status-danger); }
.order-survey__reply { display: grid; gap: .2rem; margin: .5rem 0 0; padding: .55rem .65rem; border-inline-start: 3px solid var(--ds-color-action-accent); border-radius: 10px; background: var(--ds-color-surface-muted); color: var(--ds-color-text-secondary); font-size: .73rem; line-height: 1.7; }
.order-survey__reply strong { color: var(--ds-color-text-primary); }
.order-survey__footer { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: .55rem; padding-top: .65rem; border-top: 1px solid var(--ds-color-border); }
.order-survey__footer p { margin: 0; color: var(--ds-color-text-muted); font-size: .7rem; line-height: 1.6; }
.order-survey__edit, .order-survey__request { display: inline-flex; align-items: center; justify-content: center; gap: .25rem; min-height: 40px; padding: .45rem .7rem; border: 1px solid var(--ds-color-action-primary); border-radius: 12px; background: var(--ds-color-action-primary); color: var(--ds-color-action-primary-foreground); text-decoration: none; font: inherit; font-size: .74rem; font-weight: 800; cursor: pointer; }
.order-survey__request:disabled { opacity: .6; cursor: wait; }
@media (max-width: 520px) { .order-survey__header { align-items: flex-start; } .order-survey__state { font-size: .64rem; } .order-survey__footer { align-items: stretch; } .order-survey__footer p { flex-basis: 100%; } .order-survey__edit, .order-survey__request { width: 100%; } }
</style>
