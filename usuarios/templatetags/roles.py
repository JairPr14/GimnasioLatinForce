from __future__ import annotations

from django import template

from usuarios.permissions import user_has_perm

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, perm_code: str) -> bool:
    request = context.get("request")
    if not request:
        return False
    return user_has_perm(request.user, perm_code)

