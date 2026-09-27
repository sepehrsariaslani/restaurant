export function surveyFeatureChoices(score) {
  const rating = Number(score) || 0
  if (rating >= 7) return ['نقطه قوت']
  if (rating > 0 && rating <= 3) return ['نیاز به بهبود']
  return ['نقطه قوت', 'نیاز به بهبود']
}

export function hasCustomerSurveyRating(serviceRating, feedback = {}, orderAnswers = {}, orderQuestions = []) {
  const hasOrderScore = orderQuestions.some(
    (question) => question.answer_type === 'امتیاز ۱ تا ۱۰' && Number(orderAnswers[question.name]) >= 1,
  )
  return Boolean(Number(serviceRating) || hasOrderScore || Object.values(feedback).some((entry) => !entry?.skipped && Number(entry?.score)))
}

export function buildCustomerSurveySubmission({
  survey,
  answers = {},
  feedback = {},
  serviceRating = 0,
  generalComment = '',
  token = '',
  invitation = '',
  edit = false,
} = {}) {
  const surveyAnswers = []
  for (const question of survey?.order_questions || []) {
    const value = answers[String(question.name)]
    if (value !== '' && value != null) surveyAnswers.push({ question: question.name, value })
  }

  const items = []
  for (const item of survey?.items || []) {
    const itemFeedback = feedback[item.order_item]
    if (itemFeedback?.skipped || !Number(itemFeedback?.score)) continue

    const strengths = []
    const weaknesses = []
    for (const question of item.questions || []) {
      const key = String(question.name) + '|' + item.order_item
      const value = answers[key]
      if (value === '' || value == null) continue
      surveyAnswers.push({ question: question.name, order_item: item.order_item, value })
      if (question.answer_type === 'ویژگی خوب/بد') {
        if (value === 'نقطه قوت') strengths.push(question.question)
        if (value === 'نیاز به بهبود') weaknesses.push(question.question)
      }
    }

    items.push({
      order_item: item.order_item,
      score_10: Number(itemFeedback.score),
      comment: itemFeedback.comment || '',
      strengths,
      weaknesses,
    })
  }

  return {
    token,
    invitation,
    edit: edit ? 1 : 0,
    items,
    answers: surveyAnswers,
    service_rating: Number(serviceRating) || 0,
    comment: generalComment || '',
  }
}
