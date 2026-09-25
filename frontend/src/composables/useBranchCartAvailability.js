import { computed, ref, unref, watch } from 'vue'
import { cartState, removeLine } from '@/stores/cartStore'
import { checkCartBranchAvailability } from '@/utils/api'

export function useBranchCartAvailability(branchSource, options = {}) {
  const status = ref('idle')
  const unavailableItems = ref([])
  const error = ref('')
  const branch = computed(() => {
    const value = typeof branchSource === 'function' ? branchSource() : unref(branchSource)
    return String(value || '').trim()
  })
  const cartSignature = computed(() => cartState.lines.map((line) => `${line.id}:${line.item_slug}:${line.qty}`).join('|'))
  let requestId = 0

  async function verify() {
    const currentRequest = ++requestId
    const selectedBranch = branch.value
    const lines = [...cartState.lines]
    error.value = ''
    unavailableItems.value = []
    if (!selectedBranch) {
      status.value = 'idle'
      return false
    }
    if (!lines.length) {
      status.value = 'available'
      return true
    }

    status.value = 'checking'
    try {
      const result = await checkCartBranchAvailability({
        branch: selectedBranch,
        items: lines.map((line) => ({ id: line.id, item_slug: line.item_slug, item_title: line.item_title, qty: line.qty })),
      })
      if (currentRequest !== requestId) return false
      unavailableItems.value = Array.isArray(result?.unavailable_items) ? result.unavailable_items : []
      status.value = result?.available && !unavailableItems.value.length ? 'available' : 'unavailable'
      return status.value === 'available'
    } catch (err) {
      if (currentRequest !== requestId) return false
      status.value = 'error'
      error.value = err?.message || 'بررسی موجودی اقلام در این شعبه انجام نشد.'
      return false
    }
  }

  function removeUnavailable() {
    const ids = new Set(unavailableItems.value.map((row) => String(row.id || '')).filter(Boolean))
    ids.forEach((id) => removeLine(id))
    return verify()
  }

  if (options.watch !== false) watch([branch, cartSignature], verify, { immediate: options.immediate !== false })

  return {
    branch,
    status,
    unavailableItems,
    error,
    verify,
    removeUnavailable,
  }
}
