import re

with open('frontend/src/components/management/pos/PosCartPanel.vue', 'r') as f:
    panel = f.read()

# Make the CTA buttons Earthy and semantic (Primary / Neutral / Success)
old_save_btn = """
.save-btn {
	background: var(--mg-primary);
}

.save-btn:hover:not(:disabled) {
	box-shadow: 0 4px 12px color-mix(in srgb, var(--mg-primary) 30%, transparent);
}
"""

new_save_btn = """
.save-btn {
	background: var(--mg-primary);
	color: #fff;
	transition: all 0.2s;
}

.save-btn:hover:not(:disabled) {
	background: color-mix(in srgb, var(--mg-primary) 85%, black);
	box-shadow: 0 4px 12px color-mix(in srgb, var(--mg-primary) 30%, transparent);
}
"""
panel = panel.replace(old_save_btn, new_save_btn)

old_pay_btn = """
.pay-btn {
	background: color-mix(in srgb, var(--mg-text-main) 88%, black 12%);
}

.pay-btn:hover:not(:disabled) {
	box-shadow: 0 4px 12px rgb(52 38 31 / 0.24);
}
"""

new_pay_btn = """
.pay-btn {
	background: var(--mg-text-main);
	color: var(--mg-bg-surface);
	transition: all 0.2s;
}

.pay-btn:hover:not(:disabled) {
	background: color-mix(in srgb, var(--mg-text-main) 85%, black);
	box-shadow: 0 4px 12px color-mix(in srgb, var(--mg-text-main) 20%, transparent);
}
"""
panel = panel.replace(old_pay_btn, new_pay_btn)

old_settle = """
.settle-btn-custom {
	background: var(--mg-success);
	color: var(--mg-bg-surface);
	border: none;
	padding: 12px 16px;
	border-radius: 10px;
"""

new_settle = """
.settle-btn-custom {
	background: var(--mg-success);
	color: #fff;
	border: none;
	padding: 12px 16px;
	border-radius: 10px;
"""
panel = panel.replace(old_settle, new_settle)

with open('frontend/src/components/management/pos/PosCartPanel.vue', 'w') as f:
    f.write(panel)

