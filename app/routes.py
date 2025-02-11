from app import app
from flask import Flask, Blueprint, request, render_template, redirect, url_for, jsonify
import random


def generate_cipher(message):
    message_chars = set(char.upper() for char in message if char.isalpha())
    available_chars = list(message_chars)
    random.shuffle(available_chars)
    cipher = dict(zip(message_chars, available_chars))
    return cipher

# Encrypt a message using the substitution cipher
def encrypt_message(message, cipher):
    message = message.upper()
    encrypted = ''.join(cipher.get(char, char) if char.isalpha() else char for char in message)
    return encrypted

# Decrypt a message using the substitution cipher
def decrypt_message(message, cipher):
    reverse_cipher = {v: k for k, v in cipher.items()}
    decrypted = ''.join(reverse_cipher.get(char, char) if char.isalpha() else char for char in message)
    return decrypted

# Swap two characters in the encrypted message
def swap_letters(text, letter1, letter2):
    translation_table = str.maketrans({letter1: letter2, letter2: letter1})
    return text.translate(translation_table)

# Route for the cryptogram page
@app.route('/', methods=['GET', 'POST'])
def cryptogram_view():
    result = ""
    encrypted_message = request.form.get("encrypted_message", "")
    available_letters = sorted(set(char for char in encrypted_message if char.isalpha()))

    if request.method == 'POST':
        message = request.form.get("message", "")
        if "encrypt" in request.form and message:
            cipher = generate_cipher(message)
            encrypted_message = encrypt_message(message, cipher)
            available_letters = sorted(set(char for char in encrypted_message if char.isalpha()))
            result = encrypted_message
        elif "swap" in request.form:
            letter1 = request.form.get("letter1")
            letter2 = request.form.get("letter2")
            if letter1 and letter2 and encrypted_message:
                encrypted_message = swap_letters(encrypted_message, letter1, letter2)
                available_letters = sorted(set(char for char in encrypted_message if char.isalpha()))
                result = encrypted_message
        else:
            result = encrypted_message  # Preserve the last encrypted message instead of overwriting it
    
    return render_template("index.html", result=result, available_letters=available_letters, encrypted_message=encrypted_message)

# JavaScript and HTML will be needed for swapping letter buttons dynamically.
# Ensure that the HTML template contains buttons for available letters and a mechanism to submit swap requests.





