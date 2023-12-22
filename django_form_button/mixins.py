from typing import Any
from typing import Optional
from urllib.parse import urljoin

from django.contrib.admin import ModelAdmin
from django.http import HttpRequest
from django.template import engines
from django.urls import path

template = engines["django"].from_string("""
{% extends "admin/change_list.html" %}
{% block object-tools-items %}
  {% for button in form_buttons %}
    <li>
      <a href="{{ button.url }}">
        {{ button.title }}
      </a>
    </li>
  {% endfor %}
  {{ block.super }}
{% endblock %}
""")


class FormButtonMixin(ModelAdmin):  # type: ignore
    change_list_template = template  # type: ignore

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: Optional[dict[str, Any]] = None,
    ):
        extra_context = extra_context or {}
        form_buttons = getattr(self, "form_buttons", [])
        form_buttons = [
            {
                "name": b.name,
                "title": b.title,
                "url": urljoin(request.path, f"actions/{b.name}/"),
            }
            for b in form_buttons
        ]
        extra_context.update({"form_buttons": form_buttons})
        super()
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        return self.get_extra_urls() + urls

    def get_extra_urls(self):
        form_buttons = getattr(self, "form_buttons", [])
        return [
            path(f"actions/{func.name}/", self.admin_site.admin_view(func))
            for func in form_buttons
        ]
