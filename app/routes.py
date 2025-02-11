from app import app
from flask import Flask, Blueprint, request, render_template, redirect, url_for, jsonify, session, flash
import random


# Helper function to create a substitution cipher based on characters in the message
def generate_cipher(message):
    message_chars = set(char.upper() for char in message if char.isalpha())
    if len(message_chars) < 2:  # Ensure at least two unique letters
        return None
    available_chars = list(message_chars)
    random.shuffle(available_chars)
    cipher = dict(zip(message_chars, available_chars))
    return cipher

# Encrypt a message using the substitution cipher
def encrypt_message(message, cipher):
    if not cipher:
        return message  # Return original message if encryption is not possible
    message = message.upper()
    encrypted = ''.join(cipher.get(char, char) if char.isalpha() else char for char in message)
    return encrypted

# Decrypt a message using the substitution cipher
def decrypt_message(message, cipher):
    if not cipher:
        return message
    reverse_cipher = {v: k for k, v in cipher.items()}
    decrypted = ''.join(reverse_cipher.get(char, char) if char.isalpha() else char for char in message)
    return decrypted

# Swap two characters in the encrypted message
def swap_letters(text, letter1, letter2):
    translation_table = str.maketrans({letter1: letter2, letter2: letter1})
    return text.translate(translation_table)

# Check which letters are correctly placed
def get_correct_letters(encrypted_message, original_message):
    return {e: e for e, o in zip(encrypted_message, original_message) if e == o and e.isalpha()}

# Route for the cryptogram page
@app.route('/', methods=['GET', 'POST'])
def cryptogram_view():
    result = ""
    available_letters = []
    encrypted_message = session.get("encrypted_message", "")
    original_message = session.get("original_message", "")
    solver_mode = session.get("solver_mode", False)
    correct_letters = session.get("correct_letters", {})

    if request.method == 'POST':
        if "encrypt" in request.form and not solver_mode:
            message = request.form.get("message", "").strip()
            if not any(char.isalpha() for char in message):
                flash("Error: Message must contain at least two letters to be encrypted.", "error")
                return redirect(url_for('cryptogram_view'))
            
            cipher = generate_cipher(message)
            if not cipher:
                flash("Error: Unable to generate cipher. Please enter a valid message.", "error")
                return redirect(url_for('cryptogram_view'))
            
            encrypted_message = encrypt_message(message, cipher)
            session["cipher"] = cipher
            session["original_message"] = message.upper()
            session["encrypted_message"] = encrypted_message
            session["solver_mode"] = True  # Enter solver mode
            session["correct_letters"] = {}  # Reset correct letters
            return redirect(url_for('cryptogram_view'))
        elif "swap" in request.form and solver_mode:
            letter1 = request.form.get("letter1")
            letter2 = request.form.get("letter2")
            if letter1 and letter2 and encrypted_message:
                encrypted_message = swap_letters(encrypted_message, letter1, letter2)
                session["encrypted_message"] = encrypted_message
                session["correct_letters"] = get_correct_letters(encrypted_message, original_message)
                if encrypted_message == original_message:
                    session["solver_mode"] = False  # Exit solver mode after successful decryption
                return redirect(url_for('cryptogram_view'))
    
    if encrypted_message:
        available_letters = sorted(set(char for char in encrypted_message if char.isalpha()))
    
    return render_template("index.html", result=encrypted_message, available_letters=available_letters, encrypted_message=encrypted_message, solver_mode=solver_mode, correct_letters=session.get("correct_letters", {}))

# JavaScript and HTML will be needed for swapping letter buttons dynamically.
# Ensure that the HTML template contains buttons for available letters and a mechanism to submit swap requests.


