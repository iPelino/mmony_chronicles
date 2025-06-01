from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Sum, Count, F
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
        xml_file_instance = form.save(commit=False)
        xml_file_instance.user = self.request.user
        xml_file_instance.save()
        process_xml_file(xml_file_instance.file, self.request.user)
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
        user = self.request.user
        from django.db.models.functions import TruncDay
        from django.db.models import Value, CharField
        from collections import defaultdict
        from datetime import datetime

        # Define a helper to get annotated querysets
        def get_annotated_queryset(model, transaction_type, amount_field='amount'):
            return model.objects.filter(user=user).annotate(
                day=TruncDay('date_time'),
                type=Value(transaction_type, output_field=CharField()),
                amount_val=F(amount_field)
            ).values('day', 'type', 'amount_val')

        # Get all transaction querysets separately
        incoming_money_qs = get_annotated_queryset(IncomingMoney, 'incoming')
        payment_to_code_qs = get_annotated_queryset(PaymentToCodeHolder, 'payment_to_code')
        mobile_transfer_qs = get_annotated_queryset(TransferToMobile, 'mobile_transfer')
        bank_deposit_qs = get_annotated_queryset(BankDeposit, 'bank_deposit')
        airtime_bill_qs = get_annotated_queryset(AirtimeBillPayment, 'airtime_bill')
        cash_power_bill_qs = get_annotated_queryset(CashPowerBillPayment, 'cash_power_bill')
        third_party_qs = get_annotated_queryset(ThirdPartyTransaction, 'third_party')
        withdrawal_qs = get_annotated_queryset(WithdrawalFromAgent, 'withdrawal')
        bank_transfer_qs = get_annotated_queryset(BankTransfer, 'bank_transfer')

        # Skip models without date_time field
        # internet_bundle_qs = get_annotated_queryset(InternetBundlePurchase, 'internet_bundle')
        # voice_bundle_qs = get_annotated_queryset(VoiceBundlePurchase, 'voice_bundle')

        # Combine all transactions into a single list
        all_transactions = list(incoming_money_qs) + list(payment_to_code_qs) + list(mobile_transfer_qs) + \
                          list(bank_deposit_qs) + list(airtime_bill_qs) + list(cash_power_bill_qs) + \
                          list(third_party_qs) + list(withdrawal_qs) + list(bank_transfer_qs)

        # Aggregate transactions by day and type in Python
        aggregated_data = defaultdict(lambda: {'total_amount': 0, 'transaction_count': 0})

        for transaction in all_transactions:
            key = (transaction['day'], transaction['type'])
            aggregated_data[key]['total_amount'] += float(transaction['amount_val'])
            aggregated_data[key]['transaction_count'] += 1

        # Convert to list of dictionaries in the expected format
        daily_txns = []
        for (day, txn_type), data in aggregated_data.items():
            daily_txns.append({
                'day': day,
                'type': txn_type,
                'total_amount': data['total_amount'],
                'transaction_count': data['transaction_count']
            })

        # Sort by day and type
        daily_txns.sort(key=lambda x: (x['day'], x['type']))

        return daily_txns

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
        from django.db.models.functions import Coalesce
        from django.db.models import Value, DecimalField

        user = self.request.user
        # Use Coalesce to handle cases where amount might be None or 'none'
        summary['Incoming Money'] = IncomingMoney.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        summary['Payment to Code Holder'] = PaymentToCodeHolder.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        summary['Transfer to Mobile'] = TransferToMobile.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        summary['Bank Deposit'] = BankDeposit.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        summary['Airtime Bill Payment'] = AirtimeBillPayment.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        summary['Cash Power Bill Payment'] = CashPowerBillPayment.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        summary['Third Party Transaction'] = ThirdPartyTransaction.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        summary['Withdrawal from Agent'] = WithdrawalFromAgent.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        summary['Bank Transfer'] = BankTransfer.objects.filter(user=user).aggregate(total=Sum(Coalesce('amount', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0

        return summary

    def get_monthly_trends(self):
        user = self.request.user
        from django.db.models.functions import TruncMonth
        from django.db.models import Value, CharField, F, DecimalField, Sum
        import pandas as pd

        # Define a helper to get annotated querysets for monthly trends
        def get_annotated_queryset(model, transaction_type, amount_field='amount'):
            # Skip models without date_time field
            if not hasattr(model, 'date_time'):
                return None

            # Handle case where amount might be None or 'none'
            from django.db.models.functions import Coalesce
            amount_val_field = Coalesce(F(amount_field), 0, output_field=DecimalField(max_digits=10, decimal_places=2))

            return model.objects.filter(user=user).annotate(
                month=TruncMonth('date_time'),
                type=Value(transaction_type, output_field=CharField()),
                amount_val=amount_val_field
            ).values('month', 'type', 'amount_val')

        # Combine querysets using union
        incoming_money_qs = get_annotated_queryset(IncomingMoney, 'Incoming Money')
        payment_to_code_qs = get_annotated_queryset(PaymentToCodeHolder, 'Payment to Code Holder')
        mobile_transfer_qs = get_annotated_queryset(TransferToMobile, 'Transfer to Mobile')
        bank_deposit_qs = get_annotated_queryset(BankDeposit, 'Bank Deposit')
        airtime_bill_qs = get_annotated_queryset(AirtimeBillPayment, 'Airtime Bill Payment')
        cash_power_bill_qs = get_annotated_queryset(CashPowerBillPayment, 'Cash Power Bill Payment')
        third_party_qs = get_annotated_queryset(ThirdPartyTransaction, 'Third Party Transaction')
        withdrawal_qs = get_annotated_queryset(WithdrawalFromAgent, 'Withdrawal from Agent')
        bank_transfer_qs = get_annotated_queryset(BankTransfer, 'Bank Transfer')

        # Union all querysets
        all_transactions_qs = incoming_money_qs.union(
            payment_to_code_qs, mobile_transfer_qs, bank_deposit_qs,
            airtime_bill_qs, cash_power_bill_qs, third_party_qs,
            withdrawal_qs, bank_transfer_qs
        )

        # Convert to list and then to DataFrame
        all_transactions_list = list(all_transactions_qs)
        df = pd.DataFrame(all_transactions_list)

        if df.empty:
            return []

        # Aggregate monthly trends using pandas
        monthly_summary = df.groupby(['month', 'type'])['amount_val'].sum().reset_index()
        monthly_summary = monthly_summary.rename(columns={'amount_val': 'total_amount'})
        monthly_summary = monthly_summary.sort_values(['month', 'type'])

        # Convert to list of dictionaries for the template
        return monthly_summary.to_dict('records')

    def get_transaction_frequency(self):
        user = self.request.user
        from django.db.models.functions import TruncDay
        from django.db.models import Value, CharField, F, DecimalField
        import pandas as pd

        # Define a helper to get annotated querysets for transaction frequency
        def get_annotated_queryset(model):
            # Skip models without date_time field
            if not hasattr(model, 'date_time'):
                return None

            # Handle case where amount might be None or 'none'
            from django.db.models.functions import Coalesce
            amount_expr = Coalesce(F('amount'), 0, output_field=DecimalField(max_digits=10, decimal_places=2)) if hasattr(model, 'amount') else Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))

            return model.objects.filter(user=user).annotate(
                date=TruncDay('date_time'),
                # Add a dummy amount_val for union compatibility, not used for count
                amount_val=amount_expr
            ).values('date', 'amount_val')

        # Combine querysets using union
        incoming_money_qs = get_annotated_queryset(IncomingMoney)
        payment_to_code_qs = get_annotated_queryset(PaymentToCodeHolder)
        mobile_transfer_qs = get_annotated_queryset(TransferToMobile)
        bank_deposit_qs = get_annotated_queryset(BankDeposit)
        airtime_bill_qs = get_annotated_queryset(AirtimeBillPayment)
        cash_power_bill_qs = get_annotated_queryset(CashPowerBillPayment)
        third_party_qs = get_annotated_queryset(ThirdPartyTransaction)
        withdrawal_qs = get_annotated_queryset(WithdrawalFromAgent)
        bank_transfer_qs = get_annotated_queryset(BankTransfer)
        # Skip models without date_time field
        # internet_bundle_qs = get_annotated_queryset(InternetBundlePurchase)
        # voice_bundle_qs = get_annotated_queryset(VoiceBundlePurchase)

        # Union all querysets (excluding None values)
        all_transactions_qs = incoming_money_qs.union(
            payment_to_code_qs, mobile_transfer_qs, bank_deposit_qs,
            airtime_bill_qs, cash_power_bill_qs, third_party_qs,
            withdrawal_qs, bank_transfer_qs
        )

        # Convert to list and then to DataFrame
        all_transactions_list = list(all_transactions_qs)
        df = pd.DataFrame(all_transactions_list)

        if df.empty:
            return []

        # Aggregate transaction frequency by date using pandas
        frequency = df.groupby('date').size().reset_index(name='count')
        frequency = frequency.sort_values('date')

        # Convert to list of dictionaries for the template
        return frequency.to_dict('records')

    def get_anomalies(self):
        user = self.request.user
        from django.db.models import Value, CharField, F, DecimalField
        from django.db.models.functions import Coalesce

        # Define a helper to get annotated querysets for anomalies
        def get_annotated_queryset(model, transaction_type, is_outgoing):
            # Skip models without date_time field
            if not hasattr(model, 'date_time'):
                return None

            amount_field = 'amount'
            # Use Coalesce to handle cases where a field might not exist on a model or might be None
            description_field = Coalesce(F('description'), Value(''), output_field=CharField()) if hasattr(model, 'description') else Value('', output_field=CharField())
            sender_field = Coalesce(F('sender'), Value(''), output_field=CharField()) if hasattr(model, 'sender') else Value('', output_field=CharField())
            recipient_field = Coalesce(F('recipient'), Value(''), output_field=CharField()) if hasattr(model, 'recipient') else Value('', output_field=CharField())
            # Handle case where amount might be None or 'none'
            amount_val_field = Coalesce(F(amount_field), 0, output_field=DecimalField(max_digits=10, decimal_places=2))

            qs = model.objects.filter(user=user).annotate(
                date_time_val=F('date_time'),
                amount_val=amount_val_field,
                type_val=Value(transaction_type, output_field=CharField()),
                id_val=F('id'),
                description_val=description_field,
                sender_val=sender_field,
                recipient_val=recipient_field
            ).values('date_time_val', 'amount_val', 'type_val', 'id_val', 'description_val', 'sender_val', 'recipient_val')

            # Apply negation for outgoing transactions at the database level if possible,
            # or handle in Python if not directly supported by ORM for all cases.
            # For simplicity, we'll keep the negation in Python for now after fetching.
            return qs

        # Combine querysets using union
        incoming_money_qs = get_annotated_queryset(IncomingMoney, 'Incoming Money', False)
        payment_to_code_qs = get_annotated_queryset(PaymentToCodeHolder, 'Payment to Code Holder', True)
        mobile_transfer_qs = get_annotated_queryset(TransferToMobile, 'Transfer to Mobile', True)
        bank_deposit_qs = get_annotated_queryset(BankDeposit, 'Bank Deposit', False)
        airtime_bill_qs = get_annotated_queryset(AirtimeBillPayment, 'Airtime Bill Payment', True)
        cash_power_bill_qs = get_annotated_queryset(CashPowerBillPayment, 'Cash Power Bill Payment', True)
        third_party_qs = get_annotated_queryset(ThirdPartyTransaction, 'Third Party Transaction', True)
        withdrawal_qs = get_annotated_queryset(WithdrawalFromAgent, 'Withdrawal from Agent', True)
        bank_transfer_qs = get_annotated_queryset(BankTransfer, 'Bank Transfer', True)

        # Union all querysets
        all_transactions_qs = incoming_money_qs.union(
            payment_to_code_qs, mobile_transfer_qs, bank_deposit_qs,
            airtime_bill_qs, cash_power_bill_qs, third_party_qs,
            withdrawal_qs, bank_transfer_qs
        )

        # Convert to list of dictionaries and then to DataFrame
        all_transactions_list = []
        for tx in all_transactions_qs:
            # Handle case where amount_val might be None or 'none'
            try:
                amount = float(tx['amount_val']) if tx['amount_val'] not in (None, 'none') else 0.0
            except (ValueError, TypeError):
                amount = 0.0

            # Negate amount for outgoing transactions (re-apply logic from original)
            if tx['type_val'] in ['Payment to Code Holder', 'Transfer to Mobile', 'Airtime Bill Payment',
                                  'Cash Power Bill Payment', 'Third Party Transaction', 'Withdrawal from Agent',
                                  'Bank Transfer']:
                amount = -amount

            all_transactions_list.append({
                'date_time': tx['date_time_val'],
                'amount': amount,
                'type': tx['type_val'],
                'id': tx['id_val'],
                'description': tx['description_val'],
                'sender': tx['sender_val'],
                'recipient': tx['recipient_val']
            })

        df = pd.DataFrame(all_transactions_list)
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
        from django.db.models.functions import Coalesce
        from django.db.models import DecimalField, Sum

        # Use Coalesce to handle cases where fee might be None or 'none'
        costs['Transfer to Mobile'] = TransferToMobile.objects.aggregate(total=Sum(Coalesce('fee', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        costs['Airtime Bill Payment'] = AirtimeBillPayment.objects.aggregate(total=Sum(Coalesce('fee', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0
        costs['Cash Power Bill Payment'] = CashPowerBillPayment.objects.aggregate(total=Sum(Coalesce('fee', 0, output_field=DecimalField(max_digits=10, decimal_places=2))))['total'] or 0

        return costs

    def get_balance_trends(self):
        user = self.request.user
        from django.db.models import Value, F, DecimalField
        from django.db.models.functions import Cast

        # Define a helper to get annotated querysets for balance trends
        def get_annotated_queryset(model, is_outgoing):
            # Skip models without date_time field
            if not hasattr(model, 'date_time'):
                return None

            # Cast amount to DecimalField to ensure consistent type for union
            # Handle case where amount might be 'none' by using Coalesce
            from django.db.models.functions import Coalesce

            # Default to 0 if amount is None or 'none'
            amount_expr = Coalesce(F('amount'), 0, output_field=DecimalField(max_digits=10, decimal_places=2))
            if is_outgoing:
                amount_expr = -amount_expr # Negate amount for outgoing transactions

            return model.objects.filter(user=user).annotate(
                date_time_val=F('date_time'),
                amount_val=Cast(amount_expr, output_field=DecimalField(max_digits=10, decimal_places=2))
            ).values('date_time_val', 'amount_val')

        # Combine querysets using union
        incoming_money_qs = get_annotated_queryset(IncomingMoney, False)
        payment_to_code_qs = get_annotated_queryset(PaymentToCodeHolder, True)
        mobile_transfer_qs = get_annotated_queryset(TransferToMobile, True)
        bank_deposit_qs = get_annotated_queryset(BankDeposit, False)
        airtime_bill_qs = get_annotated_queryset(AirtimeBillPayment, True)
        cash_power_bill_qs = get_annotated_queryset(CashPowerBillPayment, True)
        third_party_qs = get_annotated_queryset(ThirdPartyTransaction, True)
        withdrawal_qs = get_annotated_queryset(WithdrawalFromAgent, True)
        bank_transfer_qs = get_annotated_queryset(BankTransfer, True)

        # Union all querysets
        all_transactions_qs = incoming_money_qs.union(
            payment_to_code_qs, mobile_transfer_qs, bank_deposit_qs,
            airtime_bill_qs, cash_power_bill_qs, third_party_qs,
            withdrawal_qs, bank_transfer_qs
        )

        # Convert to list of dictionaries and then to DataFrame
        all_transactions_list = list(all_transactions_qs)
        df = pd.DataFrame(all_transactions_list)
        if df.empty:
            return []

        # Rename columns for consistency with original logic
        df = df.rename(columns={'date_time_val': 'date_time', 'amount_val': 'amount'})

        # Sort by date_time
        df = df.sort_values('date_time')

        # Calculate cumulative sum (balance)
        df['balance'] = df['amount'].cumsum()

        # Select only date_time and balance columns
        balance_trend = df[['date_time', 'balance']]

        # Convert to list of dictionaries for the template
        return balance_trend.to_dict('records')
