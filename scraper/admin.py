from django.contrib import admin
from .models import ScrapedLead

@admin.register(ScrapedLead)
class ScrapedLeadAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'industry', 'qualification_score', 'pipeline_status', 'created_at')
    list_filter = ('qualification_score', 'pipeline_status', 'industry')
    search_fields = ('company_name', 'location', 'description_summary')
