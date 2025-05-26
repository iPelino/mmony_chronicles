# Mobile Money Chronicles - Django Web Application

This Django web application provides analysis and visualization of mobile money transaction data.

## Features

- Upload XML files containing mobile money transaction data
- Process and store transaction data in a database
- View interactive visualizations of transaction data
- Analyze transaction patterns and trends
- Generate insights from transaction data

## Project Structure

The project follows a standard Django structure:

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

## Installation

1. Clone the repository:
```
git clone <repository-url>
cd mmony_chronicles_django
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run migrations:
```
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser (optional):
```
python manage.py createsuperuser
```

6. Run the development server:
```
python manage.py runserver
```

7. Access the application at http://127.0.0.1:8000/

## Usage

1. Navigate to the Upload page and upload an XML file containing mobile money transaction data.
2. After uploading, you'll be redirected to the Dashboard page where you can view visualizations of your transaction data.
3. Visit the Analysis page to see detailed analysis and insights from your transaction data.

## Testing

Run the tests with:
```
python manage.py test
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.