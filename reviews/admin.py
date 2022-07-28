from django.contrib import admin

from reviews.models import Review


class ReviewAdmin(admin.TabularInline):
    list_display = ("product", "author", "rewiev")


admin.site.register(Review)
