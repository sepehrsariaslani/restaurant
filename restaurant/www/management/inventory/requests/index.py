from restaurant.www.management._context import build_context


def get_context(context):
    return build_context(context, "management-inventory")
