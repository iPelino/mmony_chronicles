from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.views.generic import TemplateView, FormView
from .models import (
    IncomingMoney, PaymentToCodeHolder, TransferToMobile, BankDeposit,
    AirtimeBillPayment, CashPowerBillPayment, ThirdPartyTransaction,
    WithdrawalFromAgent, BankTransfer, InternetBundlePurchase, VoiceBundlePurchase
)
from .forms import XMLUploadForm
from .utils.process_data import process_xml_file
import json
import pandas as pd
from datetime import datetime

class HomeView(TemplateView):
    template_name = 'transactions/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add basic stats for the home page
        context['incoming_count'] = IncomingMoney.objects.count()
        context['outgoing_count'] = (
            TransferToMobile.objects.count() +
            PaymentToCodeHolder.objects.count() +
            BankTransfer.objects.count()
        )
        context['total_transactions'] = (
            IncomingMoney.objects.count() +
            PaymentToCodeHolder.objects.count() +
            TransferToMobile.objects.count() +
            BankDeposit.objects.count() +
            AirtimeBillPayment.objects.count() +
            CashPowerBillPayment.objects.count() +
            ThirdPartyTransaction.objects.count() +
            WithdrawalFromAgent.objects.count() +
            BankTransfer.objects.count() +
            InternetBundlePurchase.objects.count() +
            VoiceBundlePurchase.objects.count()
        )
        return context

class UploadView(FormView):
    template_name = 'transactions/upload.html'
    form_class = XMLUploadForm
    success_url = '/dashboard/'

    def dispatch(self, request, *args, **kwargs):
        # Redirect to login if user is not authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        xml_file = form.cleaned_data['xml_file']
        process_xml_file(xml_file, self.request.user)
        return super().form_valid(form)

class DashboardView(TemplateView):
    template_name = 'transactions/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        # Redirect to login if user is not authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add data for charts
        daily_transactions = self.get_daily_transactions()
        top_recipients = self.get_top_recipients()
        top_recipients_code_holders = self.get_top_recipients_code_holders()
        top_agents = self.get_top_agents()
        bundle_analysis = self.get_bundle_analysis()

        # Add raw data to context
        context['daily_transactions'] = daily_transactions
        context['top_recipients'] = top_recipients
        context['top_recipients_code_holders'] = top_recipients_code_holders
        context['top_agents'] = top_agents
        context['bundle_analysis'] = bundle_analysis

        # Add JSON serialized data for JavaScript
        context['daily_transactions_json'] = json.dumps(daily_transactions, default=str)
        context['top_recipients_json'] = json.dumps(top_recipients, default=str)
        context['top_recipients_code_holders_json'] = json.dumps(top_recipients_code_holders, default=str)
        context['top_agents_json'] = json.dumps(top_agents, default=str)
        context['bundle_analysis_json'] = json.dumps(bundle_analysis, default=str)

        return context

    def get_daily_transactions(self):
        # Get all transactions with date_time field for the current user
        all_transactions = []
        user = self.request.user

        # Incoming Money
        for tx in IncomingMoney.objects.filter(user=user):
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'incoming',
                'amount': float(tx.amount)
            })

        # Payment to Code Holder
        for tx in PaymentToCodeHolder.objects.filter(user=user):
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'payment_to_code',
                'amount': float(tx.amount)
            })

        # Transfer to Mobile
        for tx in TransferToMobile.objects.filter(user=user):
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'mobile_transfer',
                'amount': float(tx.amount)
            })

        # Bank Deposit
        for tx in BankDeposit.objects.filter(user=user):
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'bank_deposit',
                'amount': float(tx.amount)
            })

        # Airtime Bill Payment
        for tx in AirtimeBillPayment.objects.filter(user=user):
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'airtime_bill',
                'amount': float(tx.amount)
            })

        # Cash Power Bill Payment
        for tx in CashPowerBillPayment.objects.filter(user=user):
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'cash_power_bill',
                'amount': float(tx.amount)
            })

        # Third Party Transaction
        for tx in ThirdPartyTransaction.objects.filter(user=user):
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'third_party',
                'amount': float(tx.amount)
            })

        # Withdrawal from Agent
        for tx in WithdrawalFromAgent.objects.all():
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'withdrawal',
                'amount': float(tx.amount)
            })

        # Bank Transfer
        for tx in BankTransfer.objects.all():
            all_transactions.append({
                'day': tx.date_time.date(),
                'type': 'bank_transfer',
                'amount': float(tx.amount)
            })

        # Convert to DataFrame for easier aggregation
        df = pd.DataFrame(all_transactions)
        if df.empty:
            return []

        # Group by day and type
        daily_txns = df.groupby(['day', 'type']).agg({
            'amount': ['sum', 'count']
        }).reset_index()

        # Flatten the multi-level columns
        daily_txns.columns = ['day', 'type', 'total_amount', 'transaction_count']

        # Convert to list of dictionaries for the template
        return daily_txns.to_dict('records')

    def get_top_recipients(self):
        # Get top recipients of mobile transfers for the current user
        user = self.request.user
        recipients = TransferToMobile.objects.filter(user=user).values('recipient').annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')[:30]

        return list(recipients)

    def get_top_recipients_code_holders(self):
        # Get top recipients of code holder payments for the current user
        user = self.request.user
        recipients = PaymentToCodeHolder.objects.filter(user=user).values('recipient').annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')[:30]

        return list(recipients)

    def get_top_agents(self):
        # Get top agents by withdrawal volume for the current user
        user = self.request.user
        agents = WithdrawalFromAgent.objects.filter(user=user).values('agent_name').annotate(
            transaction_count=Count('id'),
            total_amount=Sum('amount')
        ).order_by('-total_amount')[:10]

        return list(agents)

    def get_bundle_analysis(self):
        # Analyze internet/voice bundle purchases for the current user
        user = self.request.user
        internet_bundles = InternetBundlePurchase.objects.filter(user=user).values('bundle_size', 'unit').annotate(
            purchase_count=Count('id'),
            total_amount=Sum('amount')
        )

        voice_bundles = VoiceBundlePurchase.objects.filter(user=user).values('minutes').annotate(
            purchase_count=Count('id'),
            total_amount=Sum('amount')
        )

        return {
            'internet': list(internet_bundles),
            'voice': list(voice_bundles)
        }

class AnalysisView(TemplateView):
    template_name = 'transactions/analysis.html'

    def dispatch(self, request, *args, **kwargs):
        # Redirect to login if user is not authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add data for analysis
        transaction_summary = self.get_transaction_summary()
        monthly_trends = self.get_monthly_trends()
        transaction_frequency = self.get_transaction_frequency()
        anomalies = self.get_anomalies()
        transaction_costs = self.get_transaction_costs()
        balance_trends = self.get_balance_trends()

        # Add raw data to context
        context['transaction_summary'] = transaction_summary
        context['monthly_trends'] = monthly_trends
        context['transaction_frequency'] = transaction_frequency
        context['anomalies'] = anomalies
        context['transaction_costs'] = transaction_costs
        context['balance_trends'] = balance_trends

        # Add JSON serialized data for JavaScript
        context['transaction_summary_json'] = json.dumps(transaction_summary, default=str)
        context['monthly_trends_json'] = json.dumps(monthly_trends, default=str)
        context['transaction_frequency_json'] = json.dumps(transaction_frequency, default=str)
        context['anomalies_json'] = json.dumps(anomalies, default=str)
        context['transaction_costs_json'] = json.dumps(transaction_costs, default=str)
        context['balance_trends_json'] = json.dumps(balance_trends, default=str)

        return context

    def get_transaction_summary(self):
        # Get summary of transactions by type
        summary = {}

        summary['Incoming Money'] = IncomingMoney.objects.aggregate(total=Sum('amount'))['total'] or 0
        summary['Payment to Code Holder'] = PaymentToCodeHolder.objects.aggregate(total=Sum('amount'))['total'] or 0
        summary['Transfer to Mobile'] = TransferToMobile.objects.aggregate(total=Sum('amount'))['total'] or 0
        summary['Bank Deposit'] = BankDeposit.objects.aggregate(total=Sum('amount'))['total'] or 0
        summary['Airtime Bill Payment'] = AirtimeBillPayment.objects.aggregate(total=Sum('amount'))['total'] or 0
        summary['Cash Power Bill Payment'] = CashPowerBillPayment.objects.aggregate(total=Sum('amount'))['total'] or 0
        summary['Third Party Transaction'] = ThirdPartyTransaction.objects.aggregate(total=Sum('amount'))['total'] or 0
        summary['Withdrawal from Agent'] = WithdrawalFromAgent.objects.aggregate(total=Sum('amount'))['total'] or 0
        summary['Bank Transfer'] = BankTransfer.objects.aggregate(total=Sum('amount'))['total'] or 0

        return summary

    def get_monthly_trends(self):
        # Get monthly trends of transactions
        all_transactions = []

        # Collect all transactions with date_time field
        for model, type_name in [
            (IncomingMoney, 'Incoming Money'),
            (PaymentToCodeHolder, 'Payment to Code Holder'),
            (TransferToMobile, 'Transfer to Mobile'),
            (BankDeposit, 'Bank Deposit'),
            (AirtimeBillPayment, 'Airtime Bill Payment'),
            (CashPowerBillPayment, 'Cash Power Bill Payment'),
            (ThirdPartyTransaction, 'Third Party Transaction'),
            (WithdrawalFromAgent, 'Withdrawal from Agent'),
            (BankTransfer, 'Bank Transfer')
        ]:
            for tx in model.objects.all():
                all_transactions.append({
                    'date_time': tx.date_time,
                    'type': type_name,
                    'amount': float(tx.amount)
                })

        # Convert to DataFrame
        df = pd.DataFrame(all_transactions)
        if df.empty:
            return []

        # Extract month from date_time
        df['month'] = df['date_time'].dt.to_period('M')

        # Group by month and type
        monthly_summary = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)

        # Convert to list of dictionaries for the template
        result = []
        for month, row in monthly_summary.iterrows():
            month_data = {'month': str(month)}
            for type_name, amount in row.items():
                month_data[type_name] = amount
            result.append(month_data)

        return result

    def get_transaction_frequency(self):
        # Get frequency of transactions by date
        all_transactions = []

        # Collect all transactions with date_time field
        for model in [
            IncomingMoney, PaymentToCodeHolder, TransferToMobile, BankDeposit,
            AirtimeBillPayment, CashPowerBillPayment, ThirdPartyTransaction,
            WithdrawalFromAgent, BankTransfer
        ]:
            for tx in model.objects.all():
                all_transactions.append({
                    'date': tx.date_time.date()
                })

        # Convert to DataFrame
        df = pd.DataFrame(all_transactions)
        if df.empty:
            return []

        # Count transactions by date
        frequency = df['date'].value_counts().sort_index()

        # Convert to list of dictionaries for the template
        result = [{'date': date, 'count': count} for date, count in frequency.items()]

        return result

    def get_anomalies(self):
        # Detect anomalies in transaction amounts
        all_transactions = []

        # Collect all transactions with amount field
        for model, type_name in [
            (IncomingMoney, 'Incoming Money'),
            (PaymentToCodeHolder, 'Payment to Code Holder'),
            (TransferToMobile, 'Transfer to Mobile'),
            (BankDeposit, 'Bank Deposit'),
            (AirtimeBillPayment, 'Airtime Bill Payment'),
            (CashPowerBillPayment, 'Cash Power Bill Payment'),
            (ThirdPartyTransaction, 'Third Party Transaction'),
            (WithdrawalFromAgent, 'Withdrawal from Agent'),
            (BankTransfer, 'Bank Transfer')
        ]:
            for tx in model.objects.all():
                all_transactions.append({
                    'type': type_name,
                    'amount': float(tx.amount),
                    'date_time': tx.date_time,
                    'id': tx.id,
                    'description': getattr(tx, 'description', ''),
                    'sender': getattr(tx, 'sender', ''),
                    'recipient': getattr(tx, 'recipient', '')
                })

        # Convert to DataFrame
        df = pd.DataFrame(all_transactions)
        if df.empty:
            return []

        # Calculate overall statistics
        overall_mean = df['amount'].mean()
        overall_std = df['amount'].std()
        overall_threshold = overall_mean + 3 * overall_std

        # Calculate type-specific statistics
        type_stats = df.groupby('type')['amount'].agg(['mean', 'std', 'count']).reset_index()
        type_stats['threshold'] = type_stats['mean'] + 3 * type_stats['std']

        # Create a dictionary for quick lookup
        type_stats_dict = {row['type']: row for _, row in type_stats.iterrows()}

        # Identify different types of anomalies
        anomalies = []

        # 1. High amount anomalies (overall)
        high_amount_anomalies = df[df['amount'] > overall_threshold].copy()
        if not high_amount_anomalies.empty:
            high_amount_anomalies['anomaly_type'] = 'High Amount'
            high_amount_anomalies['threshold'] = overall_threshold
            high_amount_anomalies['deviation_percent'] = ((high_amount_anomalies['amount'] - overall_threshold) / overall_threshold * 100).round(2)
            high_amount_anomalies['overall_mean'] = overall_mean
            high_amount_anomalies['times_above_mean'] = (high_amount_anomalies['amount'] / overall_mean).round(2)
            anomalies.append(high_amount_anomalies)

        # 2. Type-specific high amount anomalies
        for tx_type, stats in type_stats_dict.items():
            if pd.isna(stats['threshold']):  # Skip if threshold is NaN (happens when std is 0)
                continue

            type_anomalies = df[(df['type'] == tx_type) & (df['amount'] > stats['threshold'])].copy()
            if not type_anomalies.empty:
                type_anomalies['anomaly_type'] = f'High Amount for {tx_type}'
                type_anomalies['threshold'] = stats['threshold']
                type_anomalies['type_mean'] = stats['mean']
                type_anomalies['deviation_percent'] = ((type_anomalies['amount'] - stats['threshold']) / stats['threshold'] * 100).round(2)
                type_anomalies['times_above_type_mean'] = (type_anomalies['amount'] / stats['mean']).round(2)
                anomalies.append(type_anomalies)

        # 3. Frequency anomalies (transactions occurring at unusual times)
        df['hour'] = pd.to_datetime(df['date_time']).dt.hour
        night_transactions = df[(df['hour'] >= 22) | (df['hour'] <= 5)].copy()
        if not night_transactions.empty:
            night_transactions['anomaly_type'] = 'Unusual Time (Late Night/Early Morning)'
            night_transactions['unusual_hour'] = night_transactions['hour']
            anomalies.append(night_transactions)

        # Combine all anomalies and remove duplicates
        if anomalies:
            combined_anomalies = pd.concat(anomalies).drop_duplicates(subset=['id', 'type', 'amount', 'date_time'])
            return combined_anomalies.to_dict('records')
        else:
            return []

    def get_transaction_costs(self):
        # Get transaction costs (fees)
        costs = {}

        costs['Transfer to Mobile'] = TransferToMobile.objects.aggregate(total=Sum('fee'))['total'] or 0
        costs['Airtime Bill Payment'] = AirtimeBillPayment.objects.aggregate(total=Sum('fee'))['total'] or 0
        costs['Cash Power Bill Payment'] = CashPowerBillPayment.objects.aggregate(total=Sum('fee'))['total'] or 0

        return costs

    def get_balance_trends(self):
        # Calculate balance trends over time
        all_transactions = []

        # Collect all transactions with amount field and date_time
        for model, type_name, is_outgoing in [
            (IncomingMoney, 'Incoming Money', False),
            (PaymentToCodeHolder, 'Payment to Code Holder', True),
            (TransferToMobile, 'Transfer to Mobile', True),
            (BankDeposit, 'Bank Deposit', False),
            (AirtimeBillPayment, 'Airtime Bill Payment', True),
            (CashPowerBillPayment, 'Cash Power Bill Payment', True),
            (ThirdPartyTransaction, 'Third Party Transaction', True),
            (WithdrawalFromAgent, 'Withdrawal from Agent', True),
            (BankTransfer, 'Bank Transfer', True)
        ]:
            for tx in model.objects.all():
                # Negate amount for outgoing transactions
                amount = float(tx.amount)
                if is_outgoing:
                    amount = -amount

                all_transactions.append({
                    'date_time': tx.date_time,
                    'amount': amount
                })

        # Convert to DataFrame
        df = pd.DataFrame(all_transactions)
        if df.empty:
            return []

        # Sort by date_time
        df = df.sort_values('date_time')

        # Calculate cumulative sum (balance)
        df['balance'] = df['amount'].cumsum()

        # Select only date_time and balance columns
        balance_trend = df[['date_time', 'balance']]

        # Convert to list of dictionaries for the template
        return balance_trend.to_dict('records')
