from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from apps.category.models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "organization")
    list_filter = ("organization",)
    search_fields = ("name", "slug")
    readonly_fields = ("slug", "id")
    ordering = ("organization", "name")

    fieldsets = (
        (_("Category Details"), {
            "fields": ("name", "slug", "organization"),
        }),
    )
