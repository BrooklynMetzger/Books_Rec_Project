from flask import Flask, render_template, request
import psycopg2

app = Flask(__name__)

DB_USER = "my_app_user"
DB_PASS = "books" # actual password
DB_HOST = "localhost"
DB_NAME = "books_proj_db" 

def get_db_connection():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
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