from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv
import re
from collections import Counter
import math

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

ADMIN_ID = "0000"

#genres for filter drop down
GENRES = ["Fiction", "Non-Fiction", "Thriller", "Romance", "Fantasy", "Horror", "Mystery", "Science Fiction", "Biography"]
STOP_WORDS = {"this", "that", "with", "from", "your", "have", "about", "which", 
              "their", "they", "were", "what", "there", "when", "would", "will", 
              "book", "novel", "story", "read", "author", "because"}

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

#separate route for admin login box
@app.route('/admin_login', methods=['POST'])
def admin_login():
    admin_id = request.form.get('admin_id', '').strip()

    if admin_id == ADMIN_ID:
        session['user_id'] = ADMIN_ID
        return redirect(url_for('admin_page'))
    else:
        #incorrect id
        return redirect(url_for('login'))
    
#logout routing
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    books = []
    current_page = 1
    total_pages = 0

    search_query = request.form.get('search_query', '').strip()
    author_query = request.form.get('author_query', '').strip()
    genre_query = request.form.get('genre_query', '').strip()
    isbn_query = request.form.get('isbn_query', '').strip()
    min_rating = request.form.get('min_rating', '').strip() 
    publish_date_query = request.form.get('publish_date_query', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        current_page = int(request.form.get('page', 1))

        # Base SQL
        sql = """
            SELECT b.Title, b.Author, b.Thumbnail, b.ISBN
            FROM Book b
            LEFT JOIN Review r ON b.ISBN = r.ISBN
        """
        count_sql = """
            SELECT COUNT(*)
            FROM Book b
            LEFT JOIN Review r ON b.ISBN = r.ISBN
        """
        
        conditions = []
        params = []

        if search_query:
            conditions.append("b.Title ILIKE %s")
            params.append(f"%{search_query}%")
        if author_query:
            conditions.append("b.Author ILIKE %s")
            params.append(f"%{author_query}%")
        if genre_query:
            conditions.append("b.Genre ILIKE %s")
            params.append(f"%{genre_query}%")
        if isbn_query:
            conditions.append("b.ISBN ILIKE %s") 
            params.append(f"%{isbn_query}%") 
        if publish_date_query:
            conditions.append("b.DatePublished ILIKE %s")
            params.append(f"%{publish_date_query}%")
        if min_rating:
            try:
                conditions.append("r.Rating >= %s")
                params.append(float(min_rating))
            except ValueError:
                pass 

        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            sql += where_clause
            count_sql += where_clause
        
        # Calculate total pages for pagination with 15 books per page
        cursor.execute(count_sql, tuple(params))
        total_books = cursor.fetchone()[0]
        books_per_page = 15
        total_pages = math.ceil(total_books / books_per_page)

        # Pagination
        offset = (current_page - 1) * books_per_page
        sql += " LIMIT %s OFFSET %s;" 
        
        main_params = list(params)
        main_params.extend([books_per_page, offset])

        cursor.execute(sql, tuple(main_params))
        books = cursor.fetchall()

    # Fetch saved books for the dropdown
    cursor.execute("""
        SELECT b.ISBN, b.Title
        FROM Book b
        JOIN Saves s ON b.ISBN = s.ISBN
        WHERE s.UserID = %s
        ORDER BY b.Title ASC
    """, (session['user_id'],))
    saved_books = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('index.html', books=books, 
            search_query=search_query, author_query=author_query, 
            genre_query=genre_query, isbn_query=isbn_query, 
            min_rating=min_rating, publish_date_query=publish_date_query,
            genres=GENRES, user_id=session['user_id'],
            saved_books=saved_books, current_page=current_page, total_pages=total_pages)

# recommendation route
@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    base_isbn = request.args.get('base_isbn')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    offset = (page - 1) * per_page
    
    if not base_isbn:
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch saved books to select from
    cursor.execute("""
        SELECT b.ISBN, b.Title FROM Book b
        JOIN Saves s ON b.ISBN = s.ISBN
        WHERE s.UserID = %s ORDER BY b.Title ASC
    """, (user_id,))
    saved_books = cursor.fetchall()
    
    # Fetch data for the selected book
    cursor.execute("SELECT Title, Author, Genre, Summary FROM Book WHERE ISBN = %s", (base_isbn,))
    book_data = cursor.fetchone()
    
    if not book_data:
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    # Target data for recommendation filter
    target_title, target_author, target_genre, target_summary = book_data

    # Get keywords
    text_for_keywords = f"{target_title} {target_summary}" if target_summary else target_title
    words = re.findall(r'\b[a-z0-9]{4,}\b', text_for_keywords.lower())
    meaningful_words = [w for w in words if w not in STOP_WORDS]
    word_counts = Counter(meaningful_words)
    top_keywords = [word for word, count in word_counts.most_common(3)]

    # Create conditions
    conditions = []
    params = []
    if target_author:
        conditions.append("b.Author = %s")
        params.append(target_author)
    if target_genre:
        conditions.append("b.Genre = %s")
        params.append(target_genre)
    for kw in top_keywords:
        conditions.append("(b.Title ILIKE %s OR b.Summary ILIKE %s)")
        params.extend([f"%{kw}%", f"%{kw}%"])
    
    where_clause = " (" + " OR ".join(conditions) + ") "
    where_clause += " AND b.ISBN != %s"
    params.append(base_isbn)
    where_clause += " AND b.ISBN NOT IN (SELECT ISBN FROM Saves WHERE UserID = %s)"
    params.append(user_id)

    cursor.execute(f"SELECT COUNT(DISTINCT b.ISBN) FROM Book b WHERE {where_clause}", tuple(params))
    total_results = cursor.fetchone()[0]
    total_pages = (total_results + per_page - 1) // per_page

    author_order_sql = "CASE WHEN b.Author = %s THEN 0 ELSE 1 END"
    order_params = [target_author] if target_author else []
    
    sql = f"""
        SELECT b.Title, b.Author, b.Thumbnail, b.ISBN 
        FROM Book b
        LEFT JOIN Review r ON b.ISBN = r.ISBN
        WHERE {where_clause}
        GROUP BY b.ISBN, b.Title, b.Author, b.Thumbnail
        ORDER BY {author_order_sql if target_author else '1'}, AVG(r.Rating) DESC NULLS LAST, b.ISBN ASC
        LIMIT %s OFFSET %s
    """
    
    cursor.execute(sql, tuple(params + order_params + [per_page, offset]))
    recommended_books = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    rec_message = f"Found {total_results} recommendations for '{target_title}'"
    
    return render_template('index.html', 
                           books=recommended_books, 
                           rec_message=rec_message, 
                           genres=GENRES, 
                           user_id=user_id, 
                           saved_books=saved_books,
                           current_page=page, 
                           total_pages=total_pages, 
                           base_isbn=base_isbn)

#saved books routing
@app.route('/saved_books')
def saved_books():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.Title, b.Author, b.Thumbnail, b.ISBN
        FROM Book b
        JOIN Saves s ON b.ISBN = s.ISBN
        WHERE s.UserID = %s;
    """, (user_id,))
    books = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('saved_books.html', books=books, user_id=user_id)

#delete book from saves route
@app.route('/delete_book', methods=['POST'])
def delete_book():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json()
    isbn = data.get('isbn')
    user_id = session['user_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Saves WHERE UserID = %s AND ISBN = %s;", (user_id, isbn))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Removed"}), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

#save book route
@app.route('/save_book', methods=['POST'])
def save_book():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    isbn = data.get('isbn')
    user_id = session['user_id']

    if not isbn:
        return jsonify({"error": "ISBN not provided"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM Saves WHERE UserID = %s AND ISBN = %s;",
            (user_id, isbn)
        )
        already_saved = cursor.fetchone()
        if already_saved:
            cursor.close()
            conn.close()
            return jsonify({"error": "Book already saved"}), 200
        
        #ensure user exists in user table
        cursor.execute("SELECT 1 FROM \"User\" WHERE UserID = %s;", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO \"User\" (UserID) VALUES (%s);", (user_id,))
            
        cursor.execute(
             "INSERT INTO Saves (UserID, ISBN) VALUES (%s, %s);",
                (user_id, isbn)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Saved"}), 200
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500
        

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
