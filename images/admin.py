from django.contrib import admin
from .models import Image


class ImageInline(admin.TabularInline):
    model = Image
