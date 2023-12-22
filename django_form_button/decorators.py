from functools import wraps
from typing import Callable
from typing import ParamSpec
from typing import Protocol
from typing import Type
from typing import TypeVar
from typing import cast

from django.contrib import admin
from django.forms import Form
from django.http import HttpRequest
from django.http import HttpResponse
from django.http.response import HttpResponseBase
from django.template import RequestContext
from django.template import Template

# https://github.com/microsoft/pylance-release/issues/3777
P = ParamSpec("P")
R = TypeVar("R", covariant=True)


class FuncWithAttrs(Protocol[P, R]):
    def __call__(*args: P.args, **kwargs: P.kwargs) -> R: ...

    title: str
    name: str


def make_func_with_attrs(fn: Callable[P, R]) -> FuncWithAttrs[P, R]:
    return cast(FuncWithAttrs[P, R], fn)


template = Template("""
{% extends "admin/base_site.html" %}
{% load admin_urls static l10n %}
{% block extrastyle %}
  {{ block.super }}
  <link rel="stylesheet"
        type="text/css"
        href="{% static "admin/css/forms.css" %}">
{% endblock %}
{% block content %}
  <div id="content-main">
    <form method="post" enctype="multipart/form-data">
      {% csrf_token %}
      {% for obj in queryset.all %}<input type="hidden" name="_selected_action" value="{{ obj.pk|unlocalize }}"/>{% endfor %}
      <div>
        {% if form.errors %}<p class="errornote">Please correct the errors below.</p>{% endif %}
        <fieldset class="module aligned wide">
          {% for field in form %}
            <div class="form-row">
              {{ field.errors }}
              {{ field.label_tag }} {{ field }}
              {% if field.help_text %}<div class="help">{{ field.help_text|safe }}</div>{% endif %}
            </div>
          {% endfor %}
        </div>
      </fieldset>
      <div class="submit-row">
        <input type="hidden" name="action" value="{{ action }}"/>
        <input type="submit" name="submit" value="Submit" class="default" />
      </div>
    </form>
  </div>
{% endblock %}
""")


def render_form(request: HttpRequest, form: Form, title: str):
    context = {
        "site_header": admin.site.site_header,
        "site_title": admin.site.site_title,
        "site_title": admin.site.site_title,
        "title": title,
        "form": form,
    }
    context = RequestContext(request, context)
    return HttpResponse(template.render(context))


def form_button(title: str, form_cls: Type[Form]):
    def decorator(func: Callable[[HttpRequest, Form], HttpResponseBase]):
        @make_func_with_attrs
        @wraps(func)
        def wrapper(request: HttpRequest):
            if request.POST.get("submit") is not None:
                form = form_cls(request.POST, request.FILES)
                if form.is_valid():
                    # success
                    return func(request, form)
                # show form with errors
                return render_form(request, form, title)
            else:
                # show an empty form
                return render_form(request, form_cls(), title)

        wrapper.title = title
        wrapper.name = func.__name__
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


def button(title: str):
    def decorator(func: Callable[[HttpRequest], HttpResponseBase]):
        @make_func_with_attrs
        @wraps(func)
        def wrapper(request: HttpRequest):
            return func(request)

        wrapper.title = title
        wrapper.name = func.__name__
        wrapper.__name__ = func.__name__
        return wrapper

    return decorator
