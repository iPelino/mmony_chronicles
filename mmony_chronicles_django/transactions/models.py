from django.db import models
from django.conf import settings

class IncomingMoney(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sender = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    transaction_id = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='incoming_money')

    def __str__(self):
        return f"{self.amount} from {self.sender} on {self.date_time}"

class PaymentToCodeHolder(models.Model):
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='payments_to_code_holder')

    def __str__(self):
        return f"{self.amount} to {self.recipient} on {self.date_time}"

class TransferToMobile(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient = models.CharField(max_length=255)
    recipient_number = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='transfers_to_mobile')

    def __str__(self):
        return f"{self.amount} to {self.recipient} ({self.recipient_number}) on {self.date_time}"

class BankDeposit(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='bank_deposits')

    def __str__(self):
        return f"{self.amount} on {self.date_time}"

class AirtimeBillPayment(models.Model):
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='airtime_bill_payments')

    def __str__(self):
        return f"Airtime: {self.amount} on {self.date_time}"

class CashPowerBillPayment(models.Model):
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='cash_power_bill_payments')

    def __str__(self):
        return f"Cash Power: {self.amount} on {self.date_time}"

class ThirdPartyTransaction(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    initiated_by = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    transaction_id = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='third_party_transactions')

    def __str__(self):
        return f"{self.amount} initiated by {self.initiated_by} on {self.date_time}"

class WithdrawalFromAgent(models.Model):
    user_name = models.CharField(max_length=255)
    agent_name = models.CharField(max_length=255)
    agent_number = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='withdrawals_from_agent')

    def __str__(self):
        return f"{self.amount} from {self.agent_name} on {self.date_time}"

class BankTransfer(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='bank_transfers')

    def __str__(self):
        return f"{self.amount} to {self.recipient} on {self.date_time}"

class InternetBundlePurchase(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bundle_size = models.CharField(max_length=255)
    unit = models.CharField(max_length=10)
    duration = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='internet_bundle_purchases')

    def __str__(self):
        return f"{self.bundle_size}{self.unit} for {self.amount}"

class VoiceBundlePurchase(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    minutes = models.CharField(max_length=255)
    smses = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='voice_bundle_purchases')

    def __str__(self):
        return f"{self.minutes} minutes + {self.smses} SMS for {self.amount}"
