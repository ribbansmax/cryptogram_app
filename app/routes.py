from app import app
from flask import Flask, Blueprint, request, render_template, redirect, url_for, jsonify, session, flash
import random
import sqlite3
import base64
import json

# Initialize SQLite database
def init_db():
    with sqlite3.connect("cryptograms.db") as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS cryptograms 
                     (id TEXT PRIMARY KEY, encrypted TEXT, cipher TEXT, original TEXT)''')
        conn.commit()

init_db()

# Helper function to create a substitution cipher based on characters in the message
def generate_cipher(message):
    message_chars = list(set(char.upper() for char in message if char.isalpha()))
    if len(message_chars) < 2:  # Ensure at least two unique letters
        return None

    while True:
        shuffled_chars = message_chars[:]  # Copy the list
        random.shuffle(shuffled_chars)  # Shuffle the characters
        
        # Check if any character maps to itself
        if all(original != shuffled for original, shuffled in zip(message_chars, shuffled_chars)):
            return dict(zip(message_chars, shuffled_chars))  # Only return if valid

# Encrypt a message using the substitution cipher
def encrypt_message(message, cipher):
    if not cipher:
        return message  # Return original message if encryption is not possible
    message = message.upper()
    encrypted = ''.join(cipher.get(char, char) if char.isalpha() else char for char in message)
    return encrypted

# Generate a short, URL-safe ID
def generate_short_id():
    return base64.urlsafe_b64encode(random.getrandbits(24).to_bytes(3, 'big')).decode().rstrip('=')

# Route for the cryptogram page
@app.route('/', methods=['GET', 'POST'])
def cryptogram_view():
    result = ""
    available_letters = []
    encrypted_message = session.get("swapped_message", session.get("encrypted_message", ""))
    solver_mode = session.get("solver_mode", False)
    correct_letters = session.get("correct_letters", {})
    short_url = None

    if request.method == 'POST':
        if "encrypt" in request.form and not solver_mode:
            message = request.form.get("message", "").strip()
            if not any(char.isalpha() for char in message):
                flash("Error: Message must contain at least one letter to be encrypted.", "error")
                return redirect(url_for('cryptogram_view'))
            
            cipher = generate_cipher(message)
            if not cipher:
                flash("Error: Message must contain at least two unique letters to be encrypted.", "error")
                return redirect(url_for('cryptogram_view'))
            
            encrypted_message = encrypt_message(message, cipher)
            short_id = generate_short_id()

            # Store in database
            with sqlite3.connect("cryptograms.db") as conn:
                c = conn.cursor()
                c.execute("INSERT INTO cryptograms (id, encrypted, cipher, original) VALUES (?, ?, ?, ?)",
                          (short_id, encrypted_message, json.dumps(cipher), message.upper()))
                conn.commit()

            short_url = url_for('solver_view', short_id=short_id, _external=True)
            flash(f'Share this link: <a href="{short_url}" target="_blank">{short_url}</a>', "success")
            # return redirect(short_url)  # Redirect user to solver mode

        elif "swap" in request.form and solver_mode:
            letter1 = request.form.get("letter1")
            letter2 = request.form.get("letter2")
            if letter1 and letter2 and encrypted_message:
                swapped_message = session.get("swapped_message", encrypted_message)

                # Perform the letter swap
                translation_table = str.maketrans({letter1: letter2, letter2: letter1})
                swapped_message = swapped_message.translate(translation_table)

                # Update swapped message in session
                session["swapped_message"] = swapped_message

                # Recalculate correct letters
                correct_letters = {}
                original_message = session.get("original_message", "")

                if original_message:
                    for i, char in enumerate(swapped_message):
                        if char.isalpha() and char == original_message[i]:
                            correct_letters[char] = True  # Mark as correct

                session["correct_letters"] = correct_letters  # Store updated correct letters

                print(f"Swapped Message: {session.get('swapped_message', '')}, Original Message: {session.get('encrypted_message', '')}, Correct Letters: {session.get('correct_letters', {})}")

                return redirect(url_for('cryptogram_view', short_id=session.get("short_id")))



    if "short_id" in request.args:
        short_id = request.args.get("short_id")
        with sqlite3.connect("cryptograms.db") as conn:
            c = conn.cursor()
            c.execute("SELECT encrypted, original FROM cryptograms WHERE id = ?", (short_id,))
            row = c.fetchone()
            if row:
                encrypted_message = row[0]
                session["encrypted_message"] = encrypted_message
                session["swapped_message"] = encrypted_message
                session["original_message"] = original_message
                session["solver_mode"] = True
                session["short_id"] = short_id

    if encrypted_message:
        available_letters = sorted(set(char for char in encrypted_message if char.isalpha()))
    
    return render_template("index.html", short_url=short_url, result=encrypted_message, 
                           available_letters=available_letters, encrypted_message=encrypted_message, 
                           solver_mode=solver_mode, correct_letters=session.get("correct_letters", {}))


@app.route('/solve/<short_id>')
def solver_view(short_id):
    session.clear()

    with sqlite3.connect("cryptograms.db") as conn:
        c = conn.cursor()
        c.execute("SELECT encrypted, cipher, original FROM cryptograms WHERE id = ?", (short_id,))
        row = c.fetchone()

        if row is None:
            flash("Error: Cryptogram not found.", "error")
            return redirect(url_for('cryptogram_view'))

        encrypted_message, cipher, original_message = row
        cipher = json.loads(cipher)

        # Store values in session
        session["encrypted_message"] = encrypted_message
        session["cipher"] = cipher
        print(original_message)
        session["original_message"] = original_message
        session["solver_mode"] = True
        session["correct_letters"] = {}

    return redirect(url_for('cryptogram_view'))

@app.route('/reset')
def reset_session():
    session.clear()  # Clears all session data
    flash("Session has been reset.", "info")
    return redirect(url_for('cryptogram_view'))
