import re

with open('restaurant/www/management/_context.py', 'r') as f:
    content = f.read()

addition = """
import os

def _get_frontend_version():
    try:
        # Cache busting strategy: Use the actual modified time of the built asset
        # so it auto-updates precisely when `npm run build` is executed.
        asset_path = frappe.get_app_path("restaurant", "public", "frontend", "assets", "index.js")
        if os.path.exists(asset_path):
            return str(int(os.path.getmtime(asset_path)))
    except Exception:
        pass
    
    # Fallback to frappe's system build version
    return frappe.utils.get_build_version()
"""

# Inject before build_context
if "_get_frontend_version" not in content:
    content = content.replace("def build_context(", addition + "\n\ndef build_context(")
    
    # Also inject into the context
    content = content.replace("context.boot = boot\n    return context", "context.boot = boot\n    context.frontend_version = _get_frontend_version()\n    return context")

with open('restaurant/www/management/_context.py', 'w') as f:
    f.write(content)

