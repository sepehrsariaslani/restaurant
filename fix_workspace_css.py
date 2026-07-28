with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'r') as f:
    content = f.read()

content = content.replace(
"""
.kds-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 1rem;
  overflow: hidden;
}
""",
"""
.kds-workspace {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: 1.5rem;
  overflow: hidden;
  background: var(--mg-bg-page);
}
@media (max-width: 1024px) {
  .kds-workspace {
    height: auto;
    overflow: visible;
    padding: 1rem 0.5rem;
  }
}
"""
)

with open('frontend/src/pages/management/ManagementKitchenPage.vue', 'w') as f:
    f.write(content)
