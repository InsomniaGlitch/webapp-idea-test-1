from django.contrib import admin
from .models import AudioFile


@admin.register(AudioFile)
class AudioFileAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "publish_date")
    search_fields = ("name", "category")
    list_filter = ("category", "publish_date")
