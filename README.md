# 🏥 Global Peds Reading Room

<div align="center">

**An AI-powered educational platform for global pediatric radiology learning**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[🚀 Live Demo](#) • [📖 Documentation](docs/) • [🐛 Report Bug](../../issues) • [💡 Request Feature](../../issues)

</div>

---

## 🌟 Overview

Global Peds Reading Room is a comprehensive educational web platform designed to revolutionize pediatric radiology learning. Medical professionals can view curated radiology cases, submit diagnostic reports, and receive **AI-powered feedback** to enhance their diagnostic skills.

### ✨ Key Features

- 🔍 **Interactive DICOM Viewer** - View medical images with embedded Stone Web Viewer
- 🤖 **AI-Powered Feedback** - Get intelligent feedback on diagnostic reports using Google Gemini
- 📋 **Structured Templates** - Standardized reporting templates for consistency
- 👥 **Multi-User Support** - Role-based access for students, residents, fellows, and attendings
- 📊 **Progress Tracking** - Monitor learning progress and improvement over time
- 🌐 **Global Access** - Designed for international medical education
- ⚡ **Real-time Analysis** - Instant comparison with expert interpretations

---

## 📸 Screenshots

> 🚧 **Coming Soon**: Screenshots of the platform interface will be added here

---

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** 
- **PostgreSQL**
- **Orthanc DICOM Server** (with Stone Web Viewer)
- **Google Gemini API Key**

### 🔧 Installation

#### 1️⃣ Backend Setup

```bash
# Clone the repository
git clone https://github.com/straus91/global-peds-reading-room.git
cd global-peds-reading-room

# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows cmd:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database credentials and API keys

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

#### 2️⃣ Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Start local server
python -m http.server 5500
```

#### 3️⃣ Access the Application

- **Frontend**: http://localhost:5500
- **Backend API**: http://127.0.0.1:8000
- **Admin Panel**: http://127.0.0.1:8000/admin

---

## 🛠️ Tech Stack

### Backend
- **Django 5.2** - Web framework
- **Django REST Framework** - API development
- **PostgreSQL** - Primary database
- **Google Gemini API** - AI-powered feedback
- **JWT Authentication** - Secure user sessions

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **HTML5 & CSS3** - Modern web standards
- **Stone Web Viewer** - DICOM image viewing
- **Responsive Design** - Works on all devices

### Infrastructure
- **Orthanc DICOM Server** - Medical image storage
- **Gunicorn** - Production WSGI server
- **nginx** - Reverse proxy (production)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [🏗️ Architecture](docs/ARCHITECTURE.md) | System design and technical overview |
| [👨‍💻 Development](docs/DEVELOPMENT.md) | Development setup and guidelines |
| [📁 Project Map](docs/PROJECT_MAP.md) | Codebase structure and organization |
| [🤖 AI Guide](docs/AI_GUIDE.md) | AI feedback system implementation |
| [🚀 Deployment](docs/DEPLOYMENT.md) | Production deployment guide |
| [📝 Changelog](docs/CHANGELOG.md) | Version history and updates |

---

## 🏗️ Project Structure

```
global-peds-reading-room/
├── 📁 backend/                 # Django REST API
│   ├── 📁 cases/               # Core case management logic
│   ├── 📁 users/               # User authentication & profiles
│   ├── 📁 api/                 # API routing & views
│   └── 📁 globalpeds_project/  # Django settings
├── 📁 frontend/                # Vanilla JS frontend
│   ├── 📁 admin/               # Admin interface pages
│   ├── 📁 css/                 # Stylesheets
│   ├── 📁 js/                  # JavaScript modules
│   └── 📁 assets/              # Images & static files
├── 📁 docs/                    # Documentation
└── 📄 README.md               # This file
```

---

## 🌟 Features Deep Dive

### 🤖 AI-Powered Feedback System
- **Context-Aware Analysis**: AI considers case history, patient demographics, and imaging findings
- **Severity Indicators**: Discrepancies are categorized by clinical importance
- **Learning-Focused**: Feedback designed to enhance diagnostic skills, not just correct errors
- **Continuous Improvement**: User ratings help refine AI feedback quality

### 👥 User Management
- **Role-Based Access**: Different permissions for students, residents, fellows, and attendings
- **Registration Approval**: Admin oversight for new user registration
- **Progress Tracking**: Individual learning analytics and improvement metrics
- **Global Accessibility**: Multi-country support with institution tracking

### 📊 Case Management
- **DICOM Integration**: Seamless viewing of medical images
- **Template System**: Standardized reporting formats
- **Expert Comparisons**: Side-by-side analysis with expert interpretations
- **Case Curation**: Admin tools for adding and managing teaching cases

---

## 🚀 Deployment

### Development
```bash
# Start backend
cd backend && python manage.py runserver

# Start frontend  
cd frontend && python -m http.server 5500
```

### Production
See [Deployment Guide](docs/DEPLOYMENT.md) for detailed production setup instructions.

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python manage.py test`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

- 📧 **Email**: [Contact Developer](mailto:mst@ad.unc.edu)
- 🐛 **Issues**: [GitHub Issues](../../issues)
- 💬 **Discussions**: [GitHub Discussions](../../discussions)

---

## 🙏 Acknowledgments

- **Medical Educators** who provided case curation expertise
- **Orthanc Community** for excellent DICOM server solutions
- **Google Gemini** for AI capabilities
- **Open Source Community** for tools and libraries

---

<div align="center">

**Made with ❤️ for medical education**

⭐ Star this repo if you find it helpful!

</div>