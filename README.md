# WordBud 📝  
**A modern dictionary management system built with Django and Supabase**  

WordBud is a dictionary management system designed with a **modular Django architecture**, **Supabase Postgres backend**, and **clean code structure**. It provides a solid foundation for building features such as user authentication, dictionary lookups, word management, and user favorites.  

---

## 🚀 Features  
- 🔑 **User Authentication System** (Django auth + customizable)  
- 🗂️ **Modular App Structure** (`accounts`, `dictionary`, `favorites`, `core`)  
- 🌐 **Supabase Postgres Database Integration**  
- ⚡ **Django REST Framework Ready** (API-friendly design)  
- 📦 **Environment-based Config** using `python-decouple`  
- 🛠️ **Scalable and Team-friendly Git Workflow** (`main` = stable, `dev` = active development)  

---

## 🛠️ Tech Stack  
- **Backend:** Django 5 + Django REST Framework  
- **Database:** Supabase (Postgres)  
- **Auth:** Django’s built-in authentication (extendable)  
- **Environment Management:** `python-decouple`  
- **Package Management:** `pip + requirements.txt`  
- **Deployment Ready:** Config for static/media files & production DB  

---

## 📂 Project Structure 
WordBud/

│── apps/

│ ├── accounts/ # User authentication system

│ ├── dictionary/ # Core dictionary logic

│ ├── favorites/ # User saved words

│ └── core/ # Shared utilities

│── config/ # Django project settings

│── templates/ # Global templates

│── static/ # Static assets

│── media/ # Uploaded files

│── manage.py

│── requirements.txt

│── README.md

---

## ⚙️ Setup Instructions  

### 1️⃣ Clone the Repository  

git clone <copy the repo url>
### 2️⃣ Create Virtual Environment & Install Dependencies
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows

pip install -r requirements.txt

### 3️⃣ Configure Environment Variables

Create a .env file in the project root:

SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://username:password@host:5432/dbname

### 4️⃣ Run Migrations & Create Superuser
python manage.py migrate
python manage.py createsuperuser

### 5️⃣ Start Development Server
python manage.py runserver

### 🔀 Git Workflow

## main → Stable branch (production-ready code)

## dev → Active development branch

## Feature branches → Create per-task (e.g., feature/auth-system)

Example:

git checkout dev
git checkout -b feature/auth-system

### 📌 Roadmap

- ✅ Project skeleton setup

- 🔑 User authentication (current task)

- 📖 Dictionary CRUD system

- ⭐ Favorites system

- 🌍 API endpoints (Django REST Framework)

- 🎨 Frontend integration (to be decided)

### 🤝 Contributing

- Fork the repository

- Create a feature branch (git checkout -b feature/new-feature)

- Commit changes (git commit -m 'Add new feature')

- Push to branch (git push origin feature/new-feature)

- Open a Pull Request

⚡ Built with Django + Supabase
