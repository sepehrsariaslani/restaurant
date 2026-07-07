from ._context import build_context


def get_context(context):
    return build_context(context, "management-settings", required_roles={"System Manager"})
