from django.contrib import admin
from .models import (
    IncomingMoney, PaymentToCodeHolder, TransferToMobile, BankDeposit,
    AirtimeBillPayment, CashPowerBillPayment, ThirdPartyTransaction,
    WithdrawalFromAgent, BankTransfer, InternetBundlePurchase, VoiceBundlePurchase
)

# Register models
admin.site.register(IncomingMoney)
admin.site.register(PaymentToCodeHolder)
admin.site.register(TransferToMobile)
admin.site.register(BankDeposit)
admin.site.register(AirtimeBillPayment)
admin.site.register(CashPowerBillPayment)
admin.site.register(ThirdPartyTransaction)
admin.site.register(WithdrawalFromAgent)
admin.site.register(BankTransfer)
admin.site.register(InternetBundlePurchase)
admin.site.register(VoiceBundlePurchase)