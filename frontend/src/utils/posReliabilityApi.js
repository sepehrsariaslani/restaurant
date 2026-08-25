import { callMethodByPath } from './api'

export function getReliablePOSBoot({ branch = '' } = {}) {
  return callMethodByPath('restaurant.api_pos_reliability.get_management_pos_boot_reliable', { branch })
}

export function replayOfflinePOSOrder(payload = {}) {
  return callMethodByPath('restaurant.api_pos_reliability.replay_offline_pos_order', { payload })
}

export function updatePOSProductAtomic(payload = {}) {
  return callMethodByPath('restaurant.api_pos_reliability.update_pos_product_atomic', { payload })
}
