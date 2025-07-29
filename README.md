# Flask Scheduler App

This project provides a small dashboard for managing apartment tasks using Flask. Features include:

- **User authentication** with roles (admin, purple, viewer).
- **Calendar** for adding events that everyone can view.
- **Class schedule** view displaying weekly events.
- **Grocery list** that residents can update.
- **Utility bill tracker** (admin only) with email notifications via Gmail/Yagmail.
- **Daily overview** page showing weather and today's schedule.
- **Music player** to play uploaded songs on a connected speaker.


A small SQLite database (`database.db`) stores user accounts, events, schedules, grocery items, and utility bills.

All passwords are hashed using Werkzeug's `pbkdf2:sha256` method. If you are upgrading from an older version that used scrypt, delete `database.db` or reset each account password so it is stored with the new algorithm.

## Getting Started

1. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   python app.py
   ```
   The app will initialize the database on first run and start listening on `http://localhost:5000/`.

An admin account is created automatically with username `admin` and password `adminpass`.

## Password Hashing

User passwords are stored using Werkzeug's `pbkdf2:sha256` hash. If you migrate from a version that used a different scheme, remove the existing `database.db` file or manually reset each user's password after upgrading so the new hash method is applied.

## Configuration

- The daily overview page fetches weather data. Edit `app.py` and update `weather_api_key` and `city` in the `overview` route with your own OpenWeatherMap API key and city.
- Email sending for utilities uses `yagmail` with a Gmail account. Update the credentials in the `utilities` route if you plan to use this feature.

## License

This repository was provided without a specific license. Use at your own risk.