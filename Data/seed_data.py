import pandas as pd
import psycopg2
import re
import os
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from dotenv import load_dotenv

load_dotenv()
DetectorFactory.seed = 0  

def detect_language(text):
    if not text or pd.isna(text) or str(text).strip() == "":
        return "Unknown"
    try:
        return detect(str(text))
    except LangDetectException:
        return "Unknown"

def extract_value(row, possible_columns, default_val):
    #Checks the CSV row for any of the possible column names and returns the first match
    for col in possible_columns:
        if col in row.index and not pd.isna(row[col]):
            return str(row[col]).strip()
    return default_val

def seed_database(csv_filename):
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
         port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()

    print("Fetching existing titles from the database to prevent duplicates...")
    cursor.execute("SELECT Title FROM Book;")
    existing_titles = {row[0].strip().lower() for row in cursor.fetchall()}
    
    print(f"Reading {csv_filename}... (Auto-detecting columns)")
    try:
        #Read all columns as strings 
        df = pd.read_csv(csv_filename, dtype=str)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    books_added, books_skipped_dup, books_skipped_no_isbn = 0, 0, 0

    print("Scanning books and inserting...")
    for index, row in df.iterrows():
        #Standardize Title
        title = extract_value(row, ['title', 'Name'], 'Unknown Title')[:255]
        
        if title.lower() in existing_titles:
            books_skipped_dup += 1
            continue

        # Standardize & Clean Author
        raw_author = extract_value(row, ['author', 'authors', 'Authors'], 'Unknown Author')
        clean_author = re.sub(r'\s*\(.*?\)', '', raw_author).strip() # Removes (Goodreads Author), etc.
        author = clean_author[:255]

        #ISBN Check
        raw_isbn = extract_value(row, ['isbn13', 'isbn_13', 'ISBN', 'isbn', 'isbn10', 'isbn_10'], '')
        isbn = raw_isbn.replace("['", "").replace("']", "") 
        
        if not isbn or len(isbn) < 9 or isbn.lower() == 'nan':
            # Instantly skip if there is no valid ISBN
            books_skipped_no_isbn += 1
            continue

        existing_titles.add(title.lower())

        #Standardize everything else
        genre = extract_value(row, ['categories', 'genre', 'genres'], 'Unknown Genre')
        genre = genre.replace("['", "").replace("']", "")[:255]
        
        description = extract_value(row, ['description', 'summary', 'Description'], '')
        if description.lower() == 'nan': 
            description = ''
        
        thumbnail = extract_value(row, ['thumbnail', 'coverImg', 'image_url'], None)
        if thumbnail and thumbnail.lower() == 'nan': 
            thumbnail = None
        
        #Language handling
        language = extract_value(row, ['language', 'Language'], 'Unknown')
        if language.lower() in ['unknown', 'nan', '']:
            language = detect_language(description) if description else detect_language(title)
            
        if language in ['en', 'eng', 'en-US']: language = 'English'
        elif language in ['es', 'spa']: language = 'Spanish'
        elif language in ['fr', 'fre']: language = 'French'
        elif language in ['de', 'ger']: language = 'German'
        elif len(language) <= 3: language = language.upper()

        #Numbers and Dates
        try: pages = int(float(extract_value(row, ['num_pages', 'pages', 'page_count', 'Pages'], 0)))
        except: pages = 0
        
        date_published = extract_value(row, ['published_year', 'published_date', 'publishDate', 'PublishYear'], 'Unknown')[:50]
        if date_published.endswith('.0'): date_published = date_published[:-2] 
            
        try: rating = float(extract_value(row, ['average_rating', 'rating', 'Rating'], 0.0))
        except: rating = 0.0
        
        try: review_count = int(float(extract_value(row, ['ratings_count', 'CountsOfReview', 'numRatings'], 0)))
        except: review_count = 0

        #DATABASE INSERTS

        #Insert into Book table
        cursor.execute("""
            INSERT INTO Book (ISBN, Title, Author, Genre, Language, Pages, DatePublished, Thumbnail, Summary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ISBN) DO NOTHING;
        """, (isbn, title, author, genre, language, pages, date_published, thumbnail, description))

        #Insert into Review table
        cursor.execute("""
            INSERT INTO Review (ISBN, Rating, ReviewCount)
            VALUES (%s, %s, %s) RETURNING ReviewID;
        """, (isbn, rating, review_count))
        
        result = cursor.fetchone()
        if result:
            #Insert into Has table
            cursor.execute("""
                INSERT INTO Has (ReviewID, ISBN) VALUES (%s, %s) ON CONFLICT DO NOTHING;
            """, (result[0], isbn))

        books_added += 1
        if books_added % 500 == 0:
            conn.commit()
            print(f"--- Checkpoint: Saved {books_added} new books ---")

    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n=======================================================")
    print(f"SUCCESS: Total Books Added: {books_added}")
    print(f"SKIPPED: {books_skipped_dup} (Already in database)")
    print(f"REJECTED: {books_skipped_no_isbn} (No ISBN in CSV)")
    print("=======================================================")

if __name__ == "__main__":
    print("Seeding Database with 4 csv files.")
    seed_database("books_1.Best_Books_Ever.csv")

    # books_1.Best_Books_Ever.csv is the largest source of data
    # The other calls are there if you would like to add more data
    # Just download them then uncomment the calls below

    #print("book1.Best_Books_Ever down next google_books")
    #seed_database("google_books_dataset.csv")
    #print("Google done next books")
    #seed_database("books.csv")
    #print("books done time for data")
    #seed_database("data.csv")