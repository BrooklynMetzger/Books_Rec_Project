BOOK DATABASE SETUP & SEEDING GUIDE

PREREQUISITES
-----------------------------------------------------------
Make sure you have Python and PostgreSQL installed.
Install the required Python libraries by running:
    
    pip install pandas psycopg2-binary langdetect requests python-dotenv

Need to make a .env file in root directory in this style since the github is public
    DB_USER=your_postgres_username  // update both USER and PASS fields
    DB_PASS=your_postgres_password // with your username and password
    DB_HOST=localhost
    DB_PORT=5433 //or whatever your port number is
    DB_NAME=books_proj_db // can be named anything you want  
    SECRET_KEY=dev-secret-key //for flask to work, not for data seeding

Download books_1.Best_Books_Ever.csv as main data file used from googledrive
Other files are there if extra data is wanted 
Put them in Data folder
https://drive.google.com/drive/folders/1Caobhx38DKTPC_wno7G9A5Ywrnf1MpBQ?usp=sharing       

FILE PREPARATION
-----------------------------------------------------------
Make sure you are in the Data folder
STEP 1: CREATE THE DATABASE STRUCTURE
-----------------------------------------------------------
Run the setup script. This will create the 'books_proj_db' 
database and all tables (Book, Review, User, etc.).

    python setup_db.py

Expected output: "Database and Tables created successfully!"

SEED THE DATA
-----------------------------------------------------------
Run the seeder script. 
    python seed_data.py

The script will:
    - Skip books without an ISBN.
    - Prevent duplicate titles.
    - Auto-detect languages if missing.
    - Link books to their ratings/reviews automatically.

DATABASE SCHEMA REFERENCE
-------------------------------------------
- User(UserID)
- Admin(UserID) -> Links to User
- Book(ISBN, Title, Author, Genre, Language, Pages, 
       DatePublished, Summary, Thumbnail) // added summary and thumbnail
- Review(ReviewID, ISBN, Rating, ReviewCount) // reviewText became ReviewCount
- Has(ReviewID, ISBN) -> Links Reviews to Books
- Saves, Searches, AddBook -> Junction tables for User-Book interactions

VERIFICATION
-------------------------------------------
Check if data loaded correctly:
    sudo -u postgres psql -d books_proj_db

Run this to see a sample of joined data:
    SELECT b.Title, b.Author, r.Rating 
    FROM Book b 
    JOIN Review r ON b.ISBN = r.ISBN 
    LIMIT 10;