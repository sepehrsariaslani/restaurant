const META_PREFIX = '<!--faq_meta:'
const META_SUFFIX = '-->'

function normalizeMeta(meta = {}) {
  return {
    category: String(meta?.category || '').trim(),
    icon: String(meta?.icon || '').trim(),
    image: String(meta?.image || '').trim(),
    summary: String(meta?.summary || '').trim(),
  }
}

function hasMetaValues(meta = {}) {
  return Boolean(meta.category || meta.icon || meta.image || meta.summary)
}

export function parseFaqAnswer(rawAnswer = '') {
  const answerText = String(rawAnswer || '')
  if (!answerText.startsWith(META_PREFIX)) {
    return {
      answer: answerText.trim(),
      meta: normalizeMeta({}),
    }
  }

  const endIndex = answerText.indexOf(META_SUFFIX)
  if (endIndex < 0) {
    return {
      answer: answerText.trim(),
      meta: normalizeMeta({}),
    }
  }

  const rawMeta = answerText.slice(META_PREFIX.length, endIndex).trim()
  const rest = answerText.slice(endIndex + META_SUFFIX.length).trim()

  try {
    const parsed = JSON.parse(rawMeta)
    return {
      answer: rest,
      meta: normalizeMeta(parsed),
    }
  } catch (error) {
    return {
      answer: answerText.trim(),
      meta: normalizeMeta({}),
    }
  }
}

export function composeFaqAnswer(rawAnswer = '', rawMeta = {}) {
  const answer = String(rawAnswer || '').trim()
  const meta = normalizeMeta(rawMeta)
  if (!hasMetaValues(meta)) {
    return answer
  }
  return `${META_PREFIX}${JSON.stringify(meta)}${META_SUFFIX}\n${answer}`.trim()
}

export function normalizeFaqPublicRow(row = {}) {
  const parsed = parseFaqAnswer(row?.answer || '')
  return {
    ...row,
    question: String(row?.question || '').trim(),
    answer: parsed.answer,
    category: parsed.meta.category,
    icon: parsed.meta.icon,
    image: parsed.meta.image,
    summary: parsed.meta.summary,
    sort_order: Number(row?.sort_order || 0) || 0,
    is_active: Number(row?.is_active || 0) ? 1 : 0,
  }
}
