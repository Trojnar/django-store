from django.contrib import admin

from reviews.models import Review


class ReviewAdmin(admin.ModelAdmin):
    list_display = ("review", "id", "author", "product")


admin.site.register(Review, ReviewAdmin)
