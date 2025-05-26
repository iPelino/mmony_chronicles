from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import (
    IncomingMoney, PaymentToCodeHolder, TransferToMobile, BankDeposit,
    AirtimeBillPayment, CashPowerBillPayment, ThirdPartyTransaction,
    WithdrawalFromAgent, BankTransfer, InternetBundlePurchase, VoiceBundlePurchase
)

class ModelTestCase(TestCase):
    def setUp(self):
        # Create test data for each model
        IncomingMoney.objects.create(
            amount=1000,
            sender="Test Sender",
            date_time=timezone.now(),
            transaction_id="123456"
        )
        
        PaymentToCodeHolder.objects.create(
            transaction_id="234567",
            amount=2000,
            recipient="Test Recipient",
            date_time=timezone.now()
        )
        
        TransferToMobile.objects.create(
            amount=3000,
            recipient="Test Mobile Recipient",
            recipient_number="250123456789",
            date_time=timezone.now(),
            fee=100
        )
        
        BankDeposit.objects.create(
            amount=4000,
            date_time=timezone.now()
        )
        
        AirtimeBillPayment.objects.create(
            transaction_id="345678",
            amount=500,
            date_time=timezone.now(),
            fee=50
        )
        
        CashPowerBillPayment.objects.create(
            transaction_id="456789",
            amount=1500,
            date_time=timezone.now(),
            fee=75
        )
        
        ThirdPartyTransaction.objects.create(
            amount=2500,
            initiated_by="Test Initiator",
            date_time=timezone.now(),
            transaction_id="567890"
        )
        
        WithdrawalFromAgent.objects.create(
            user_name="Test User",
            agent_name="Test Agent",
            agent_number="123456",
            amount=5000,
            date_time=timezone.now()
        )
        
        BankTransfer.objects.create(
            amount=6000,
            recipient="Test Bank Recipient",
            date_time=timezone.now()
        )
        
        InternetBundlePurchase.objects.create(
            amount=1000,
            bundle_size="5",
            unit="GB"
        )
        
        VoiceBundlePurchase.objects.create(
            amount=500,
            minutes="60",
            smses="100"
        )
    
    def test_incoming_money_model(self):
        incoming = IncomingMoney.objects.get(transaction_id="123456")
        self.assertEqual(incoming.amount, 1000)
        self.assertEqual(incoming.sender, "Test Sender")
    
    def test_payment_to_code_holder_model(self):
        payment = PaymentToCodeHolder.objects.get(transaction_id="234567")
        self.assertEqual(payment.amount, 2000)
        self.assertEqual(payment.recipient, "Test Recipient")
    
    def test_transfer_to_mobile_model(self):
        transfer = TransferToMobile.objects.get(recipient_number="250123456789")
        self.assertEqual(transfer.amount, 3000)
        self.assertEqual(transfer.fee, 100)
    
    def test_bank_deposit_model(self):
        deposit = BankDeposit.objects.first()
        self.assertEqual(deposit.amount, 4000)
    
    def test_airtime_bill_payment_model(self):
        payment = AirtimeBillPayment.objects.get(transaction_id="345678")
        self.assertEqual(payment.amount, 500)
        self.assertEqual(payment.fee, 50)
    
    def test_cash_power_bill_payment_model(self):
        payment = CashPowerBillPayment.objects.get(transaction_id="456789")
        self.assertEqual(payment.amount, 1500)
        self.assertEqual(payment.fee, 75)
    
    def test_third_party_transaction_model(self):
        transaction = ThirdPartyTransaction.objects.get(transaction_id="567890")
        self.assertEqual(transaction.amount, 2500)
        self.assertEqual(transaction.initiated_by, "Test Initiator")
    
    def test_withdrawal_from_agent_model(self):
        withdrawal = WithdrawalFromAgent.objects.get(agent_number="123456")
        self.assertEqual(withdrawal.amount, 5000)
        self.assertEqual(withdrawal.agent_name, "Test Agent")
    
    def test_bank_transfer_model(self):
        transfer = BankTransfer.objects.get(recipient="Test Bank Recipient")
        self.assertEqual(transfer.amount, 6000)
    
    def test_internet_bundle_purchase_model(self):
        purchase = InternetBundlePurchase.objects.get(bundle_size="5")
        self.assertEqual(purchase.amount, 1000)
        self.assertEqual(purchase.unit, "GB")
    
    def test_voice_bundle_purchase_model(self):
        purchase = VoiceBundlePurchase.objects.get(minutes="60")
        self.assertEqual(purchase.amount, 500)
        self.assertEqual(purchase.smses, "100")

class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/index.html')
    
    def test_upload_view(self):
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/upload.html')
    
    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/dashboard.html')
    
    def test_analysis_view(self):
        response = self.client.get(reverse('analysis'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/analysis.html')