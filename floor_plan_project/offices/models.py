# offices/models.py

from django.db import models

class Office(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('rented', 'Rented'),
    ]

    office_number = models.IntegerField(unique=True, primary_key=True)
    size_sqft = models.DecimalField(max_digits=7, decimal_places=2)
    annual_rent = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

    # --- ADD THIS NEW FIELD ---
    start_date = models.DateField(null=True, blank=True, help_text="The date the current lease started.")
    expiry_date = models.DateField(null=True, blank=True, help_text="The date the current lease expires.")
    # --------------------------
    company_name = models.CharField(max_length=200, blank=True, null=True)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    contact_email = models.EmailField(max_length=254, blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Office {self.office_number}"

