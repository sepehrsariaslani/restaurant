import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    c = f.read()

c = c.replace('color: var(--mg-primary)', 'color: var(--mg-text-muted)')
# Not blindly. The previous regex converted many things to var(--mg-primary) which should be text-muted.
# For example: rgb(1 90 114 / 0.78) was probably a dark blue-grey.

