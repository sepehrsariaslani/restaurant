import re

with open('frontend/src/components/management/ManagementLayout.vue', 'r') as f:
    content = f.read()

# Replace CSS block for DFM
old_css_start = "/* --- Desktop Floating Menu --- */"
old_css_end = ".desktop-sidebar { display: none; }"

css_block = content[content.find(old_css_start):content.find(old_css_end) + len(old_css_end)]

new_css = """/* --- Desktop Floating Menu (Top Right) --- */
	.dfm-wrapper {
		position: fixed;
		top: 1.25rem;
		right: 1.25rem;
		z-index: 10000;
	}

	.dfm-toggle-btn {
		width: 3.8rem;
		height: 3.8rem;
		border-radius: 50%;
		background: var(--mg-bg-surface);
		color: var(--mg-primary);
		border: 2px solid var(--mg-primary);
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		box-shadow: 0 8px 24px rgba(0,0,0,0.08);
		transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		position: relative;
		z-index: 10001;
	}
	
	/* Space rings animation */
	.dfm-toggle-btn::before, .dfm-toggle-btn::after {
		content: '';
		position: absolute;
		inset: -2px;
		border-radius: 50%;
		border: 2px solid var(--mg-primary);
		opacity: 0;
		pointer-events: none;
	}
	.dfm-toggle-btn::before {
		animation: dfm-ring-pulse 3s infinite ease-out;
	}
	.dfm-toggle-btn::after {
		animation: dfm-ring-pulse 3s infinite ease-out 1.5s;
	}

	@keyframes dfm-ring-pulse {
		0% { transform: scale(1); opacity: 0.8; border-width: 2px; }
		100% { transform: scale(1.6); opacity: 0; border-width: 0px; }
	}

	.dfm-toggle-btn:hover {
		transform: scale(1.05);
		background: var(--mg-primary);
		color: var(--mg-bg-surface);
	}
	.dfm-toggle-btn:hover .dfm-line {
		background: var(--mg-bg-surface);
	}

	.dfm-burger {
		width: 22px;
		height: 16px;
		position: relative;
	}
	.dfm-line {
		display: block;
		width: 100%;
		height: 2.5px;
		background: var(--mg-primary);
		border-radius: 2px;
		position: absolute;
		right: 0;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	}
	.dfm-line.top { top: 0; }
	.dfm-line.mid { top: 50%; transform: translateY(-50%); }
	.dfm-line.bot { bottom: 0; }

	.dfm-toggle-btn.is-open {
		background: var(--mg-primary);
		color: #fff;
		border-color: var(--mg-primary);
		transform: rotate(90deg);
	}
	.dfm-toggle-btn.is-open::before, .dfm-toggle-btn.is-open::after {
		animation-play-state: paused;
		opacity: 0;
		display: none;
	}
	.dfm-toggle-btn.is-open .dfm-line { background: #fff; }
	.dfm-toggle-btn.is-open .dfm-line.top { top: 50%; transform: translateY(-50%) rotate(45deg); }
	.dfm-toggle-btn.is-open .dfm-line.mid { opacity: 0; transform: translateY(-50%) scaleX(0); }
	.dfm-toggle-btn.is-open .dfm-line.bot { bottom: 50%; transform: translateY(50%) rotate(-45deg); }

	.dfm-dropdown {
		position: absolute;
		top: calc(100% + 1rem);
		right: 0;
		width: 18rem;
		background: color-mix(in srgb, var(--mg-bg-surface) 96%, transparent);
		backdrop-filter: blur(16px);
		-webkit-backdrop-filter: blur(16px);
		border: 1px solid var(--mg-border-light);
		border-radius: 24px;
		box-shadow: 0 32px 64px rgba(0,0,0,0.15);
		display: flex;
		flex-direction: column;
		max-height: calc(100vh - 6rem);
		z-index: 10000;
		overflow: hidden;
	}

	.dfm-brand-block {
		padding: 1.25rem 1.25rem;
		border-bottom: 1px solid var(--mg-border-light);
		background: var(--mg-bg-page);
	}

	.dfm-brand {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		text-decoration: none;
		color: var(--mg-text-main);
	}
	
	.dfm-brand-text { display: grid; }
	.dfm-brand-text strong { font-weight: 900; font-size: 1.1rem; letter-spacing: -0.01em; }
	.dfm-brand-text small { font-size: 0.75rem; color: var(--mg-text-muted); margin-top: 0.1rem; }

	.dfm-nav {
		padding: 1rem;
		overflow-y: auto;
		gap: 1.25rem;
	}

	.dfm-backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0,0,0,0.2);
		backdrop-filter: blur(4px);
		-webkit-backdrop-filter: blur(4px);
		z-index: 9998;
	}

	.dfm-anim-enter-active, .dfm-anim-leave-active {
		transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
		transform-origin: top right;
	}
	.dfm-anim-enter-from, .dfm-anim-leave-to {
		opacity: 0;
		transform: scale(0.85) translateY(-20px);
	}

	.desktop-header {
		padding-right: 6.5rem !important; /* Make room for the top-right floating button */
	}

	/* Desktop layout content takes full width now */
	.desktop-sidebar { display: none; }"""

if css_block:
    content = content.replace(css_block, new_css)
else:
    print("Could not find CSS block!")

with open('frontend/src/components/management/ManagementLayout.vue', 'w') as f:
    f.write(content)
