import re

with open('frontend/src/pages/management/ManagementPosPage.vue', 'r') as f:
    pos = f.read()

# Add a style fix for the margin/padding in PosCartPanel
