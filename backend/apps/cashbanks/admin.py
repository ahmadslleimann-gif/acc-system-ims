from django.contrib import admin
from .models import CashBankAccount, CashTransaction

admin.site.register(CashBankAccount)
admin.site.register(CashTransaction)
