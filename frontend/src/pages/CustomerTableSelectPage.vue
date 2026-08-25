<template>
  <div class="table-select-page" dir="rtl">
    <div class="page-header">
      <button class="back-btn" @click="goBack">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
      </button>
      <h1 class="page-title">انتخاب میز</h1>
      <div style="width:40px"></div>
    </div>

    <!-- Area Tabs -->
    <div class="area-tabs">
      <button
        v-for="area in areas"
        :key="area.id"
        class="area-tab"
        :class="{ active: selectedArea === area.id }"
        @click="selectedArea = area.id"
      >
        {{ area.name }}
      </button>
    </div>

    <!-- Legend -->
    <div class="legend-row">
      <span class="legend-item"><i class="dot available"></i>خالی</span>
      <span class="legend-item"><i class="dot reserved"></i>رزرو شده</span>
      <span class="legend-item"><i class="dot occupied"></i>اشغال</span>
      <span class="legend-item"><i class="dot selected"></i>انتخاب شما</span>
    </div>

    <!-- Table Map -->
    <div class="floor-plan" @click.self="selectedTable = null">
      <div class="floor-bg">
        <div class="area-label">{{ currentArea?.name }}</div>

        <!-- Tables positioned in floor plan -->
        <div class="tables-grid">
          <div
            v-for="table in filteredTables"
            :key="table.id"
            class="table-box"
            :class="[table.status, { 'is-selected': selectedTable?.id === table.id }]"
            @click="selectTable(table)"
          >
            <div class="table-shape" :class="`shape-${table.shape}`">
              <span class="table-label">{{ table.label }}</span>
              <span class="table-cap">{{ table.capacity }}👤</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Selected Table Info -->
    <div class="selection-info" v-if="selectedTable">
      <div class="sel-details">
        <span class="sel-name">{{ selectedTable.label }}</span>
        <span class="sel-cap">{{ selectedTable.capacity }} نفره</span>
        <span class="sel-area">{{ currentArea?.name }}</span>
      </div>
      <button class="confirm-btn" @click="confirmTable">تأیید این میز</button>
    </div>
    <div class="selection-info empty-sel" v-else>
      <span>برای انتخاب روی میز خالی کلیک کنید</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const areas = [
  { id: 'indoor', name: 'سالن داخلی' },
  { id: 'terrace', name: 'تراس' },
  { id: 'vip', name: 'VIP' },
]

const selectedArea = ref('indoor')
const selectedTable = ref(null)

const tables = [
  { id: 1, label: 'میز ۱', capacity: 2, shape: 'round', status: 'available', area: 'indoor' },
  { id: 2, label: 'میز ۲', capacity: 4, shape: 'rect', status: 'occupied', area: 'indoor' },
  { id: 3, label: 'میز ۳', capacity: 4, shape: 'rect', status: 'available', area: 'indoor' },
  { id: 4, label: 'میز ۴', capacity: 6, shape: 'rect', status: 'reserved', area: 'indoor' },
  { id: 5, label: 'میز ۵', capacity: 2, shape: 'round', status: 'available', area: 'indoor' },
  { id: 6, label: 'میز ۶', capacity: 2, shape: 'round', status: 'available', area: 'indoor' },
  { id: 7, label: 'میز ۷', capacity: 4, shape: 'rect', status: 'occupied', area: 'indoor' },
  { id: 8, label: 'میز ۸', capacity: 8, shape: 'wide', status: 'available', area: 'indoor' },
  { id: 9, label: 'T-۱', capacity: 2, shape: 'round', status: 'available', area: 'terrace' },
  { id: 10, label: 'T-۲', capacity: 4, shape: 'rect', status: 'available', area: 'terrace' },
  { id: 11, label: 'T-۳', capacity: 4, shape: 'rect', status: 'reserved', area: 'terrace' },
  { id: 12, label: 'T-۴', capacity: 6, shape: 'rect', status: 'available', area: 'terrace' },
  { id: 13, label: 'VIP-۱', capacity: 6, shape: 'wide', status: 'available', area: 'vip' },
  { id: 14, label: 'VIP-۲', capacity: 8, shape: 'wide', status: 'reserved', area: 'vip' },
  { id: 15, label: 'VIP-۳', capacity: 10, shape: 'wide', status: 'available', area: 'vip' },
]

const filteredTables = computed(() => tables.filter(t => t.area === selectedArea.value))
const currentArea = computed(() => areas.find(a => a.id === selectedArea.value))

function selectTable(table) {
  if (table.status !== 'available') return
  selectedTable.value = table
}

function confirmTable() {
  if (!selectedTable.value) return
  try { localStorage.setItem('selected_table', JSON.stringify(selectedTable.value)) } catch {}
  window.history.back()
}

function goBack() { window.history.back() }
</script>

<style scoped>
.table-select-page { min-height: 100vh; background: #f7f0e8; direction: rtl; display: flex; flex-direction: column; }

.page-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 3.5rem 1rem 1rem; background: #fff; border-bottom: 1px solid #ede3d8;
}
.back-btn { width: 40px; height: 40px; border-radius: 50%; background: #f7f0e8; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #3f2a1d; }
.page-title { font-size: 1.1rem; font-weight: 800; color: #3f2a1d; margin: 0; }

.area-tabs {
  display: flex; gap: 0.5rem; padding: 0.75rem 1rem;
  background: #fff; border-bottom: 1px solid #ede3d8; overflow-x: auto; scrollbar-width: none;
}
.area-tabs::-webkit-scrollbar { display: none; }
.area-tab {
  padding: 0.5rem 1.1rem; border-radius: 999px; border: 1.5px solid #e5ddd4;
  background: #fdf8f1; color: #846b58; font-size: 0.85rem; font-weight: 700;
  font-family: inherit; cursor: pointer; white-space: nowrap; transition: all 0.2s;
}
.area-tab.active { background: #6f4a31; border-color: #6f4a31; color: #fff; }

.legend-row {
  display: flex; gap: 1rem; padding: 0.75rem 1rem;
  background: rgba(247,240,232,0.9); border-bottom: 1px solid #ede3d8;
  overflow-x: auto; scrollbar-width: none;
}
.legend-row::-webkit-scrollbar { display: none; }
.legend-item { display: flex; align-items: center; gap: 0.35rem; font-size: 0.72rem; color: #846b58; white-space: nowrap; }
.dot { width: 14px; height: 14px; border-radius: 4px; display: inline-block; }
.dot.available { background: #c8e6c9; border: 1px solid #4caf50; }
.dot.reserved { background: #fff9c4; border: 1px solid #fbc02d; }
.dot.occupied { background: #ffcdd2; border: 1px solid #e53935; }
.dot.selected { background: #6f4a31; border: 1px solid #3f2a1d; }

.floor-plan { flex: 1; overflow: auto; padding: 1rem; padding-bottom: 6rem; }

.floor-bg {
  background: #fff; border-radius: 24px; padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08); min-height: 400px; position: relative;
}

.area-label {
  text-align: center; font-size: 0.8rem; font-weight: 700; color: #c5b09a;
  text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.5rem;
}

.tables-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;
}

.table-box { cursor: pointer; }
.table-box.occupied, .table-box.reserved { cursor: not-allowed; }

.table-shape {
  border-radius: 12px; padding: 0.9rem 0.5rem;
  display: flex; flex-direction: column; align-items: center; gap: 0.3rem;
  border: 2px solid transparent; transition: all 0.2s;
}
.shape-round { border-radius: 50%; aspect-ratio: 1; padding: 0.7rem; }
.shape-wide { grid-column: span 2; border-radius: 14px; }

.table-box.available .table-shape { background: #e8f5e9; border-color: #4caf50; }
.table-box.reserved .table-shape { background: #fff9c4; border-color: #fbc02d; opacity: 0.75; }
.table-box.occupied .table-shape { background: #ffcdd2; border-color: #e53935; opacity: 0.75; }
.table-box.is-selected .table-shape { background: #6f4a31; border-color: #3f2a1d; }
.table-box.is-selected .table-label, .table-box.is-selected .table-cap { color: #fff; }

.table-label { font-size: 0.75rem; font-weight: 800; color: #3f2a1d; text-align: center; }
.table-cap { font-size: 0.65rem; color: #846b58; }
.table-box.available:hover .table-shape { transform: scale(1.05); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }

.selection-info {
  position: fixed; bottom: 0; left: 0; right: 0;
  background: #fff; border-top: 1px solid #ede3d8;
  padding: 0.9rem 1.25rem; display: flex; align-items: center; gap: 1rem;
  box-shadow: 0 -4px 20px rgba(0,0,0,0.08);
}
.selection-info.empty-sel { justify-content: center; color: #b0997f; font-size: 0.88rem; }
.sel-details { flex: 1; display: flex; align-items: center; gap: 0.6rem; }
.sel-name { font-size: 0.95rem; font-weight: 800; color: #3f2a1d; }
.sel-cap, .sel-area { font-size: 0.75rem; color: #846b58; background: #f1e7db; border-radius: 999px; padding: 2px 8px; }
.confirm-btn { background: #6f4a31; color: #fff; border: none; border-radius: 14px; padding: 0.75rem 1.4rem; font-size: 0.9rem; font-weight: 700; font-family: inherit; cursor: pointer; flex-shrink: 0; }
</style>
