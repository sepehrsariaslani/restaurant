with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    content = f.read()

# Make search include item details
search_computed = """const shown = computed(() => {
  let l = orders.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    l = l.filter(o => {
      const matchMeta = String(o.order_code || '').toLowerCase().includes(q) || 
                        String(o.customer_name || '').toLowerCase().includes(q) ||
                        String(o.channel || '').toLowerCase().includes(q);
      const matchItems = (o.items || []).some(it => 
        String(it.title || it.item_name || '').toLowerCase().includes(q) ||
        String(it.note || '').toLowerCase().includes(q)
      );
      return matchMeta || matchItems;
    })
  }
  return l
})"""

content = content.replace("""const shown = computed(() => {
  let l = orders.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    l = l.filter(o => 
      String(o.order_code || '').toLowerCase().includes(q) || 
      String(o.customer_name || '').toLowerCase().includes(q) ||
      String(o.channel || '').toLowerCase().includes(q)
    )
  }
  return l
})""", search_computed)

# Prevent race condition between optimistic update and polling
# We add a ref to track currently modifying order IDs
state_add = """const searchQuery = ref('')
const filterStatus = ref('') // desktop filter
const mobileTab = ref('new') // mobile tab filter
const dateFilter = ref(getLocalTodayDate())
const nowTick = ref(Date.now())
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)

// Prevent race conditions
const inFlightMutations = ref(new Set())"""

content = content.replace("""const searchQuery = ref('')
const filterStatus = ref('') // desktop filter
const mobileTab = ref('new') // mobile tab filter
const dateFilter = ref(getLocalTodayDate())
const nowTick = ref(Date.now())
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)""", state_add)

fetch_update = """  try {
    const res = await callRestaurantAPI('get_kitchen_display_orders', { limit: 100, date: dateFilter.value })
    let newOrders = res.orders || []
    
    // Protect optimistic updates: keep local status if order is currently being mutated
    if (inFlightMutations.value.size > 0) {
      newOrders = newOrders.map(no => {
        if (inFlightMutations.value.has(no.name)) {
          const localOrder = orders.value.find(lo => lo.name === no.name)
          if (localOrder) no.status = localOrder.status
        }
        return no
      })
    }"""

content = content.replace("""  try {
    const res = await callRestaurantAPI('get_kitchen_display_orders', { limit: 100, date: dateFilter.value })
    const newOrders = res.orders || []""", fetch_update)


optimistic_update = """async function _updateOrderStatus(order, nextStatus) {
  const originalStatus = order.status
  // Optimistic update
  order.status = nextStatus
  inFlightMutations.value.add(order.name)
  
  try {
    await callRestaurantAPI('update_kitchen_order_status', {
      order_name: order.name,
      status: nextStatus
    })
    inFlightMutations.value.delete(order.name)
  } catch (e) {
    // Rollback
    inFlightMutations.value.delete(order.name)
    order.status = originalStatus
    errorMsg.value = e.message || 'خطا در تغییر وضعیت'
    setTimeout(() => { errorMsg.value = '' }, 3000)
  }
}"""

content = content.replace("""async function _updateOrderStatus(order, nextStatus) {
  const originalStatus = order.status
  // Optimistic update
  order.status = nextStatus
  
  try {
    await callRestaurantAPI('update_kitchen_order_status', {
      order_name: order.name,
      status: nextStatus
    })
  } catch (e) {
    // Rollback
    order.status = originalStatus
    errorMsg.value = e.message || 'خطا در تغییر وضعیت'
    setTimeout(() => { errorMsg.value = '' }, 3000)
  }
}""", optimistic_update)

# Fix event listener leak: making handlers named and ensuring cleanup
on_mount_listeners = """  if (typeof window !== 'undefined') {
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('resize', handleResize)
  }
})

function handleOnline() { isOnline.value = true; if (isToday.value) fetchOrders() }
function handleOffline() { isOnline.value = false }
function handleVisibilityChange() { if (document.visibilityState === 'visible' && isToday.value) fetchOrders() }
function handleResize() { windowWidth.value = window.innerWidth }

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (typeof window !== 'undefined') {
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    window.removeEventListener('resize', handleResize)
  }
})"""

content = content.replace("""  if (typeof window !== 'undefined') {
    window.addEventListener('online', () => { isOnline.value = true; if (isToday.value) fetchOrders() })
    window.addEventListener('offline', () => { isOnline.value = false })
    
    visibilityHandler = () => {
      if (document.visibilityState === 'visible' && isToday.value) fetchOrders()
    }
    document.addEventListener('visibilitychange', visibilityHandler)
    
    resizeHandler = () => { windowWidth.value = window.innerWidth }
    window.addEventListener('resize', resizeHandler)
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (clockTimer) clearInterval(clockTimer)
  if (typeof window !== 'undefined') {
    if (visibilityHandler) document.removeEventListener('visibilitychange', visibilityHandler)
    if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  }
})""", on_mount_listeners)

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'w') as f:
    f.write(content)

print("Frontend fixes applied.")
