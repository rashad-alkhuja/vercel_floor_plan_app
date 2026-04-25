# offices/admin.py

from django.contrib import admin
from .models import Office

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('office_number', 'status', 'start_date', 'expiry_date', 'company_name', 'contact_person', 'size_sqft')
    list_editable = ('status', 'start_date', 'expiry_date',)
    list_filter = ('status',)
    ordering = ('office_number',)
    
    # This will organize the edit page for a cleaner look
    fieldsets = (
        ('Office Details', {
            'fields': ('office_number', 'size_sqft', 'annual_rent')
        }),
        ('Lease Status', {
            'fields': ('status', 'start_date', 'expiry_date')
        }),
        ('Tenant Information (for Rented Offices)', {
            'fields': ('company_name', 'contact_person', 'contact_email', 'contact_phone')
        }),
    )

