# RecruitAI - AI-Powered Recruitment Platform

![RecruitAI](https://img.shields.io/badge/Django-5.x-green.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

RecruitAI is a modern, AI-powered recruitment platform that connects talented candidates with outstanding job opportunities. Built with Django and powered by SambaNova AI, it features intelligent resume matching, automated email workflows, and a professional user interface.

## 🌟 Features

### For Candidates
- 📝 **Smart Profile Management** - Create comprehensive profiles with resume uploads
- 🔍 **Job Search & Filtering** - Browse jobs with location and role filters
- 🎯 **AI-Powered Matching** - Get matched with jobs based on skills and experience
- 📊 **Application Tracking** - Track all your applications in one place
- 📧 **Email Notifications** - Receive updates on application status
- 🤖 **AI Chatbot Assistant** - Get help with SambaNova-powered chatbot
- 🔐 **Secure Authentication** - OTP-based password reset

### For HR/Recruiters
- 💼 **Job Posting** - Create and manage job postings with rich text editor
- 👥 **Candidate Management** - View and filter applicants with AI similarity scores
- 📈 **Resume-Based Scoring** - Automatic candidate ranking using AI
- ✅ **Bulk Actions** - Shortlist, reject, or invite multiple candidates at once
- 🎯 **Round Management** - Manage multiple interview rounds
- 📧 **Automated Emails** - Automatic notifications for all candidate actions
- 📊 **Analytics Dashboard** - Track jobs, applicants, and hiring metrics

### Additional Features
- 🎨 **Modern UI/UX** - Professional design with gradients and animations
- 📱 **Responsive Design** - Works seamlessly on all devices
- ☁️ **Cloud Storage** - Resume storage via Cloudinary
- 🔒 **Privacy & Security** - Comprehensive privacy policy and terms of service
- 📚 **Career Resources** - Resume tips, interview prep, and career advice
- 💰 **Pricing Plans** - Flexible pricing for different business sizes

## 🚀 Tech Stack

- **Backend:** Django 5.x
- **Database:** SQLite (Development) / PostgreSQL (Production)
- **AI/ML:** 
  - SambaNova AI (Chatbot)
  - Scikit-learn (Resume matching)
- **Storage:** Cloudinary
- **Email:** Django Anymail with SendGrid
- **Task Queue:** Celery + Redis
- **Deployment:** Gunicorn + WhiteNoise

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Git

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/recruitai.git
cd recruitai
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (Optional - for PostgreSQL in production)
DATABASE_URL=postgresql://user:password@localhost:5432/recruitai

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email Configuration (SendGrid)
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@recruitai.com

# SambaNova AI
SAMBANOVA_API_KEY=your-sambanova-api-key

# Redis (for Celery - Optional)
REDIS_URL=redis://localhost:6379/0
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Collect Static Files (Production)
```bash
python manage.py collectstatic
```

### 8. Run Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser!

## 📁 Project Structure

```
JobPortal/
├── core/                      # Main application
│   ├── migrations/           # Database migrations
│   ├── templatetags/         # Custom template tags
│   ├── admin.py             # Admin configuration
│   ├── auth_views.py        # Authentication views
│   ├── chatbot.py           # SambaNova AI chatbot
│   ├── decorators.py        # Custom decorators
│   ├── forms.py             # Django forms
│   ├── models.py            # Database models
│   ├── signals.py           # Email notification signals
│   ├── urls.py              # URL routing
│   ├── utils.py             # Utility functions
│   └── views.py             # View functions
├── portal/                   # Project configuration
│   ├── settings.py          # Django settings
│   ├── urls.py              # Root URL config
│   └── wsgi.py              # WSGI config
├── templates/               # HTML templates
│   ├── auth/               # Authentication templates
│   ├── core/               # Core app templates
│   └── emails/             # Email templates
├── static/                  # Static files
│   ├── css/                # Stylesheets
│   └── js/                 # JavaScript files
├── .env                     # Environment variables
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔑 Key Models

### CustomUser
- Extends Django's AbstractUser
- Fields: `is_hr`, `is_candidate`, `company_name`

### CandidateProfile
- One-to-One with User
- Fields: Skills, projects, education, experience, resume (Cloudinary)

### JobPost
- Fields: Title, description, location, required skills, eligibility criteria
- Methods: `check_eligibility(profile)`

### Application
- Links Candidate to JobPost
- Fields: Status, score, interview details
- Statuses: PENDING, SHORTLISTED, SECOND_ROUND, SELECTED, REJECTED

## 🤖 AI Features

### Resume Matching Algorithm
Uses TF-IDF and cosine similarity to match candidates with jobs:
- **Keyword Matching:** Direct skill overlap
- **Semantic Matching:** Contextual similarity using TF-IDF
- **Blended Scoring:** Weighted combination (80% skills, 20% job description)

### SambaNova Chatbot
- Model: Meta-Llama-3.1-8B-Instruct
- Provides real-time assistance to users
- Helps with navigation and common questions

## 📧 Email Notifications

Automated emails are sent for:
- ✅ New job posted (to matching candidates)
- ✅ Application received (to candidate)
- ✅ Shortlisted (to candidate)
- ✅ Interview invitation (to candidate)
- ✅ Round cleared (to candidate)
- ✅ Final selection (to candidate)
- ✅ Rejection (to candidate)

## 🎨 UI/UX Features

- Modern gradient designs (#667eea → #764ba2)
- Smooth animations and hover effects
- Responsive Bootstrap 5 layout
- Professional typography (Inter font)
- Glassmorphism effects
- Interactive chatbot widget

## 🔐 Security Features

- Django's built-in CSRF protection
- Password hashing with PBKDF2
- OTP-based password reset
- Secure file uploads to Cloudinary
- Environment variable protection

## 🚀 Deployment

### Deploy to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables in Render dashboard
4. Use the included `render.yaml` for configuration
5. Deploy!

### Deploy to Heroku

```bash
# Install Heroku CLI
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
heroku config:set SAMBANOVA_API_KEY=your-api-key
# ... set other environment variables
git push heroku main
heroku run python manage.py migrate
```

## 📝 Usage

### For Candidates
1. Sign up as a Candidate
2. Complete your profile with skills and resume
3. Browse available jobs
4. Apply to jobs matching your profile
5. Track applications in "My Applications"

### For HR/Recruiters
1. Sign up as an HR user
2. Create job postings
3. View applicants with AI-generated scores
4. Shortlist candidates
5. Manage interview rounds
6. Select final candidates

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run specific app tests
python manage.py test core
```

## 📊 Admin Panel

Access the Django admin panel at `/admin/`:
- Manage users, jobs, and applications
- View all data in one place
- Perform bulk actions

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- SambaNova AI for the chatbot integration
- Cloudinary for file storage
- Bootstrap for the UI framework
- Django community for excellent documentation

## 📞 Support

For support, email support@recruitai.com or visit our [Contact Page](http://127.0.0.1:8000/contact/).

## 🔗 Links

- **Live Demo:** [https://recruitai.onrender.com](https://recruitai.onrender.com)
- **Documentation:** [Wiki](https://github.com/yourusername/recruitai/wiki)
- **Bug Reports:** [Issues](https://github.com/yourusername/recruitai/issues)

---

**Made with ❤️ using Django and SambaNova AI**
