
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_mail import Mail, Message
import os
import random
import cv2
import base64
import numpy as np
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a strong secret key

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'adepuneha20@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'ymvw guqw wpfe dfyv'  # Update with your app password
mail = Mail(app)

# OpenCV face detection using Haar Cascade
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def send_otp(email, otp):
    msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[email])
    msg.body = f'Your OTP code is: {otp}'
    mail.send(msg)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        session['email'] = email  # Store email in session
        return redirect(url_for('capture'))
    return render_template('register.html')

@app.route('/capture', methods=['GET', 'POST'])
def capture():
    if request.method == 'POST':
        data = request.get_json()
        images = data.get('images')

        # Directory to save images
        save_dir = 'captured_images'
        os.makedirs(save_dir, exist_ok=True)

        for i, img_data in enumerate(images):
            # Save image as a file
            img_name = f"{session['email']}_image_{i+1}.png"
            img_path = os.path.join(save_dir, img_name)
            img_data = img_data.split(",")[1]  # Remove metadata
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(img_data))

        flash('You have successfully submitted your images. Now go to the home page and start the quiz.')
        return jsonify({'success': True})

    return render_template('face_capture.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        session['name'] = name
        session['email'] = email
        otp = random.randint(1000, 9999)
        session['otp'] = otp
        send_otp(email, otp)
        flash(f"An OTP has been sent to {email}. Please check your email.")
        return redirect(url_for('otp'))
    return render_template('signin.html')

@app.route('/otp', methods=['GET', 'POST'])
def otp():
    if request.method == 'POST':
        return redirect(url_for('verify_otp'))
    return render_template('otp.html')

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    otp = request.form['otp']
    if int(otp) == session.get('otp'):
        return redirect(url_for('instructions'))
    else:
        flash("Invalid OTP", "error")
        return redirect(url_for('otp'))

@app.route('/instructions')
def instructions():
    return render_template('start_quiz.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        correct_answers = {
            "q1": "A",
            "q2": "A",
            "q3": "A",
            "q4": "B",
            "q5": "B"
        }
        answers = request.form
        score = sum(1 for question, correct_answer in correct_answers.items() if answers.get(question) == correct_answer)

        name = session.get('name')
        email = session.get('email')

        # Prepare data to send to Google Sheet
        data = {
            'name': name,
            'email': email,
            'score': score
        }

        google_script_url = 'https://script.google.com/macros/s/AKfycby8lX2cfJ_9mDtkL8hWQ2tHVpWG-xJRR4rkEqyVnZhf8DQPZweXFq-1YIF8HFC6x9gG/exec'
        response = requests.post(google_script_url, json=data)

        if response.status_code == 200:
            flash('Quiz submitted successfully!')
        else:
            flash('Error submitting quiz data.')

        return render_template('result.html', score=score)

    return render_template('quiz.html')

@app.route('/result')
def result():
    score = request.args.get('score', 0)
    return render_template('result.html', score=score)

# Video feed route
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()  # Read frame from camera
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    camera.release()  # Release camera resource when done


if __name__ == '__main__':
    app.run(debug=True)

