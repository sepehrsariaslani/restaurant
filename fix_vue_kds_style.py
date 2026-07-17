import re

with open("frontend/src/pages/management/ManagementKitchenPage.vue", "r") as f:
    content = f.read()

# Make sure CSS is using actual earthy palette correctly
old_css = content[content.find("<style scoped>"):content.find("</style>") + len("</style>")]

new_css = """<style scoped>
/* Workflow-based KDS Dashboard */
.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.badge-kds {
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
  font-size: 0.8rem;
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  vertical-align: middle;
  margin-right: 0.25rem;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 900;
  color: var(--mg-text-main);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  color: var(--mg-text-muted);
  font-size: 0.95rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--mg-success-bg);
  color: var(--mg-success);
  padding: 0.4rem 0.85rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.85rem;
  font-weight: 700;
  border: 1px solid rgba(111, 123, 86, 0.2);
}
.live-indicator.offline {
  background: var(--mg-bg-surface);
  color: var(--mg-text-muted);
  border-color: var(--mg-border);
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: currentColor;
  border-radius: 50%;
  animation: pulse 2s infinite;
}
.offline .pulse-dot { animation: none; }

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.1); opacity: 1; box-shadow: 0 0 0 4px rgba(111, 123, 86, 0.2); }
  100% { transform: scale(0.95); opacity: 0.8; box-shadow: 0 0 0 0 rgba(111, 123, 86, 0); }
}

.search-box {
  position: relative;
  width: 260px;
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
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  color: var(--mg-text-main);
  font-size: 0.9rem;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: var(--mg-primary);
  outline: none;
}

.icon-btn, .refresh-btn {
  background: var(--mg-surface-alt);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-md);
  width: 2.8rem;
  height: 2.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--mg-text-main);
  cursor: pointer;
  transition: all 0.2s;
}
.icon-btn:hover, .refresh-btn:hover {
  background: var(--mg-bg-surface);
  color: var(--mg-primary);
}
.icon-btn.active {
  color: var(--mg-primary);
}

.is-spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }

/* KPI Strip */
.kpi-strip {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.kpi-tile {
  background: var(--mg-surface-alt);
  border-radius: var(--mg-radius-md);
  padding: 1rem 1.25rem;
  display: flex;
  align-items: flex-start;
  gap: 0.85rem;
  flex: 1;
  min-width: 130px;
  border: 1px solid var(--mg-border-light);
  text-align: right;
  cursor: pointer;
  transition: all 0.2s;
}

.kpi-tile:hover {
  border-color: var(--mg-border);
  transform: translateY(-2px);
}

.kpi-tile.active {
  background: var(--mg-bg-surface);
  border-color: var(--mg-primary);
  box-shadow: var(--mg-shadow-sm);
}

.kpi-tile.readonly {
  cursor: default;
}
.kpi-tile.readonly:hover {
  transform: none;
  border-color: var(--mg-border-light);
}

.kpi-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 0.5rem;
  flex-shrink: 0;
}

.kpi-dot.all { background: var(--mg-text-main); }
.kpi-dot.new { background: var(--mg-primary); } 
.kpi-dot.preparing { background: var(--mg-danger); } 
.kpi-dot.ready { background: var(--mg-success); }

.kpi-info {
  display: flex;
  flex-direction: column;
}

.kpi-val {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--mg-text-main);
  line-height: 1.1;
}

.kpi-label {
  font-size: 0.8rem;
  color: var(--mg-text-muted);
  font-weight: 700;
  margin-top: 0.25rem;
}

.text-sm { font-size: 0.85rem; }

.kpi-divider {
  width: 1px;
  background: var(--mg-border-light);
  margin: 0.5rem 0.5rem;
}

/* Empty / Alerts */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  background: var(--mg-surface-alt);
  border: 1px dashed var(--mg-border);
  border-radius: var(--mg-radius-md);
  color: var(--mg-secondary);
  text-align: center;
}
.empty-icon-wrapper {
  margin-bottom: 1.5rem;
  opacity: 0.8;
}
.success-icon { color: var(--mg-success); }

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
.secondary-btn {
  background: var(--mg-bg-surface);
  border: 1px solid var(--mg-border);
  color: var(--mg-text-main);
  padding: 0.6rem 1.2rem;
  border-radius: var(--mg-radius-sm);
  font-weight: 700;
  cursor: pointer;
  margin-top: 1rem;
}

.workspace-alerts {
  margin-bottom: 1.5rem;
}
.error-alert {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-radius: var(--mg-radius-sm);
  font-size: 0.95rem;
  font-weight: 700;
  margin: 0;
  background: var(--mg-danger-bg);
  color: var(--mg-danger);
  border: 1px solid rgba(166, 84, 63, 0.2);
}
.muted-loading {
  color: var(--mg-secondary);
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 2rem;
}

/* Board Layout */
.kds-board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.5rem;
  align-items: start;
}

.kds-column {
  display: flex;
  flex-direction: column;
  background: var(--mg-surface-alt);
  border-radius: var(--mg-radius-md);
  border: 1px solid var(--mg-border-light);
  height: calc(100vh - 200px);
}

.kds-col-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--mg-border-light);
  background: var(--mg-bg-surface);
  border-radius: 16px 16px 0 0;
}

.col-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.col-title h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--mg-text-main);
}
.col-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.col-dot.new { background: var(--mg-primary); }
.col-dot.preparing { background: var(--mg-danger); }
.col-dot.ready { background: var(--mg-success); }

.col-count {
  background: var(--mg-bg-page);
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--mg-text-muted);
  border: 1px solid var(--mg-border-light);
}

.kds-col-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

@media (max-width: 1024px) {
  .kds-board {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
  .kds-column {
    height: auto;
    max-height: 600px;
  }
}

@media (max-width: 768px) {
  .workspace-header {
    flex-direction: column;
    align-items: stretch;
  }
  .search-box { width: 100%; }
  .header-actions { flex-wrap: wrap; }
  .kpi-divider { display: none; }
  .kpi-tiles, .kpi-strip {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>"""

if old_css in content:
    content = content.replace(old_css, new_css)
    with open("frontend/src/pages/management/ManagementKitchenPage.vue", "w") as f:
        f.write(content)
    print("Fixed Vue KDS style")
else:
    print("Style block not found")
