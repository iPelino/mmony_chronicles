from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date
from .models import PaymentToCodeHolder, TransferToMobile, BankTransfer

class ReceiverHistoryView(TemplateView):
    template_name = 'transactions/receiver_history.html'

    def dispatch(self, request, *args, **kwargs):
        # Redirect to login if user is not authenticated
        if not request.user.is_authenticated:
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get filter parameters from request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        code_holder = self.request.GET.get('code_holder')
        receiver = self.request.GET.get('receiver')

        # Set default date values if not provided
        today = datetime.now().date()
        default_start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        default_end_date = today.strftime('%Y-%m-%d')

        # Initialize filter conditions and error messages
        code_holder_filter = Q()
        mobile_filter = Q()
        bank_filter = Q()
        error_messages = []

        # Apply date filters if provided
        if start_date:
            # Parse the start date using Django's parse_date function
            start_date_obj = parse_date(start_date)

            if start_date_obj:
                # Apply the filter to all transaction types using __date lookup to ignore time
                code_holder_filter &= Q(date_time__date__gte=start_date_obj)
                mobile_filter &= Q(date_time__date__gte=start_date_obj)
                bank_filter &= Q(date_time__date__gte=start_date_obj)

                # Debug print to check the parsed date
                print(f"Filtering transactions from date: {start_date_obj}")
            else:
                # Invalid date format, log the error and add to error messages
                print(f"Error parsing start date: {start_date}")
                error_messages.append(f"Invalid start date format: {start_date}. Please use YYYY-MM-DD format.")
                # Use default start date
                start_date = default_start_date

        # If no start date provided, use default
        else:
            start_date = default_start_date

        if end_date:
            # Parse the end date using Django's parse_date function
            end_date_obj = parse_date(end_date)

            if end_date_obj:
                # Add one day to end_date_obj to include the entire end date
                # This ensures transactions from the entire end date are included
                end_date_inclusive = end_date_obj + timedelta(days=1)

                # Apply the filter to all transaction types using __date lookup to ignore time
                code_holder_filter &= Q(date_time__date__lt=end_date_inclusive)
                mobile_filter &= Q(date_time__date__lt=end_date_inclusive)
                bank_filter &= Q(date_time__date__lt=end_date_inclusive)

                # Debug print to check the parsed date
                print(f"Filtering transactions until date: {end_date_obj} (inclusive)")
            else:
                # Invalid date format, log the error and add to error messages
                print(f"Error parsing end date: {end_date}")
                error_messages.append(f"Invalid end date format: {end_date}. Please use YYYY-MM-DD format.")
                # Use default end date
                end_date = default_end_date

        # If no end date provided, use default
        else:
            end_date = default_end_date

        # Debug print to show the actual date range being used for filtering
        start_date_obj = parse_date(start_date)
        end_date_obj = parse_date(end_date)
        if start_date_obj and end_date_obj:
            print(f"Actual date range for filtering: {start_date_obj} to {end_date_obj} (inclusive)")

        # Create filter conditions for code_holder and receiver
        code_holder_condition = Q()

        if code_holder:
            code_holder_condition = Q(recipient__icontains=code_holder)

        # Initialize receiver conditions
        receiver_condition_basic = Q()
        receiver_condition_mobile = Q()

        if receiver:
            # For PaymentToCodeHolder and BankTransfer, only recipient field is available
            receiver_condition_basic = Q(recipient__icontains=receiver)
            # For TransferToMobile, both recipient and recipient_number fields are available
            receiver_condition_mobile = receiver_condition_basic | Q(recipient_number__icontains=receiver)

        # Apply filters to each transaction type
        if code_holder and receiver:
            # If both filters are provided, return transactions that match either criteria
            code_holder_filter &= (code_holder_condition | receiver_condition_basic)
            mobile_filter &= (code_holder_condition | receiver_condition_mobile)
            bank_filter &= (code_holder_condition | receiver_condition_basic)
        elif code_holder:
            # If only code_holder filter is provided
            code_holder_filter &= code_holder_condition
            mobile_filter &= code_holder_condition
            bank_filter &= code_holder_condition
        elif receiver:
            # If only receiver filter is provided
            code_holder_filter &= receiver_condition_basic
            mobile_filter &= receiver_condition_mobile
            bank_filter &= receiver_condition_basic

        # Get transactions for the current user with applied filters
        user = self.request.user
        code_holder_payments = PaymentToCodeHolder.objects.filter(
            code_holder_filter, 
            user=user
        ).order_by('-date_time')

        mobile_transfers = TransferToMobile.objects.filter(
            mobile_filter, 
            user=user
        ).order_by('-date_time')

        bank_transfers = BankTransfer.objects.filter(
            bank_filter, 
            user=user
        ).order_by('-date_time')

        # Prepare transactions for display
        transactions = []

        for payment in code_holder_payments:
            transactions.append({
                'type': 'Payment to Code Holder',
                'recipient': payment.recipient,
                'amount': payment.amount,
                'date_time': payment.date_time,
                'transaction_id': payment.transaction_id,
                'details': f"Code Holder: {payment.recipient}"
            })

        for transfer in mobile_transfers:
            transactions.append({
                'type': 'Transfer to Mobile',
                'recipient': transfer.recipient,
                'amount': transfer.amount,
                'date_time': transfer.date_time,
                'transaction_id': getattr(transfer, 'transaction_id', 'N/A'),
                'details': f"Mobile: {transfer.recipient_number}"
            })

        for transfer in bank_transfers:
            transactions.append({
                'type': 'Bank Transfer',
                'recipient': transfer.recipient,
                'amount': transfer.amount,
                'date_time': transfer.date_time,
                'transaction_id': getattr(transfer, 'transaction_id', 'N/A'),
                'details': f"Bank: {transfer.recipient}"
            })

        # Sort transactions by date (newest first)
        transactions.sort(key=lambda x: x['date_time'], reverse=True)

        # Debug prints to show transaction counts
        print(f"Found {len(code_holder_payments)} code holder payments")
        print(f"Found {len(mobile_transfers)} mobile transfers")
        print(f"Found {len(bank_transfers)} bank transfers")
        print(f"Total transactions after filtering: {len(transactions)}")

        # Add to context
        context['transactions'] = transactions
        context['filter_params'] = {
            'start_date': start_date,
            'end_date': end_date,
            'code_holder': code_holder,
            'receiver': receiver
        }

        # Add filter status message
        filter_messages = []
        if start_date:
            filter_messages.append(f"From: {start_date}")
        if end_date:
            filter_messages.append(f"To: {end_date}")
        if code_holder:
            filter_messages.append(f"Code Holder: {code_holder}")
        if receiver:
            filter_messages.append(f"Receiver: {receiver}")

        context['filter_status'] = " | ".join(filter_messages) if filter_messages else ""

        # Add error messages to context
        context['error_messages'] = error_messages

        return context
