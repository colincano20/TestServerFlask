from flask import Flask, render_template, request, redirect, url_for, session,jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
from datetime import date, datetime,timedelta
import os
import pygame 
from kasa import SmartBulb
import asyncio
import colorsys

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# --- DATABASE SETUP ---
def init_db():
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT, email TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                created_by TEXT NOT NULL
            )
        ''')
        
        cur.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,              -- e.g., 'Austin'
                class_title TEXT,       -- e.g., 'Thermodynamics'
                weekday TEXT,           -- e.g., 'Monday'
                start_time TEXT,        -- '09:30'
                end_time TEXT           -- '10:20'
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS grocery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT,
                user TEXT            
                    )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS utilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT,
                    type TEXT,
                    total REAL
                    )
                    ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS polls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS poll_options (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER,
                option_text TEXT,
                FOREIGN KEY (poll_id) REFERENCES polls(id)
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poll_id INTEGER,
                option_id INTEGER,
                user TEXT,
                FOREIGN KEY (poll_id) REFERENCES polls(id),
                FOREIGN KEY (option_id) REFERENCES poll_options(id)
            )
            
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS bus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT,
                time TEXT            
                    )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                file_path TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                message TEXT
            )
        ''')
        
        conn.commit()

# --- AUTH HELPERS ---
def get_user(username):
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (username,))
        return cur.fetchone()

def add_user(username, password, role):
    hashed = generate_password_hash(password, method="pbkdf2:sha256")
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed, role))
        conn.commit()

def check_login(username, password):
    user = get_user(username)
    if user and check_password_hash(user[2], password):
        return user
    return None
WEEKDAY_MAP = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4
}
# --- ROUTES ---
@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/overview')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = check_login(request.form['username'], request.form['password'])
        if user:
            session['user'] = user[1]
            session['role'] = user[3]
            return redirect('/dashboard')
        else:
            error = "Invalid username or password."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/overview')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html', user=session['user'], role=session['role'])

@app.route('/access')
def access_manager():
    if session.get('role') != 'admin':
        return redirect('/dashboard')
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT username, role FROM users')
        users = cur.fetchall()
    return render_template('access_manager.html', users=users)
@app.route('/users', methods = ['GET'])
def users():
    if session.get('role') != 'admin':
        return redirect('/dashboard')
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT username, role FROM users')
        users = cur.fetchall()
    return render_template('users.html', users=users)


@app.route('/adduser', methods=['POST'])
def add_user_route():
    if session.get('role') != 'admin':
        return redirect('/dashboard')
    
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if username and password and role:
        add_user(username, password, role)
        return redirect('/access')
    else:
        return "Missing username, password, or role", 400  # Or render a template with error
    
@app.route('/deleteuser', methods=['POST'])
def delete_user():
    if session.get('role') != 'admin':
        return redirect('/dashboard')

    username = request.form.get('username')
    if username:
        with sqlite3.connect('database.db', check_same_thread=False) as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM users WHERE username = ?', (username,))
            conn.commit()
    return redirect('/access')


@app.route('/changerole', methods=['POST'])
def change_role():
    if session.get('role') != 'admin':
        return redirect('/dashboard')
    
    username = request.form.get('username')
    new_role = request.form.get('role')
    if username and new_role:
        print(f"Changing role for {username} to {new_role}")
        with sqlite3.connect('database.db', check_same_thread=False) as conn:
            cur = conn.cursor()
            
            cur.execute('UPDATE users SET role = ? WHERE username = ?', (new_role, username))
            conn.commit()
    return redirect('/access')
            
@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user' not in session:
        return redirect('/login')

    username = request.form.get('username')
    new_password = request.form.get('new_password')

    if new_password:
        hashed = generate_password_hash(new_password, method="pbkdf2:sha256")
        with sqlite3.connect('database.db', check_same_thread=False) as conn:
            cur = conn.cursor()
            cur.execute('UPDATE users SET password = ? WHERE username = ?', (hashed, username))
            conn.commit()
        return redirect('/access')
    else:
        return "New password cannot be empty", 400





@app.route('/calendar', methods=['GET', 'POST'])
def calendar():
    if 'user' not in session:
        return redirect('/login')

    role = session.get('role')
    can_add = role in ['admin', 'purple']

    if request.method == 'POST' and can_add:
        title = request.form.get('title')
        date = request.form.get('date')
        time = request.form.get('time')

        if title and date:
            # Combine date and time if time is provided
            full_datetime = f"{date}T{time}" if time else date
            with sqlite3.connect('database.db', check_same_thread=False) as conn:
                cur = conn.cursor()
                cur.execute(
                    'INSERT INTO events (title, date, created_by) VALUES (?, ?, ?)',
                    (title, full_datetime, session['user'])
                )
                conn.commit()
            return redirect('/calendar')

    return render_template('calendar.html', can_add=can_add)
@app.route('/events')
def get_events():
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT title, date, created_by FROM events')
        events = cur.fetchall()

    # Convert to format FullCalendar expects
    event_list = [{
        "title": f"{e[0]} ({e[2]})",  # title (creator)
        "start": e[1]  # ISO date or datetime
    } for e in events]

    return json.dumps(event_list)
   
    
    
@app.route('/schedule')
def class_schedule():
    if 'user' not in session:
        return redirect('/login')
    return render_template('schedule.html')
@app.route('/class_events')
def class_events():
    import sqlite3
    from datetime import datetime, timedelta
    color_map = {
    'Austin': '#3498db',   # blue
    'Tyler': '#e67e22',    # orange
    'Parker': '#2ecc71',   # green
    'Colin': '#9b59b6'     # purple
}
    WEEKDAY_MAP = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4}
    start_date = datetime.strptime("2025-07-20", "%Y-%m-%d")  # Semester start
    weeks = 22

    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name, class_title, weekday, start_time, end_time FROM schedule")
        rows = cur.fetchall()

    events = []

    for row in rows:
        name, title, weekday, start_time, end_time = row
        weekday_num = WEEKDAY_MAP.get(weekday)
        if weekday_num is None:
            continue

        for i in range(weeks):
            class_date = start_date + timedelta(days=(weekday_num - start_date.weekday()) % 7 + i * 7)

            start_dt = datetime.combine(class_date.date(), datetime.strptime(start_time, "%H:%M").time())
            end_dt = datetime.combine(class_date.date(), datetime.strptime(end_time, "%H:%M").time())

            events.append({
                "title": f"{title} – {name}",
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "allDay": False,
                "color": color_map.get(name, "#95a5a6")
            })

    return json.dumps(events)



    
    



@app.route('/grocery', methods=['GET', 'POST'])
def grocery_list():
    if 'user' not in session:
        return redirect('/login')
    
    role = session.get('role')
    can_add = role in ['admin', 'purple']

    if request.method == 'POST' and can_add:
        item = request.form.get('item')
        user = get_user(session['user'])[1]  # Extract value from tuple
        with sqlite3.connect('database.db', check_same_thread=False) as conn:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO grocery (item, user) VALUES (?, ?)',
                (item, user)
            )
            conn.commit()
        return redirect(url_for('grocery_list'))
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM grocery')  # Assuming columns: id, item, user
        items = cur.fetchall()
    return render_template('grocery.html',items=items, can_add=can_add)

@app.route('/delete-item', methods=['POST'])
def delete_item():
    if 'user' not in session:
        return redirect('/login')

    item_id = request.form.get('item_id')
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM grocery WHERE id = ?', (item_id,))
        conn.commit()
    return redirect('/grocery')





@app.route('/utilities', methods=['GET', 'POST'])
def utilities():
    if session.get('role') != 'admin':
        return redirect('/dashboard')

    if request.method == 'POST':
        # Get form data
        month = request.form['month']
        utype = request.form['type']
        total = float(request.form['total'])
        

        # Save to DB
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO utilities (month, type, total) VALUES (?, ?, ?)',
                (month, utype, total)
            )
            conn.commit()

        # Get all roommates (non-admin)
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT username, email FROM users WHERE role != "admin"')
            users = cur.fetchall()

        # Send emails
        import yagmail
        yag = yagmail.SMTP("maphia.server@gmail.com", "fvxo qgaq kusy fspl")

        for username, email in users:
            share = round(total / 4, 2)
            subject = f"⚡ {utype} Bill – {month}"
            body = f"""
        Hey {username},

        This month's {utype} bill is ${total:.2f}.
        Your share: ${share:.2f}.

        Please pay by the end of the week – thanks!

        – Maphia Apartment Bot
        """
            yag.send(to=email, subject=subject, contents=body)

        return redirect('/utilities')

    # Load bills for display
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM utilities')
        bills = cur.fetchall()



    return render_template('utilities.html', bills=bills, )

@app.route('/polls')
def polls():
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, question FROM polls ORDER BY created_at DESC')
        poll_rows = cur.fetchall()

        polls_data = []
        for p in poll_rows:
            cur.execute('SELECT id, option_text FROM poll_options WHERE poll_id=?', (p[0],))
            options = cur.fetchall()
            option_data = []
            for opt in options:
                cur.execute('SELECT COUNT(*) FROM votes WHERE option_id=?', (opt[0],))
                count = cur.fetchone()[0]
                option_data.append({'id': opt[0], 'text': opt[1], 'votes': count})
            polls_data.append({'id': p[0], 'question': p[1], 'options': option_data})

    can_create = 'user' in session and session.get('role') in ['admin', 'purple']
    return render_template('polls.html', polls=polls_data, can_create=can_create)


@app.route('/create_poll', methods=['POST'])
def create_poll():
    if session.get('role') not in ['admin', 'purple']:
        return redirect('/dashboard')

    question = request.form.get('question')
    options = [request.form.get('option1'), request.form.get('option2'), request.form.get('option3'), request.form.get('option4')]
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('INSERT INTO polls (question, created_by) VALUES (?, ?)', (question, session['user']))
        poll_id = cur.lastrowid
        for opt in options:
            if opt:
                cur.execute('INSERT INTO poll_options (poll_id, option_text) VALUES (?, ?)', (poll_id, opt))
        conn.commit()
    return redirect('/polls')


@app.route('/vote', methods=['POST'])
def vote():
    if 'user' not in session:
        return redirect('/login')

    poll_id = request.form.get('poll_id')
    option_id = request.form.get('option_id')

    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM votes WHERE poll_id=? AND user=?', (poll_id, session['user']))
        cur.execute('INSERT INTO votes (poll_id, option_id, user) VALUES (?, ?, ?)', (poll_id, option_id, session['user']))
        conn.commit()
    return redirect('/polls')

@app.route('/music')
def music():
    if 'user' not in session:
        return redirect('/login')
    can_add = session.get('role') in ['admin', 'purple']
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, title FROM songs')
        songs = cur.fetchall()
    return render_template('music.html', songs=songs, can_add=can_add)


@app.route('/upload_music', methods=['POST'])
def upload_music():
    if session.get('role') not in ['admin', 'purple']:
        return redirect('/dashboard')
    file = request.files.get('file')
    title = request.form.get('title') or (file.filename if file else '')
    if file:
        os.makedirs('static/music', exist_ok=True)
        filename = secure_filename(file.filename)
        filepath = os.path.join('static', 'music', filename)
        file.save(filepath)
        with sqlite3.connect('database.db', check_same_thread=False) as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO songs (title, file_path) VALUES (?, ?)', (title, filepath))
            conn.commit()
    return redirect('/music')


@app.route('/play_music', methods=['POST'])
def play_music():
    if 'user' not in session:
        return redirect('/login')
    song_id = request.form.get('song_id')
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT file_path FROM songs WHERE id=?', (song_id,))
        row = cur.fetchone()
    if row:
        filepath = row[0]
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
        except Exception as e:
            print(f'Error playing music: {e}')
    return redirect('/music')



@app.route('/messages', methods=['GET', 'POST'] )
def messages():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            with sqlite3.connect('database.db', check_same_thread=False) as conn:
                cur = conn.cursor()
                cur.execute('INSERT INTO messages (user, message) VALUES (?, ?)', (session['user'], message))
                conn.commit()
            return redirect('/messages')

    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT user, message FROM messages ORDER BY id DESC')
        messages = cur.fetchall()

    return render_template('messages.html', messages=messages)

@app.route('/overview')
def overview():
    if 'user' not in session:
        role = None
    else:
        role = session.get('role')

    # Fetch today's weather
    import requests
    weather_api_key = 'your_openweathermap_api_key'
    city = 'YourCityName'
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric'
    response = requests.get(url)
    weather_data = response.json()

    if response.status_code == 200:
        weather_info = {
            'temp': weather_data['main']['temp'],
            'description': weather_data['weather'][0]['description'],
            'icon': weather_data['weather'][0]['icon']
        }
    else:
        weather_info = None
    # Get most recent poll
    latest_poll = None
    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute('SELECT id, question FROM polls ORDER BY created_at DESC LIMIT 1')
        row = cur.fetchone()
        if row:
            poll_id, question = row
            cur.execute('SELECT id, option_text FROM poll_options WHERE poll_id=?', (poll_id,))
            options = cur.fetchall()
            option_data = []
            for opt in options:
                cur.execute('SELECT COUNT(*) FROM votes WHERE option_id=?', (opt[0],))
                count = cur.fetchone()[0]
                option_data.append({'option_text': opt[1], 'votes': count})
            latest_poll = {'question': question, 'options': option_data}
    now = datetime.now()
    
    today = date.today()
    current_day = today.weekday()
    if current_day < 5:
        day = 'Weekday'
    elif current_day == 5:
        day = 'Saturday'
    else:
        day = 'Sunday'
          
    current_time = now.strftime('%H:%M')  # e.g., '15:45'
    

    with sqlite3.connect('database.db', check_same_thread=False) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM bus 
            WHERE day = ? AND time > ?
            ORDER BY time ASC
            LIMIT 1
        """, (day, current_time))
        next_bus = cur.fetchone()
        object = datetime.strptime(next_bus[2], "%H:%M")
        current_twelve = object.strftime("%#I:%M %p")

    return render_template('overview.html', weather=weather_info, role=role, latest_poll=latest_poll, next_bus=current_twelve)


# Bulb IPs
BULB_IPS = ["192.168.1.193", "192.168.1.194"]

async def apply_to_all(action):
    bulbs = [SmartBulb(ip) for ip in BULB_IPS]
    await asyncio.gather(*(bulb.update() for bulb in bulbs))
    await asyncio.gather(*(action(bulb) for bulb in bulbs))

@app.route("/lights")
def lights():
    return render_template("lights.html")

@app.route("/lights/on")
def lights_on():
    asyncio.run(apply_to_all(lambda b: b.turn_on()))
    return redirect(url_for('lights'))

@app.route("/lights/off")
def lights_off():
    asyncio.run(apply_to_all(lambda b: b.turn_off()))
    return redirect(url_for('lights'))

@app.route("/lights/brightness/<int:level>")
def lights_brightness(level):
    asyncio.run(apply_to_all(lambda b: b.set_brightness(level)))
    return ("", 204)  # No content for AJAX

@app.route("/lights/color/<hex_color>")
def lights_color(hex_color):
    # Convert hex (e.g., "ff0000") to HSV
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    hue = int(h * 360)        # 0–360
    sat = int(s * 100)        # 0–100

    async def set_color(bulb):
        await bulb.set_hsv(hue, sat, bulb.brightness)

    asyncio.run(apply_to_all(set_color))
    return ("", 204)

@app.route("/lights/hue/<int:hue>")
def lights_hue(hue):
    asyncio.run(apply_to_all(lambda b: b.set_hsv(hue, 100, b.brightness)))
    return ("", 204)

@app.route("/lights/saturation/<int:sat>")
def lights_saturation(sat):
    asyncio.run(apply_to_all(lambda b: b.set_hsv(b.hue, sat, b.brightness)))
    return ("", 204)


# --- INIT ---
if __name__ == '__main__':
    init_db()
    # Add a default admin if none exists
    if not get_user('admin'):
        add_user('admin', 'adminpass', 'admin')
    app.run(host='0.0.0.0', port=5000, debug=True)