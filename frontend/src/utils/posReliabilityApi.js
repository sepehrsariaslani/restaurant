import { callMethodByPath } from './api'

export function getReliablePOSBoot({ branch = '' } = {}) {
  return callMethodByPath('restaurant.api_pos_background.get_management_pos_boot_safe', { branch })
}

export function listManagementProductsSafe({
  search = '',
  category = '',
  active_only = 0,
  branch = '',
  tag = '',
} = {}) {
  return callMethodByPath('restaurant.api_management_products_safe.list_management_products_safe', {
    search,
    category,
    active_only,
    branch,
    tag,
  })
}

export function replayOfflinePOSOrder(payload = {}) {
  return callMethodByPath('restaurant.api_pos_reliability.replay_offline_pos_order', { payload })
}

export function updatePOSProductAtomic(payload = {}) {
  return callMethodByPath('restaurant.api_pos_reliability.update_pos_product_atomic', { payload })
}

export function enqueuePOSBackgroundCheckout(payload = {}, deliver_after = false) {
  return callMethodByPath('restaurant.api_pos_background.enqueue_pos_checkout', {
    payload,
    deliver_after: deliver_after ? 1 : 0,
  })
}

export function enqueuePOSBackgroundSettlement(order_name = '', payment = {}, deliver_after = false) {
  return callMethodByPath('restaurant.api_pos_background.enqueue_pos_settlement', {
    order_name,
    payment,
    deliver_after: deliver_after ? 1 : 0,
  })
}

export function getPOSBackgroundOperation(job_key = '') {
  return callMethodByPath('restaurant.api_pos_background.get_pos_background_operation', { job_key })
}
