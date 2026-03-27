import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST")
    )

def search_books_by_title(search_query):
    """
    Searches the database for books matching the title
    """
    conn = get_connection()
    
    # RealDictCursor automatically maps column names to the data
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
 
    sql_query = """
        SELECT 
            b.ISBN, 
            b.Title, 
            b.Author, 
            b.Genre, 
            b.Language, 
            b.Pages,
            b.Summary, 
            b.DatePublished, 
            b.Thumbnail,
            r.Rating, 
            r.ReviewCount
        FROM Book b
        LEFT JOIN Review r ON b.ISBN = r.ISBN
        WHERE b.Title ILIKE %s
        ORDER BY r.ReviewCount DESC NULLS LAST
        LIMIT 20;
    """
    
    #Execute the query
    formatted_search = f"%{search_query}%"
    cursor.execute(sql_query, (formatted_search,))
    
    #Fetch all matching books
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Convert the results from RealDictRow objects to standard lists/dicts
    return [dict(row) for row in results]

#Test
if __name__ == "__main__":
    test_title = input("Enter a book title to search for: ")
    books_found = search_books_by_title(test_title)
    
    if not books_found:
        print("No books found matching that title.")
    else:
        print(f"\nFound {len(books_found)} result(s):\n")
        for book in books_found:
            summary_text = book['summary']
            if summary_text and summary_text != 'nan':
                snippet = summary_text[:120] + "..."
            else:
                snippet = "No summary available."

            print(f"📖 {book['title']}")
            print(f"   Author: {book['author']}")
            print(f"   Rating: {book['rating']} ({book['reviewcount']} reviews)")
            print(f"   Summary: {snippet}")
            print(f"   Cover:  {book['thumbnail']}")
            print("-" * 40)