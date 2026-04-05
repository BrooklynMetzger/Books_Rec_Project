from flask import Flask, render_template, request, session, redirect, url_for, jsonify
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

ADMIN_ID = "admin"

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

            cursor.execute("SELECT UserID FROM \"User\" WHERE UserID = %s;", (user_id,))
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

#logout routing
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
def index():

    #send back to login if a user is not logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
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

    return render_template('index.html', books=books, search_query=search_query, user_id=session['user_id'])

#admin page
@app.route('/add_book', methods=['POST'])
def add_book():
    if session.get('user_id') != ADMIN_ID:
        return jsonify({"error": "Unauthorized. Admin access only"}), 403
        
    conn = None
    cursor = None
    data = request.get_json()

    isbn = data.get('isbn')
    title = data.get('title')
    author = data.get('author')
    genre = data.get('genre')
    language = data.get('language')
    pages= data.get('pages')
    date_published = data.get('date')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(""" 
                    INSERT INTO Book (ISBN, Title, Author, Genre, Language, Pages, DatePublished) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                    """, (isbn, title, author, genre, language, pages, date_published))
        
        conn.commit()
        return jsonify({"message" : "Book added"}), 200
    except Exception as ex:
        if conn:
            conn.rollback()
        return jsonify({"error": str(ex)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/admin')
def admin_page():
    if session.get('user_id') != ADMIN_ID:
        return redirect(url_for('login'))
    return render_template('admin.html')


if __name__ == '__main__':
    # Runs the app in debug mode on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)
