import os
from dotenv import load_dotenv
import psycopg2

#Load the variables from .env
load_dotenv()

#Use os.getenv to pull the values
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

def setup_database():
    try:
        #Connect to the default 'postgres' database first to create our app database
        conn = psycopg2.connect(dbname="postgres", user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        conn.autocommit = True
        cursor = conn.cursor()

        #Create the database if it doesn't exist
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            print(f"Creating database {DB_NAME}...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
        
        cursor.close()
        conn.close()

        #Now connect to actual project database to create tables
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        cursor = conn.cursor()

        print("Creating tables...")

        #SQL Schema 
        sql_commands = [
            """DROP TABLE IF EXISTS Has, AddBook, Searches, Saves, Review, Admin, "User", Book CASCADE;""",
            
            """CREATE TABLE "User" (
                UserID SERIAL PRIMARY KEY
            );""",

            """CREATE TABLE Admin (
                UserID INT PRIMARY KEY REFERENCES "User"(UserID)
            );""",

            """CREATE TABLE Book (
                ISBN VARCHAR(20) PRIMARY KEY,
                Title VARCHAR(255) NOT NULL,
                Author VARCHAR(255),
                Genre VARCHAR(255),
                Language VARCHAR(100),
                Pages INT,
                DatePublished VARCHAR(50),
                Summary TEXT,
                Thumbnail TEXT
            );""",

            """CREATE TABLE Review (
                ReviewID SERIAL PRIMARY KEY,
                ISBN VARCHAR(20) REFERENCES Book(ISBN),
                Rating DECIMAL(3,2),
                ReviewCount INT
            );""",

            """CREATE TABLE Saves (
                UserID INT REFERENCES "User"(UserID),
                ISBN VARCHAR(20) REFERENCES Book(ISBN),
                PRIMARY KEY (UserID, ISBN)
            );""",

            """CREATE TABLE Searches (
                UserID INT REFERENCES "User"(UserID),
                ISBN VARCHAR(20) REFERENCES Book(ISBN),
                PRIMARY KEY (UserID, ISBN)
            );""",

            """CREATE TABLE AddBook (
                UserID INT REFERENCES "User"(UserID),
                ISBN VARCHAR(20) REFERENCES Book(ISBN),
                PRIMARY KEY (UserID, ISBN)
            );""",

            """CREATE TABLE Has (
                ReviewID INT REFERENCES Review(ReviewID),
                ISBN VARCHAR(20) REFERENCES Book(ISBN),
                PRIMARY KEY (ReviewID, ISBN)
            );"""
        ]

        for command in sql_commands:
            cursor.execute(command)

        conn.commit()
        print("Database and Tables created successfully!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_database()