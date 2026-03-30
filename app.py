from flask import Flask, render_template, request
import psycopg2

import os
from pathlib import Path
from dotenv import load_dotenv

app = Flask(__name__)

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

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