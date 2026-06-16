from django.contrib import admin
from .models import CompanyProfile, TaxRate, FiscalPeriod

admin.site.register(CompanyProfile)
admin.site.register(TaxRate)
admin.site.register(FiscalPeriod)
