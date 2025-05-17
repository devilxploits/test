# Sophia AI Application

This is the Sophia AI chatbot application with subscription limitations and fixes.

## Features Implemented
- Chat limitations where only paid users or admins can chat freely with Sophia
- 50-message free trial for Instagram and Telegram users
- Flirty subscription prompts to encourage subscriptions
- Fixed database errors with platform data storage
- Fixed module import issues
- Fixed CSS display for Premium and Price tags

## Quick Start
1. Clone this repository
2. Run the application with one of these options:
   - `python direct_run.py` (recommended)
   - `python fix_imports.py`
   - `python clone_and_run.py`

## Default Admin Login
- Username: admin
- Password: admin123

## Key Changes Made
- Added message counter to track conversations (models.py)
- Fixed platform parameter format in scheduler.py
- Implemented subscription limitations and flirty prompts
- Added subscription message styling
- Fixed Python import path issues
- Fixed CSS display for "Premium" and "$3.99" badges in Latest Posts section

## Configuration
- The main configuration is in `config.py`
- Environment variables can be set in `.env` file
- Database uses SQLite by default (in `instance/sophia.db`)

## API Endpoints
- `/` - Main landing page
- `/chat` - Chat interface (subscription protected)
- `/login` - Admin login page
- `/admin` - Admin dashboard (requires login)
- `/subscription` - Subscription page

## Deployment Notes
- The application is configured to run on port 5000
- For production deployment, use a WSGI server like Gunicorn
- All static assets are in the `static` directory
