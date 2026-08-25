import re

with open("frontend/src/pages/management/ManagementOrdersPage.vue", "r") as f:
    content = f.read()

# Make sure style is clean
style_block = content[content.find("<style scoped>"):content.rfind("</style>") + len("</style>")]

new_style = """<style scoped>
/* Workflow-based Operational Dashboard Styles */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.page-title {
  font-size: 2rem;
  font-weight: 900;
  color: var(--mg-text-main);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  color: var(--mg-text-muted);
  font-size: 1rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.search-box {
  position: relative;
  width: 320px;
}

.search-icon {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--mg-secondary);
}

.search-input {
  width: 100%;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0.85rem 1rem 0.85rem 2.5rem;
  color: var(--mg-text-main);
  font-size: 0.95rem;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: var(--mg-primary);
  outline: none;
  box-shadow: 0 0 0 3px var(--mg-danger-bg);
}

.refresh-btn {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  width: 3.2rem;
  height: 3.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mg-text-main);
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: var(--mg-bg-soft);
  color: var(--mg-primary);
}

/* KPI Strip */
.kpi-strip {
  display: flex;
  gap: 1rem;
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
}

.kpi-hero {
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 1.5rem 2.5rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border: 1px solid var(--mg-border-light);
  box-shadow: var(--mg-shadow-sm);
  min-width: 220px;
}

.kpi-hero-val {
  font-size: 3rem;
  font-weight: 900;
  color: var(--mg-text-main);
  line-height: 1;
}

.kpi-hero-label {
  font-size: 0.95rem;
  color: var(--mg-text-muted);
  margin-top: 0.5rem;
  font-weight: 700;
}

.kpi-tiles {
  display: flex;
  gap: 1rem;
  flex: 1;
  flex-wrap: wrap;
}

.kpi-tile {
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
  min-width: 140px;
  border: 1px solid var(--mg-border-light);
}

.kpi-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  margin-top: 0.4rem;
  flex-shrink: 0;
}

.kpi-dot.new { background: var(--mg-danger); } 
.kpi-dot.preparing { background: var(--mg-olive-soft); border: 1px solid var(--mg-olive); } 
.kpi-dot.ready { background: var(--mg-primary); }

.kpi-info {
  display: flex;
  flex-direction: column;
}

.kpi-val {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--mg-text-main);
  line-height: 1.1;
}

.kpi-label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 600;
  margin-top: 0.25rem;
}

.kpi-divider {
  width: 1px;
  background: var(--mg-border-light);
  margin: 0.5rem 0.5rem;
}

/* Tabs Container */
.workspace-tabs-container {
  display: flex;
  margin-bottom: 2rem;
}

.workspace-tabs {
  display: inline-flex;
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  padding: 0.35rem;
  gap: 0.25rem;
  border: 1px solid var(--mg-border-light);
  overflow-x: auto;
  max-width: 100%;
}

.workspace-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.25rem;
  border: none;
  background: transparent;
  color: var(--mg-text-muted);
  font-weight: 700;
  font-size: 0.95rem;
  cursor: pointer;
  border-radius: var(--mg-radius-sm);
  transition: all 0.2s ease;
  white-space: nowrap;
}

.workspace-tab:hover {
  color: var(--mg-text-main);
}

.workspace-tab.active {
  background: var(--mg-bg-page);
  color: var(--mg-primary);
  box-shadow: var(--mg-shadow-sm);
}

.tab-badge {
  background: var(--mg-border-light);
  color: var(--mg-text-main);
  padding: 0.15rem 0.6rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 800;
}

.workspace-tab.active .tab-badge {
  background: var(--mg-danger-bg);
  color: var(--mg-primary);
}

/* Floor Grid Area */
.workspace-floor {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 460px;
  gap: 2.5rem;
  align-items: start;
}

.floor-filters {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.floor-filter-label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 600;
  margin-left: 0.5rem;
}

.floor-chip {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-main);
  padding: 0.4rem 1rem;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.floor-chip:hover {
  border-color: var(--mg-border);
}

.floor-chip.active {
  background: var(--mg-text-main);
  border-color: var(--mg-text-main);
  color: var(--mg-bg-surface);
}
:global(.dark) .floor-chip.active {
  background: var(--mg-text-main);
  color: var(--mg-bg-surface);
}

/* Order List (Rows instead of cards) */
.order-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: calc(100vh - 4rem);
  overflow-y: auto;
  padding-right: 0.25rem;
}

.order-row {
  display: flex;
  flex-direction: column;
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: right;
  width: 100%;
}

.order-row:hover {
  border-color: var(--mg-border);
  transform: translateX(-3px);
  box-shadow: var(--mg-shadow-sm);
}

.order-row.is-selected {
  background: var(--mg-bg-soft);
  border-color: var(--mg-primary);
  box-shadow: 4px 0 0 0 var(--mg-primary) inset, var(--mg-shadow-sm);
}

.order-row-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.order-identity {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.order-identity strong {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--mg-text-main);
}

.customer-name {
  font-size: 0.9rem;
  color: var(--mg-text-muted);
  font-weight: 600;
}

.order-metrics {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.order-total {
  font-size: 1.15rem;
  font-weight: 900;
  color: var(--mg-primary);
}

.order-badges {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-badge, .payment-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 800;
  border: 1px solid transparent;
}

/* Status variants */
.status-new { background: var(--mg-danger-bg); color: var(--mg-danger); border-color: var(--mg-border-light); }
.status-confirmed, .status-preparing { background: rgba(221, 167, 123, 0.15); color: #8C5E35; border-color: rgba(221, 167, 123, 0.3); }
.status-ready { background: var(--mg-danger-bg); color: var(--mg-primary); border-color: var(--mg-primary); }
.status-delivered { background: var(--mg-bg-soft); color: var(--mg-text-muted); border-color: var(--mg-border-light); }
.status-cancelled { background: var(--mg-danger-bg); color: var(--mg-danger); border-color: var(--mg-border-light); }

:global(.dark) .status-confirmed, :global(.dark) .status-preparing { background: rgba(221, 167, 123, 0.1); color: #DDA77B; border-color: rgba(221, 167, 123, 0.2); }

/* Payment variants */
.pay-paid { background: rgba(110, 118, 74, 0.15); color: var(--mg-success); border-color: rgba(110, 118, 74, 0.3); }
.pay-unpaid { background: var(--mg-danger-bg); color: var(--mg-danger); border-color: var(--mg-border-light); }

:global(.dark) .pay-paid { background: rgba(110, 118, 74, 0.1); color: #88935C; }

.order-row-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--mg-secondary);
  border-top: 1px dashed var(--mg-border-light);
  padding-top: 0.75rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 600;
}

/* Detail Area */
.floor-detail-area {
  position: sticky;
  top: 2rem;
  height: calc(100vh - 4rem);
}

.inspection-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--mg-bg-surface);
  border-radius: var(--mg-radius-md);
  border: 1px solid var(--mg-border-light);
  box-shadow: var(--mg-shadow-md);
  overflow: hidden;
}

.inspection-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  text-align: center;
  color: var(--mg-secondary);
}

.empty-illustration {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: var(--mg-bg-page);
  margin-bottom: 1.5rem;
  color: var(--mg-secondary);
  border: 1px solid var(--mg-border-light);
}

.inspection-empty strong {
  color: var(--mg-text-main);
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
  font-weight: 800;
}

.inspection-empty p {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--mg-text-muted);
}

.inspection-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.75rem 2rem;
  border-bottom: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
}

.head-info {
  display: flex;
  flex-direction: column;
}

.head-kicker {
  font-size: 0.8rem;
  color: var(--mg-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 800;
  margin-bottom: 0.4rem;
}

.head-info h2 {
  margin: 0;
  font-size: 1.8rem;
  color: var(--mg-text-main);
  font-weight: 900;
  letter-spacing: -0.02em;
}

.head-location {
  font-size: 0.95rem;
  color: var(--mg-text-muted);
  margin-top: 0.25rem;
  font-weight: 600;
}

.inspection-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.kpi-box {
  background: var(--mg-bg-page);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.kpi-box.highlight {
  background: var(--mg-bg-surface);
  border-color: var(--mg-border);
}

.kpi-box.highlight .kpi-box-value {
  color: var(--mg-primary);
}

.kpi-box-label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 700;
}

.kpi-box-value {
  font-size: 1.3rem;
  color: var(--mg-text-main);
  font-weight: 900;
}

.text-danger { color: var(--mg-danger); }
.text-success { color: var(--mg-success); }

.inspection-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-title {
  margin: 0;
  font-size: 1.1rem;
  color: var(--mg-text-main);
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--mg-border-light);
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: var(--mg-bg-page);
  padding: 1rem;
  border-radius: var(--mg-radius-sm);
  border: 1px solid var(--mg-border-light);
}

.item-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 0.75rem;
  font-size: 0.95rem;
  color: var(--mg-text-main);
  font-weight: 600;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed var(--mg-border-light);
}
.item-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.item-qty { color: var(--mg-secondary); font-weight: 800; }
.item-price { color: var(--mg-primary); font-weight: 800; }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 0.85rem;
  color: var(--mg-text-muted);
  font-weight: 700;
}

.input {
  background: var(--mg-bg-page);
  border: 1px solid var(--mg-border-light);
  color: var(--mg-text-main);
  border-radius: var(--mg-radius-sm);
  padding: 0.75rem 1rem;
  font-family: inherit;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.input:focus {
  border-color: var(--mg-primary);
  outline: none;
}

.mt-4 { margin-top: 1rem; }

.inspection-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid var(--mg-border-light);
  background: var(--mg-bg-page);
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.flex-1 {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  height: 3.2rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.95rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
}

.primary-btn {
  background: var(--mg-primary);
  color: #fff;
}
.primary-btn:hover:not(:disabled) {
  background: var(--mg-primary-hover);
}
:global(.dark) .primary-btn { color: #1A130D; }

.secondary-btn {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border);
  color: var(--mg-text-main);
}
.secondary-btn:hover:not(:disabled) {
  background: var(--mg-bg-soft);
}

.ghost-btn {
  background: transparent;
  color: var(--mg-secondary);
}
.ghost-btn:hover {
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty / Alerts */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  background: var(--mg-bg-surface);
  border: 1px dashed var(--mg-border);
  border-radius: var(--mg-radius-md);
  color: var(--mg-secondary);
  text-align: center;
}
.empty-icon-wrapper {
  margin-bottom: 1.5rem;
  opacity: 0.6;
}
.empty-state strong {
  font-size: 1.2rem;
  color: var(--mg-text-main);
  margin-bottom: 0.5rem;
  font-weight: 800;
}
.empty-state p {
  font-size: 0.95rem;
  color: var(--mg-text-muted);
}

.workspace-alerts {
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.error-alert, .success-alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
}
.error-alert {
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
  border: 1px solid rgba(166, 84, 63, 0.2);
}
.success-alert {
  background: var(--mg-success-soft);
  color: var(--mg-success);
  border: 1px solid rgba(111, 123, 86, 0.25);
}
.muted-loading {
  color: var(--mg-secondary);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 2rem;
}

@media (max-width: 1200px) {
  .workspace-floor {
    grid-template-columns: 1fr;
  }
  .floor-detail-area {
    position: static;
    height: auto;
  }
}

@media (max-width: 768px) {
  .workspace-header {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box { width: 100%; }
  .header-actions {
    flex-wrap: wrap;
  }
  .refresh-btn { flex: 1; }
  .kpi-divider { display: none; }
  .kpi-tiles {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
  .kpi-hero {
    min-width: 100%;
    align-items: center;
  }
  .inspection-footer {
    flex-direction: column;
  }
}
</style>
"""

content = content.replace(style_block, new_style)

with open("frontend/src/pages/management/ManagementOrdersPage.vue", "w") as f:
    f.write(content)
print("Updated ManagementOrdersPage style block")
