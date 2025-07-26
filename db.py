
# db.py - Simulated in-memory database

# Global list to store messages
chat_history = []

def insert_message(user_input, bot_response):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_history.append((user_input, bot_response, timestamp))

def get_all_messages():
    return chat_history
