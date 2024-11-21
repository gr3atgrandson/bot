import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import sqlite3
from datetime import datetime
import math

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Haversine formula to calculate distance between two coordinates
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371 * c  # Radius of Earth in kilometers
    return distance

# Database connection
def connect_db():
    return sqlite3.connect('dating_bot.db')

# Start command - registers a new user
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Welcome to the Dating Bot! Type /register to start your profile.")

# Register command - collects user's name and birthdate
def register(update: Update, context: CallbackContext):
    update.message.reply_text("Please enter your name.")
    return "NAME"

# Handle name input
def handle_name(update: Update, context: CallbackContext):
    name = update.message.text
    context.user_data['name'] = name
    update.message.reply_text("Please enter your date of birth (YYYY-MM-DD).")
    return "DOB"

# Handle date of birth input
def handle_dob(update: Update, context: CallbackContext):
    dob = update.message.text
    try:
        # Check if the date format is valid
        birth_date = datetime.strptime(dob, '%Y-%m-%d')
        context.user_data['dob'] = birth_date
        age = (datetime.now() - birth_date).days // 365  # Calculate age
        update.message.reply_text(f"Your age is {age}.")
        update.message.reply_text("Please select your gender: Male, Female, Other.")
        return "GENDER"
    except ValueError:
        update.message.reply_text("Invalid date format. Please use YYYY-MM-DD.")
        return "DOB"

# Handle gender input
def handle_gender(update: Update, context: CallbackContext):
    gender = update.message.text.lower()
    context.user_data['gender'] = gender
    user_id = update.message.from_user.id
    name = context.user_data['name']
    dob = context.user_data['dob']
    # Save user to database
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (user_id, name, dob, gender) VALUES (?, ?, ?, ?)",
                   (user_id, name, dob, gender))
    conn.commit()
    conn.close()
    update.message.reply_text("Registration complete! You can now start finding matches using /find_matches.")
    return "DONE"

# Find matches based on location
def find_matches(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT location_lat, location_lon FROM users WHERE user_id = ?", (user_id,))
    user_location = cursor.fetchone()
    if user_location:
        user_lat, user_lon = user_location
        cursor.execute("SELECT user_id, name, location_lat, location_lon FROM users WHERE user_id != ?", (user_id,))
        matches = []
        for match in cursor.fetchall():
            match_id, match_name, match_lat, match_lon = match
            distance = haversine(user_lat, user_lon, match_lat, match_lon)
            if distance <= 50:  # Only show matches within 50km
                matches.append(f"{match_name}: {distance:.2f} km away")
        if matches:
            update.message.reply_text("\n".join(matches))
        else:
            update.message.reply_text("No matches found within 50 km.")
    else:
        update.message.reply_text("Please share your location first using /share_location.")
    conn.close()

# Handle location sharing
def share_location(update: Update, context: CallbackContext):
    location_button = KeyboardButton("Share Location", request_location=True)
    reply_markup = ReplyKeyboardMarkup([[location_button]], one_time_keyboard=True)
    update.message.reply_text("Please share your location so we can find matches near you.", reply_markup=reply_markup)

# Save location
def handle_location(update: Update, context: CallbackContext):
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude
    user_id = update.message.from_user.id
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET location_lat = ?, location_lon = ? WHERE user_id = ?",
                   (latitude, longitude, user_id))
    conn.commit()
    conn.close()
    update.message.reply_text("Your location has been saved.")

# Main function to start the bot
def main():
    updater = Updater("7708412147:AAHn53-AMuRbykqGQ__Lvro_mIlLuNbYgrM", use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("register", register))
    dp.add_handler(CommandHandler("find_matches", find_matches))
    dp.add_handler(CommandHandler("share_location", share_location))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_name))  # Handle name input
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_dob))   # Handle DOB input
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_gender))  # Handle gender input
    dp.add_handler(MessageHandler(Filters.location, handle_location))  # Handle location sharing

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
