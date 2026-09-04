# CasHub

CasHub is a Flask-based activity and portfolio platform designed for **International Baccalaureate (IB) students**.

As part of the IB experience, students are expected to participate in activities beyond the classroom and reflect on their personal growth, service, creativity, and involvement in their communities. Keeping track of these experiences over time can become difficult, especially when students are involved in several clubs, projects, service activities, and extracurricular commitments at once.

CasHub gives students one place to **record their extracurricular activities, write reflections, organize their involvement, interact with peers, and build a portfolio of their experiences**.

The platform is designed to make activity documentation easier and more engaging while helping students keep a clear record of the experiences that support their IB journey and portfolio requirements.

## What CasHub Does

CasHub combines activity tracking, social interaction, progress reminders, statistics, and portfolio generation into a single student-focused platform.

Students can:

* Record extracurricular and service activities
* Write reflections about what they learned or accomplished
* Associate activities with clubs or organizations
* Upload photos from activities
* Keep a chronological history of their involvement
* View and interact with classmates' activities
* Track participation across the student community
* Receive reminders when they have not documented an activity recently
* Export their experiences into a personal PDF portfolio

## Features

### Student Accounts

Students can create their own CasHub account with:

* Name
* Email
* Biography
* Clubs and organizations
* Secure password

Passwords are hashed using **PBKDF2-SHA256**, and authenticated users are managed through signed Flask sessions.

Each account becomes the student's personal activity portfolio inside the platform.

### Activity Documentation

The main purpose of CasHub is to help students consistently document the activities they participate in.

Each activity post can include:

* **Title** — the name of the activity or experience
* **Reflection** — what the student did, learned, contributed, or experienced
* **Date** — when the activity happened
* **Club or organization** — the group connected to the activity
* **Image** — an optional photo documenting the experience

This creates a chronological record that students can return to when reviewing their extracurricular involvement or preparing a portfolio.

### Reflections

CasHub encourages students to do more than simply list activities.

Each post includes space for a written reflection so students can describe:

* What they contributed
* What they learned
* Challenges they faced
* Skills they developed
* How the activity affected them or their community

This helps turn a list of extracurricular activities into a more meaningful record of student growth.

### Personal Portfolio

Every student has a personal profile containing:

* Name
* Email
* Biography
* Clubs
* Activity history
* Reflections
* Uploaded images
* Likes and comments received on their posts

The profile acts as a centralized portfolio of the student's involvement throughout the school year.

### PDF Portfolio Export

Students can export their recorded activities into a PDF portfolio directly from CasHub.

The generated portfolio includes:

* Activity titles
* Dates
* Clubs
* Written reflections
* Uploaded images when available

This allows students to keep a portable version of their activity history and use their documented experiences when reviewing their IB participation or preparing future applications and portfolios.

### Social Activity Feed

CasHub includes a community feed where students can view activities posted by their peers.

Students can:

* Browse recent activities
* See which students are participating in different clubs
* Read classmates' reflections
* Discover activities happening within the school community

The feed helps make extracurricular participation more visible and encourages students to learn from one another.

### Likes and Comments

Students can interact with activity posts through:

* Likes
* Comments

These features make CasHub more than a private activity tracker. They create a student community around extracurricular involvement and allow students to recognize and support each other's work.

### Student Profiles

Logged-in users can open another student's CasHub profile to see:

* Their biography
* Clubs
* Activities
* Reflections
* Activity history

This makes it easier for students to discover classmates with similar interests and learn more about the activities happening around their school.

### Participation Reminders

CasHub helps students maintain a consistent activity record.

If a student has not posted an activity in more than seven days, the platform displays a reminder encouraging them to document what they have been doing.

This helps prevent students from waiting until much later to reconstruct weeks or months of extracurricular activity.

### Statistics Dashboard

CasHub includes a community statistics page that highlights student participation.

The dashboard shows:

* **Top three students of the week** based on activity posts
* **Top three clubs of the week** based on activity posts
* Number of posts made by each student
* Date of each student's most recent activity
* Links to individual student profiles

The statistics page gives students and communities a quick overview of participation and makes extracurricular engagement more visible.

## Tech Stack

### Backend

* Python
* Flask
* SQLite

### Frontend

* HTML
* CSS
* Jinja templates

### Security

* Passlib
* PBKDF2-SHA256 password hashing
* Flask signed sessions
* Parameterized SQLite queries
* Authorization checks for protected actions

### Testing

* pytest

### Other Tools

* fpdf2 for PDF portfolio generation
* Werkzeug utilities for secure file uploads

## Project Structure

```text
CasHub/
├── my_app.py
├── My_library.py
├── requirements.txt
├── pyproject.toml
├── README.md
├── templates/
│   ├── _messages.html
│   ├── home.html
│   ├── login.html
│   ├── profile.html
│   ├── register.html
│   ├── statistics.html
│   └── students_profile.html
├── static/
│   ├── home.css
│   ├── login.css
│   ├── profile.css
│   ├── register.css
│   ├── statistics.css
│   └── images/
└── tests/
    ├── conftest.py
    ├── test_auth.py
    └── test_routes.py
```

## Application Architecture

```text
Browser
   ↓
Flask routes and application logic
   ↓
my_app.py
   ↓
My_library.py
   ↓
SQLite database

Flask
   ↓
Jinja templates
   ↓
HTML + CSS interface
```

`my_app.py` contains the main application routes and functionality.

`My_library.py` contains the SQLite database helper and password-hashing functions used throughout the application.

## Database

CasHub uses SQLite with four main tables.

### `users`

Stores:

* Account information
* Hashed passwords
* Biography
* Clubs
* Post count

### `posts`

Stores:

* Activity title
* Reflection
* Club
* Date
* User
* Likes
* Comments
* Image filename

### `comments`

Stores each comment and connects it to:

* A user
* A post

### `likes`

Tracks which users have liked which posts.

A uniqueness constraint prevents the same user from liking the same post more than once.

## Security

CasHub includes several protections for user accounts and data:

* Passwords are never stored as plaintext
* Authentication uses signed Flask sessions
* SQL queries use parameterized statements
* Users can only delete their own posts
* Uploaded filenames are sanitized
* Uploaded files are restricted to supported image formats
* Upload size is limited
* Generated filenames prevent accidental overwriting

## Testing

CasHub includes an automated pytest suite covering the application's main flows.

The tests check:

* Account registration
* Password hashing
* Login
* Invalid login attempts
* Duplicate account prevention
* Protected routes
* Activity creation
* Comments
* Likes and unlikes
* SQL-safe text handling
* Post deletion authorization
* Owner post deletion
* PDF generation

Run the test suite with:

```bash
python -m pytest
```

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/EmmyAbella444/CasHub.git
cd CasHub
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Set a secret key

**Windows PowerShell**

```powershell
$env:SECRET_KEY = "your-secret-key"
```

**macOS/Linux**

```bash
export SECRET_KEY="your-secret-key"
```

### 6. Start CasHub

```bash
python my_app.py
```

Then open:

```text
http://127.0.0.1:5000
```

The SQLite database is created automatically when the application starts.

## Main Routes

| Route                         | Purpose                            |
| ----------------------------- | ---------------------------------- |
| `/login`                      | User login                         |
| `/register`                   | Create an account                  |
| `/home`                       | Activity feed and post creation    |
| `/profile`                    | Current user's activity portfolio  |
| `/students_profile/<user_id>` | View another student's profile     |
| `/statistics`                 | Community activity dashboard       |
| `/save_pdf`                   | Export personal activity portfolio |
| `/logout`                     | End the current session            |

## Supported Image Formats

CasHub accepts:

* PNG
* JPG
* JPEG
* GIF
* WEBP

The maximum upload size is **5 MB**.
