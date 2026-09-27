from restaurant.www._frontend import get_frontend_version


def get_context(context):
    from restaurant.page_layout import _require_management_access
    _require_management_access()
    context.boot = {}
    context.design_title = "پیش‌نمایش طراحی"
    context.frontend_version = get_frontend_version(context)
    context.no_cache = 1
    return context
