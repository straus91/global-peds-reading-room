# 🏥 Global Peds Reading Room

<div align="center">

**An AI-powered educational platform for global pediatric radiology learning**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)](https://postgresql.org)
[![AI](https://img.shields.io/badge/AI-Gemini%202.5%20Flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![Status](https://img.shields.io/badge/Status-Beta%20Testing-yellow.svg)](#)

[📖 Documentation](docs/) • [🧪 Beta Deployment](docs/BETA_DEPLOYMENT.md) • [⚡ Quick Reference](docs/QUICK_REFERENCE.md) • [🤖 AI Roadmap](further-ai.txt)

</div>

---

## 🎯 Current Status

🧪 **Active Beta Testing** - Currently deployed on DigitalOcean droplet, implementing systematic AI improvements and preparing for production release.

**Recent Updates**:
- ✅ Upgraded to Gemini 2.5 Flash for improved AI feedback
- ✅ Enhanced AI prompts with pedagogical improvements
- ✅ Implemented comprehensive documentation for beta workflow
- 🚧 Implementing data-driven AI iteration framework
- 🚧 Setting up systematic monitoring and testing processes

---

## 🌟 Overview

Global Peds Reading Room is a comprehensive educational web platform designed to revolutionize pediatric radiology learning. Medical professionals can view curated radiology cases, submit diagnostic reports, and receive **AI-powered feedback** to enhance their diagnostic skills.

This project is under active development with a focus on **data-driven AI improvement** and **scalable educational delivery**.

### ✨ Key Features

- 🔍 **Interactive DICOM Viewer** - View medical images through Orthanc/OHIF integration
- 🤖 **AI-Powered Feedback** - Intelligent diagnostic feedback using Google Gemini 2.5 Flash
  - Context-aware analysis considering patient demographics and clinical history
  - Severity-based discrepancy classification (Critical/Moderate/Consistent)
  - Programmatic pre-analysis + LLM for optimal accuracy and cost-efficiency
  - User feedback ratings for continuous AI improvement
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
- **Orthanc DICOM Server** - Medical image storage and OHIF viewer integration
- **Gunicorn** - Production WSGI server
- **nginx** - Reverse proxy
- **DigitalOcean Droplet** - Beta/production hosting

---

## 📚 Documentation

### 🎯 Quick Start
| Document | Description |
|----------|-------------|
| [📖 Documentation Index](DOCUMENTATION_INDEX.md) | Master guide to all documentation |
| [⚡ Quick Reference](docs/QUICK_REFERENCE.md) | Common commands and emergency procedures |
| [👨‍💻 Development Guide](docs/DEVELOPMENT.md) | Development setup and guidelines |

### 🧪 Beta Testing & Deployment
| Document | Description |
|----------|-------------|
| [🚀 Beta Deployment](docs/BETA_DEPLOYMENT.md) | Current droplet deployment workflow |
| [✅ Beta Testing Workflow](docs/BETA_TESTING_WORKFLOW.md) | Systematic testing procedures |
| [📊 Monitoring Setup](docs/MONITORING_SETUP.md) | Beta environment monitoring |

### 🤖 AI System
| Document | Description |
|----------|-------------|
| [🤖 AI Guide](docs/AI_GUIDE.md) | AI feedback system implementation |
| [🔄 AI Iteration Workflow](docs/AI_ITERATION_WORKFLOW.md) | Data-driven AI improvement process |
| [🗺️ AI Features Roadmap](docs/AI_FEATURES_ROADMAP.md) | Planned AI enhancements |
| [📋 Future AI Vision](further-ai.txt) | Comprehensive AI improvement strategy |

### 🏗️ Architecture & Reference
| Document | Description |
|----------|-------------|
| [🏗️ Architecture](docs/ARCHITECTURE.md) | System design and technical overview |
| [📁 Project Map](docs/PROJECT_MAP.md) | Codebase structure and organization |
| [📝 Changelog](docs/CHANGELOG.md) | Version history and updates |

### 📖 Claude Code Integration
The `.claude/docs/` directory contains comprehensive guides for development with Claude Code:
- Risk assessment framework
- Data models documentation
- Environment configuration
- Testing strategies
- Performance optimization
- Monitoring & analytics
- Development workflows
- Security best practices

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

### Local Development
```bash
# Start backend
cd backend && python manage.py runserver

# Start frontend
cd frontend && python -m http.server 5500
```

### Beta Environment
Currently deployed on DigitalOcean droplet. See:
- [Beta Deployment Guide](docs/BETA_DEPLOYMENT.md) - Current deployment process
- [Quick Reference](docs/QUICK_REFERENCE.md) - Common commands and emergency procedures

### Production
Production deployment procedures will be finalized after beta testing phase. See [Beta Deployment](docs/BETA_DEPLOYMENT.md) for current setup.

---

## 🤝 Development Workflow

This project follows a systematic development and testing approach:

### Beta Development Process
1. Develop and test locally
2. Push changes to `online_beta` branch
3. Deploy to beta droplet for production-like testing
4. Gather metrics and user feedback
5. Iterate based on data
6. Promote successful changes to production

### Code Changes
1. Complete risk assessment (see `.claude/docs/RISK_ASSESSMENT.md`)
2. Make changes on feature branch
3. Run tests (`python manage.py test`)
4. Test locally first
5. Deploy to beta
6. Monitor and verify
7. Document learnings

See [Development Guide](docs/DEVELOPMENT.md) and [Beta Testing Workflow](docs/BETA_TESTING_WORKFLOW.md) for detailed procedures.

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