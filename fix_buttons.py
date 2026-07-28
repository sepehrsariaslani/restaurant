import re

with open('frontend/src/components/management/pos/PosCartPanel.vue', 'r') as f:
    content = f.read()

# Update buttons mapping
# "save-btn" is adding to table/registering. Should be Primary.
# "pay-btn" is settling invoice. Should be secondary or primary alternative.
# "settle-btn-custom" is settling and delivering. Should be Success.

# The prompt asks: "افزودن به میزتسویه از تب میزهاتسویه و تحویل"
# "رنگ های این دکمه ها رو هم تو صفحه پوز برای من درست بکن اگر میشه"

css_replace = """
.save-btn {
	background: var(--mg-primary);
}

.save-btn:hover:not(:disabled) {
	box-shadow: 0 4px 12px color-mix(in srgb, var(--mg-primary) 30%, transparent);
}

.settle-btn-custom {
	background: var(--mg-success);
	color: var(--mg-bg-surface);
	border: none;
	padding: 12px 16px;
	border-radius: 10px;
	font-weight: 700;
	font-size: 0.85rem;
	cursor: pointer;
	transition: all 0.15s ease;
}

.settle-btn-custom:hover:not(:disabled) {
	background: var(--mg-success);
	box-shadow: 0 4px 12px color-mix(in srgb, var(--mg-success) 30%, transparent);
}
.settle-btn-custom:disabled {
	background: var(--mg-success-bg);
	cursor: not-allowed;
	opacity: 0.6;
}

.pay-btn {
	background: var(--mg-text-main);
	color: var(--mg-bg-surface);
}

.pay-btn:hover:not(:disabled) {
	box-shadow: 0 4px 12px color-mix(in srgb, var(--mg-text-main) 20%, transparent);
}
"""

content = re.sub(r'\.save-btn \{.*?\n\}', '.save-btn {\n\tbackground: var(--mg-primary);\n}', content, flags=re.DOTALL)
content = re.sub(r'\.save-btn:hover:not\(:disabled\) \{.*?\n\}', '.save-btn:hover:not(:disabled) {\n\tbox-shadow: 0 4px 12px color-mix(in srgb, var(--mg-primary) 30%, transparent);\n}', content, flags=re.DOTALL)

content = re.sub(r'\.pay-btn \{.*?\n\}', '.pay-btn {\n\tbackground: var(--mg-text-main);\n\tcolor: var(--mg-bg-surface);\n}', content, flags=re.DOTALL)
content = re.sub(r'\.pay-btn:hover:not\(:disabled\) \{.*?\n\}', '.pay-btn:hover:not(:disabled) {\n\tbox-shadow: 0 4px 12px color-mix(in srgb, var(--mg-text-main) 20%, transparent);\n}', content, flags=re.DOTALL)

content = re.sub(r'\.settle-btn-custom:hover:not\(:disabled\) \{.*?\n\}', '.settle-btn-custom:hover:not(:disabled) {\n\tbackground: var(--mg-success);\n\tbox-shadow: 0 4px 12px color-mix(in srgb, var(--mg-success) 30%, transparent);\n}', content, flags=re.DOTALL)

with open('frontend/src/components/management/pos/PosCartPanel.vue', 'w') as f:
    f.write(content)
