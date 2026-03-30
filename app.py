from flask import Flask, render_template, request, session, redirect, url_for
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

app = Flask(__name__)

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

#secret key needed for Flask sessions to function
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

#login page routing
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()

        if user_id:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT UserID FROm \"User\" WHERE UserID = %s;", (user_id,))
            user = cursor.fetchone()

            if user:
                #if user exists, log in
                session['user_id'] = user_id
            else:
                #user dne, create new user and log them in
                cursor.execute("INSERT INTO \"User\" (UserID) VALUES (%s);", (user_id,))
                conn.commit()
                session['user_id'] = user_id
            
            cursor.close()
            conn.close()

            return redirect(url_for('index'))
        
    return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def index():
    books = []
    search_query = ""

    if request.method == 'POST':
        search_query = request.form.get('search_query', '')
        
        if search_query:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # ILIKE allows for case-insensitive searching. 
            # % are wildcards
            cursor.execute("""
                SELECT Title, Author, Thumbnail 
                FROM Book 
                WHERE Title ILIKE %s 
                LIMIT 12;
            """, (f"%{search_query}%",))
            
            books = cursor.fetchall()
            
            cursor.close()
            conn.close()

    return render_template('index.html', books=books, search_query=search_query)

if __name__ == '__main__':
    # Runs the app in debug mode on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)