function errorMessage(error) {
  return String(error?.message || error?.exc || error || 'خطای نامشخص').trim()
}

function defaultBusinessError(error) {
  const status = Number(error?.status || error?.statusCode || error?.httpStatus || 0)
  if ([400, 409, 422].includes(status)) return true
  return /validation|invalid|price|stock|موجودی|قیمت|اعتبارسنجی/i.test(errorMessage(error))
}

export function createOfflineSyncEngine({
  store,
  replayOrder,
  isOnline = () => true,
  isBusinessError = defaultBusinessError,
} = {}) {
  let inFlight = null

  async function runSequentially() {
    const result = { synced: 0, pending: 0, needsAttention: 0, skipped: false }
    if (!isOnline() || !store || typeof replayOrder !== 'function') {
      result.skipped = true
      return result
    }

    const records = await store.listPendingOfflineOrders()
    const ordered = [...(Array.isArray(records) ? records : [])]
      .sort((left, right) => Number(left?.created_at || 0) - Number(right?.created_at || 0))

    for (const record of ordered) {
      if (!isOnline()) {
        result.skipped = true
        break
      }
      const id = String(record?.id || '').trim()
      if (!id) continue
      try {
        const response = await replayOrder({ ...(record.payload || {}), client_order_key: id })
        const status = String(response?.status || '').toLowerCase()
        if (status !== 'created' && status !== 'existing') {
          throw { status: 422, message: response?.message || 'پاسخ نامعتبر از سرور' }
        }
        await store.markOfflineOrderSynced(id)
        result.synced += 1
      } catch (error) {
        const message = errorMessage(error)
        if (isBusinessError(error)) {
          await store.markOfflineOrderNeedsAttention(id, message)
          result.needsAttention += 1
        } else {
          await store.markOfflineOrderPending(id, message)
          result.pending += 1
        }
      }
    }
    return result
  }

  function syncPendingOrders() {
    if (!inFlight) {
      inFlight = runSequentially().finally(() => { inFlight = null })
    }
    return inFlight
  }

  return { syncPendingOrders, isSyncing: () => Boolean(inFlight) }
}
