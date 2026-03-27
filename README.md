# Book Database Project

## Tech Stack
* **Language:** Python 3.8+
* **Database:** PostgreSQL
* **Libraries:**
    * `psycopg2-binary`: For PostgreSQL database communication
    * `pandas`: For high-performance CSV data manipulation
    * `python-dotenv`: For managing environment variables (.env)
    * `langdetect`: For automatic language identification of book entries

## Structure
    .
    ├── .env                # Private database credentials (NOT tracked by Git)
    ├── .gitignore          # Tells Git to ignore .env, CSVs, and cache
    ├── README.md           # Project documentation
    |── Data                # Folder with database setup scripts
    |  ├── setup_db.py      # Script to create Database and Tables
    |  ├── seed_data.py     # Script to clean and import CSV data
    |  |── db_helpers.py    # Functions for the backend to query data
    |  └── README.txr       # How to setup database, .env and download data
    |─ template             # Where all html files will go with flask
    |  └─── index.html
    └─ app.py               # Main app run to start server

## Features

* **Automated Schema Creation:** Quickly builds a relational schema including Books, Reviews, Users, and junction tables.
* **Multi-Source Seeding:** Processes mutiple data sources in one execution.
* **Data Cleaning:** Handles duplicate titles, cleans author names, and enforces strict ISBN validation.
* **Secure:** Keeps sensitive database credentials out of version control using `.env` files.

## Getting Started

### 1. Clone the Repository
git clone <your-repo-url>
cd <your-repo-name>
### 2. Create python .venv (virtual envierment)
python3 -m venv venv_name
source venv_name/bin/activate
### 3. Read README.txt in Data folder and follow steps
### 4. Once database is seeded run app.py to start application
python app.py