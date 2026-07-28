import re

def fix(path):
    with open(path, 'r') as f:
        content = f.read()

    # The background for the whole POS page should be var(--mg-bg-page)
    # The panels should be var(--mg-bg-surface)
    # Removing any remaining local pos-theme overrides if possible, or mapping them strictly to mg variables.

    # Remove card-in-card look
    css = """
.pos-fullpage {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 4.5rem);
  background: var(--mg-bg-page);
  padding: 0;
  overflow: hidden;
}

.ticket-tabs-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--mg-bg-surface);
  border-bottom: 1px solid var(--mg-border-light);
  padding: 0.5rem 1rem;
}

.ticket-tabs {
  display: flex;
  gap: 0.25rem;
}

.ticket-tab-group {
  display: flex;
  align-items: center;
  background: var(--mg-bg-page);
  border: 1px solid var(--mg-border-light);
  border-radius: var(--mg-radius-sm);
  overflow: hidden;
}

.ticket-tab-group.active {
  background: var(--mg-primary);
  border-color: var(--mg-primary);
}

.ticket-tab {
  padding: 0.4rem 0.75rem;
  border: none;
  background: transparent;
  color: var(--mg-text-muted);
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
}

.ticket-tab-group.active .ticket-tab {
  color: #fff;
}

.ticket-tab-close {
  padding: 0.4rem 0.5rem;
  border: none;
  background: transparent;
  color: var(--mg-text-muted);
  cursor: pointer;
}

.ticket-tab-group.active .ticket-tab-close {
  color: rgba(255, 255, 255, 0.8);
}

.ticket-tab-close:hover {
  color: var(--mg-danger);
}

.ticket-tab.new {
  background: transparent;
  border: 1px dashed var(--mg-border);
  border-radius: var(--mg-radius-sm);
}

.ticket-tab.new:hover {
  background: var(--mg-bg-surface);
}

.pos-shell {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.pos-main-grid {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.products-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cart-col {
  width: 380px;
  background: var(--mg-bg-surface);
  border-right: 1px solid var(--mg-border-light);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@media (max-width: 1024px) {
  .pos-fullpage {
    height: 100vh;
  }
  .cart-col {
    display: none;
  }
  .cart-col.mobile-open {
    display: flex;
    position: fixed;
    inset: 0;
    width: 100%;
    z-index: 100;
  }
}
"""

    if "/* POS BASE */" in content:
        content = re.sub(r'/\* POS BASE \*/.*?/\* \-\-\-\- \*/', css, content, flags=re.DOTALL)
    
    with open(path, 'w') as f:
        f.write(content)

# Actually, replacing large CSS blobs with regex is risky. Let's inspect the style tag first.
