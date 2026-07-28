import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    content = f.read()

content = content.replace(
    "paymentSelection = resolvePaymentSubmission(paymentMeta)",
    "let paymentSelection = resolvePaymentSubmission(paymentMeta)"
)

# Unsplash replacement:
content = re.sub(
    r"'(https?://images\.unsplash\.com/[^']+)'",
    "''",
    content
)

# Also let's check for visual tokens
content = content.replace('--pos-primary-color', '--mg-primary')
content = content.replace('--pos-primary', '--mg-primary')
content = content.replace('--pos-primary-rgb', '201 120 82')  # approx --mg-primary

content = content.replace('--pos-accent-color', '--mg-primary')
content = content.replace('--pos-accent', '--mg-primary')

content = content.replace('--pos-success-color', '--mg-success')
content = content.replace('--pos-success', '--mg-success')
content = content.replace('--pos-success-rgb', '111 123 86')

content = content.replace('--pos-danger-color', '--mg-danger')
content = content.replace('--pos-danger', '--mg-danger')
content = content.replace('--pos-danger-rgb', '166 84 63')

content = content.replace('--pos-warning-color', '--mg-primary')
content = content.replace('--pos-warning', '--mg-primary')

content = content.replace('--pos-white', '--mg-bg-surface')
content = content.replace('--pos-surface-color', '--mg-bg-surface')
content = content.replace('--pos-card', '--mg-bg-surface')

content = content.replace('--pos-text', '--mg-text-main')
content = content.replace('--pos-muted', '--mg-text-muted')

content = content.replace('--pos-border', '--mg-border')
content = content.replace('--pos-soft', '--mg-bg-page')
content = content.replace('--pos-hover', '--mg-bg-page')

content = content.replace('--bg-card', '--mg-bg-surface')

with open('frontend/src/pages/management/ManagementPosPage.vue', 'w') as f:
    f.write(content)
