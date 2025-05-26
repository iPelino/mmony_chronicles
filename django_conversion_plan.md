# Django Conversion Plan for Mobile Money Transaction Analysis and Visualization

## Overview
This document outlines the plan to convert the Mobile Money Transaction Analysis and Visualization application into a Django-based web application, excluding the student grading feature.

## Current Application Structure
The current application consists of the following key components:
1. `process_data.py`: Processes XML files containing mobile money transaction data and extracts relevant information into a CSV file and SQLite database.
2. `analyze_data.py`: Analyzes the processed transaction data and generates various insights.
3. `visualize_data_v2.py`: Creates an interactive dashboard using Streamlit and Plotly to visualize the transaction data.

## Components to Exclude
The following components related to student grading will be excluded from the Django conversion:
1. `submission_scraper.py`: Scrapes student submissions from Canvas LMS.
2. `extract_ungraded.py`: Extracts ungraded student submissions.
3. `update_grading_status.py`: Updates the grading status of student submissions.
4. `github_submissions.json`: Stores student submission data.

## Django Project Structure
The Django project will be structured as follows:

```
mmony_chronicles_django/
├── manage.py
├── mmony_chronicles/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── transactions/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── forms.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── process_data.py
│   │   └── analyze_data.py
│   └── templates/
│       └── transactions/
│           ├── base.html
│           ├── index.html
│           ├── upload.html
│           ├── dashboard.html
│           └── analysis.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── templates/
    ├── base.html
    └── index.html
```

## Django Models
Based on the current SQLite database structure, the following Django models will be created:

```python
# transactions/models.py

from django.db import models

class IncomingMoney(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    sender = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    transaction_id = models.CharField(max_length=255)

class PaymentToCodeHolder(models.Model):
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient = models.CharField(max_length=255)
    date_time = models.DateTimeField()

class TransferToMobile(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient = models.CharField(max_length=255)
    recipient_number = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)

class BankDeposit(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField()

class AirtimeBillPayment(models.Model):
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)

class CashPowerBillPayment(models.Model):
    transaction_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)

class ThirdPartyTransaction(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    initiated_by = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    transaction_id = models.CharField(max_length=255)

class WithdrawalFromAgent(models.Model):
    user_name = models.CharField(max_length=255)
    agent_name = models.CharField(max_length=255)
    agent_number = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField()

class BankTransfer(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    recipient = models.CharField(max_length=255)
    date_time = models.DateTimeField()

class InternetBundlePurchase(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bundle_size = models.CharField(max_length=255)
    unit = models.CharField(max_length=10)
    duration = models.CharField(max_length=255, null=True, blank=True)

class VoiceBundlePurchase(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    minutes = models.CharField(max_length=255)
    smses = models.CharField(max_length=255)
```

## Views and Templates
The following views and templates will be created:

### Views
```python
# transactions/views.py

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

class HomeView(TemplateView):
    template_name = 'transactions/index.html'

class UploadView(FormView):
    template_name = 'transactions/upload.html'
    form_class = XMLUploadForm
    success_url = '/dashboard/'

    def form_valid(self, form):
        xml_file = form.cleaned_data['xml_file']
        process_xml_file(xml_file)
        return super().form_valid(form)

class DashboardView(TemplateView):
    template_name = 'transactions/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add data for charts
        context['daily_transactions'] = self.get_daily_transactions()
        context['top_recipients'] = self.get_top_recipients()
        context['top_recipients_code_holders'] = self.get_top_recipients_code_holders()
        context['top_agents'] = self.get_top_agents()
        context['bundle_analysis'] = self.get_bundle_analysis()
        return context

    def get_daily_transactions(self):
        # Similar to get_daily_transactions() in visualize_data_v2.py
        # but using Django ORM instead of SQL
        # ...

    def get_top_recipients(self):
        # Similar to get_top_recipients() in visualize_data_v2.py
        # ...

    def get_top_recipients_code_holders(self):
        # Similar to get_top_recipients_code_holders() in visualize_data_v2.py
        # ...

    def get_top_agents(self):
        # Similar to get_top_agents() in visualize_data_v2.py
        # ...

    def get_bundle_analysis(self):
        # Similar to get_bundle_analysis() in visualize_data_v2.py
        # ...

class AnalysisView(TemplateView):
    template_name = 'transactions/analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add data for analysis
        context['transaction_summary'] = self.get_transaction_summary()
        context['monthly_trends'] = self.get_monthly_trends()
        context['transaction_frequency'] = self.get_transaction_frequency()
        context['anomalies'] = self.get_anomalies()
        context['transaction_costs'] = self.get_transaction_costs()
        context['balance_trends'] = self.get_balance_trends()
        return context

    def get_transaction_summary(self):
        # Similar to transaction_summary() in analyze_data.py
        # ...

    def get_monthly_trends(self):
        # Similar to monthly_trends() in analyze_data.py
        # ...

    def get_transaction_frequency(self):
        # Similar to transaction_frequency() in analyze_data.py
        # ...

    def get_anomalies(self):
        # Similar to anomaly_detection() in analyze_data.py
        # ...

    def get_transaction_costs(self):
        # Similar to transaction_costs() in analyze_data.py
        # ...

    def get_balance_trends(self):
        # Similar to balance_trends() in analyze_data.py
        # ...
```

### Forms
```python
# transactions/forms.py

from django import forms

class XMLUploadForm(forms.Form):
    xml_file = forms.FileField(label='Upload XML File')
```

### Templates
The templates will be created to display the dashboard and analysis views, similar to the Streamlit application but using Django templates and JavaScript libraries like Chart.js or Plotly.js for visualization.

## URL Routing
```python
# transactions/urls.py

from django.urls import path
from .views import HomeView, UploadView, DashboardView, AnalysisView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('analysis/', AnalysisView.as_view(), name='analysis'),
]

# mmony_chronicles/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('transactions.urls')),
]
```

## Adapting Existing Functionality
The existing functionality in process_data.py, analyze_data.py, and visualize_data_v2.py will be adapted to work with Django:

1. process_data.py will be modified to work with Django models instead of SQLite.
2. analyze_data.py will be modified to work with Django models instead of CSV files.
3. visualize_data_v2.py will be replaced with Django views and templates.

## Updated Requirements
The requirements.txt file will be updated to include Django and other necessary packages:

```
pandas
plotly
django
django-crispy-forms
gunicorn  # For production deployment
whitenoise  # For serving static files
```

## Implementation Steps
1. Set up Django project structure
2. Create Django models
3. Implement views and templates
4. Adapt existing functionality
5. Test the application
6. Deploy the application

## Conclusion
This plan outlines the steps to convert the Mobile Money Transaction Analysis and Visualization application into a Django-based web application, excluding the student grading feature. The Django application will provide similar functionality to the current application but with a more robust web interface and better scalability.