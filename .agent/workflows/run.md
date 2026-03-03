---
description: How to run the RecruitAI Django application locally
---

### 1. Setup Virtual Environment
Create and activate a Python virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies
Install all required packages from `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### 3. Environment Variables
Ensure you have a `.env` file in the root directory with the following variables:
- `SECRET_KEY`: A unique secret key for Django.
- `DEBUG`: Set to `True` for development.
- `CLOUDINARY_CLOUD_NAME`: Your Cloudinary cloud name.
- `CLOUDINARY_API_KEY`: Your Cloudinary API key.
- `CLOUDINARY_API_SECRET`: Your Cloudinary API secret.
- `REDIS_URL`: URL for your Redis instance (default: `redis://localhost:6379/0`).

### 4. Database Migrations
Run the migrations to setup your local SQLite database:
```powershell
python manage.py migrate
```

### 5. Run the Application
Start the Django development server:
```powershell
python manage.py runserver
```

### 6. Run Celery Worker (Optional)
If you want to process background tasks (like AI scoring), ensure Redis is running and start the Celery worker:
```powershell
celery -A portal worker -l info
```

### 7. Create Superuser (Optional)
To access the admin panel at `/admin/`:
```powershell
python manage.py createsuperuser
```
