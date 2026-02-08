import sqlite3
import atexit

# make the starboard table if it doesnt exist
def init_db():
    conn = sqlite3.connect('starboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS starboard_messages (
            original_msg_id INTEGER PRIMARY KEY,
            starboard_msg_id INTEGER,
            guild_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# get a connection to the db
def get_db():
    conn = sqlite3.connect('starboard.db')
    conn.row_factory = sqlite3.Row
    return conn

# close stuff when exiting
@atexit.register
def close_db():
    if 'db' in globals():
        globals()['db'].close()
