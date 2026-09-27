import test from 'node:test'
import assert from 'node:assert/strict'
import {
  buildCustomerSurveySubmission,
  hasCustomerSurveyRating,
  surveyFeatureChoices,
} from '../src/utils/customerSurvey.js'

test('survey score bands expose only suitable strength and improvement choices', () => {
  assert.deepEqual(surveyFeatureChoices(10), ['نقطه قوت'])
  assert.deepEqual(surveyFeatureChoices(7), ['نقطه قوت'])
  assert.deepEqual(surveyFeatureChoices(3), ['نیاز به بهبود'])
  assert.deepEqual(surveyFeatureChoices(1), ['نیاز به بهبود'])
  assert.deepEqual(surveyFeatureChoices(4), ['نقطه قوت', 'نیاز به بهبود'])
  assert.deepEqual(surveyFeatureChoices(6), ['نقطه قوت', 'نیاز به بهبود'])
})

test('one response can rate products and service while skipping untried items', () => {
  const payload = buildCustomerSurveySubmission({
    survey: {
      order_questions: [{ name: 'Q-ORDER', answer_type: 'متن آزاد' }],
      items: [
        {
          order_item: 'SOI-1',
          questions: [
            { name: 'Q-TASTE', question: 'طعم', answer_type: 'ویژگی خوب/بد' },
            { name: 'Q-TEXT', question: 'یادداشت', answer_type: 'متن آزاد' },
          ],
        },
        { order_item: 'SOI-2', questions: [] },
      ],
    },
    answers: {
      'Q-ORDER': 'تحویل به‌موقع بود',
      'Q-TASTE|SOI-1': 'نقطه قوت',
      'Q-TEXT|SOI-1': 'تازه بود',
    },
    feedback: {
      'SOI-1': { score: 9, comment: 'خوش‌طعم', skipped: false },
      'SOI-2': { score: 0, comment: '', skipped: true },
    },
    serviceRating: 8,
    generalComment: 'سپاس',
    token: 'private-link-token',
  })

  assert.equal(payload.token, 'private-link-token')
  assert.equal(payload.service_rating, 8)
  assert.equal(payload.comment, 'سپاس')
  assert.deepEqual(payload.items, [{
    order_item: 'SOI-1',
    score_10: 9,
    comment: 'خوش‌طعم',
    strengths: ['طعم'],
    weaknesses: [],
  }])
  assert.deepEqual(payload.answers, [
    { question: 'Q-ORDER', value: 'تحویل به‌موقع بود' },
    { question: 'Q-TASTE', order_item: 'SOI-1', value: 'نقطه قوت' },
    { question: 'Q-TEXT', order_item: 'SOI-1', value: 'تازه بود' },
  ])
})

test('a review needs at least one product or service score', () => {
  assert.equal(hasCustomerSurveyRating(0, { skipped: { skipped: true, score: 0 } }), false)
  assert.equal(hasCustomerSurveyRating(6, {}), true)
  assert.equal(hasCustomerSurveyRating(0, { rated: { score: 1, skipped: false } }), true)
  assert.equal(hasCustomerSurveyRating(0, { skipped: { score: 10, skipped: true } }), false)
  assert.equal(hasCustomerSurveyRating(0, {}, { 'Q-RATING': 8 }, [{ name: 'Q-RATING', answer_type: 'امتیاز ۱ تا ۱۰' }]), true)
})

test('editing submits through the same verified invitation with an explicit edit flag', () => {
  const payload = buildCustomerSurveySubmission({
    survey: { order_questions: [], items: [{ order_item: 'SOI-1', questions: [] }] },
    feedback: { 'SOI-1': { score: 8, comment: 'تازه بود', skipped: false } },
    invitation: 'RSI-1',
    edit: true,
  })

  assert.equal(payload.invitation, 'RSI-1')
  assert.equal(payload.edit, 1)
  assert.equal(payload.items[0].score_10, 8)
})
