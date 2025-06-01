from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import mysql.connector
import cv2
import numpy as np
import os
from datetime import datetime
from PIL import Image
import io
import base64
from dotenv import load_dotenv
from functools import wraps
import hashlib

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # More secure secret key

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '1234',  # Change this to your MySQL password
    'database': 'attendance_system'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Create necessary database tables if they don't exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop existing tables in correct order (to avoid foreign key constraints)
    cursor.execute('DROP TABLE IF EXISTS attendance')
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS admins')
    cursor.execute('DROP TABLE IF EXISTS departments')
    
    # Create departments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table with department reference
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            department_id INT NOT NULL,
            branch VARCHAR(50) NOT NULL,
            roll_number VARCHAR(20) UNIQUE NOT NULL,
            photo LONGBLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')
    
    # Create attendance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            roll_number VARCHAR(20),
            date DATE,
            time TIME,
            status VARCHAR(20),
            FOREIGN KEY (roll_number) REFERENCES users(roll_number)
        )
    ''')
    
    # Create admin table with department reference
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            department_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')
    
    # Insert default departments
    default_departments = [
        'Computer Science',
        'Information Technology',
        'Electronics',
        'Mechanical',
        'Civil',
        'Electrical',
        'Chemical'
    ]
    
    for dept in default_departments:
        try:
            cursor.execute('INSERT INTO departments (name) VALUES (%s)', (dept,))
        except mysql.connector.IntegrityError:
            # Department already exists
            pass
    
    # Insert default admin
    try:
        # Get the Computer Science department ID
        cursor.execute('SELECT id FROM departments WHERE name = %s', ('Computer Science',))
        dept_id = cursor.fetchone()[0]
        
        # Insert default admin with department
        default_username = 'admin'
        default_password = 'admin123'
        password_hash = hashlib.sha256(default_password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO admins (username, password_hash, department_id)
            VALUES (%s, %s, %s)
        ''', (default_username, password_hash, dept_id))
    except mysql.connector.IntegrityError:
        # Admin already exists
        pass
    
    conn.commit()
    cursor.close()
    conn.close()

# Call init_db() when the application starts
init_db()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Load the pre-trained face detection cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@app.route('/')
def home():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get total number of registered users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # Get today's attendance count
    cursor.execute('SELECT COUNT(*) FROM attendance WHERE DATE(date) = CURDATE()')
    today_attendance = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return render_template('index.html', total_users=total_users, today_attendance=today_attendance)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT a.*, d.name as department_name 
            FROM admins a 
            LEFT JOIN departments d ON a.department_id = d.id 
            WHERE username = %s AND password_hash = %s
        ''', (username, password_hash))
        admin = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if admin:
            session['admin_logged_in'] = True
            session['admin_username'] = admin['username']
            session['admin_department'] = admin['department_name']
            flash('Login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        department_id = request.form['department']
        branch = request.form['branch']
        roll_number = request.form['roll_number']
        photo = request.files['photo']
        
        if photo:
            # Read and process the uploaded image
            image_data = photo.read()
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Detect faces in the image
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            
            if len(faces) == 0:
                flash('No face detected in the uploaded image. Please try again.', 'error')
                return redirect(url_for('register'))
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                # Insert user data into database
                cursor.execute('''
                    INSERT INTO users (name, department_id, branch, roll_number, photo)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (name, department_id, branch, roll_number, image_data))
                
                conn.commit()
                flash('Registration successful!', 'success')
                
            except mysql.connector.IntegrityError:
                flash('Roll number already exists!', 'error')
            finally:
                cursor.close()
                conn.close()
                
            return redirect(url_for('register'))
    
    # Get departments for the registration form
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, name FROM departments ORDER BY name')
    departments = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('register.html', departments=departments)

@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all users with department information
    cursor.execute('''
        SELECT u.id, u.name, d.name as department_name, u.branch, u.roll_number, u.created_at 
        FROM users u 
        JOIN departments d ON u.department_id = d.id
        ORDER BY u.created_at DESC
    ''')
    users = cursor.fetchall()
    
    # Fetch today's attendance
    cursor.execute('''
        SELECT u.name, a.roll_number, TIME_FORMAT(a.time, '%H:%i:%s') as time, a.status 
        FROM attendance a 
        JOIN users u ON a.roll_number = u.roll_number 
        WHERE DATE(a.date) = CURDATE()
    ''')
    attendance = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin.html', users=users, attendance=attendance)

@app.route('/capture_attendance', methods=['POST'])
def capture_attendance():
    # Get the image data from the request
    image_data = request.json['image'].split(',')[1]
    img_bytes = base64.b64decode(image_data)
    
    # Convert to numpy array
    img = Image.open(io.BytesIO(img_bytes))
    img_array = np.array(img)
    
    # Convert to grayscale for face detection
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Detect faces in the captured image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    
    if len(faces) == 0:
        return jsonify({'status': 'error', 'message': 'No face detected'})
    elif len(faces) > 1:
        return jsonify({'status': 'error', 'message': 'Multiple faces detected. Please ensure only one person is in frame.'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get the first user from the database (for demo purposes)
        cursor.execute('SELECT roll_number, name FROM users LIMIT 1')
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'No users registered in the system'
            })
        
        roll_number, user_name = user
        
        # Check if attendance already marked for today
        cursor.execute('''
            SELECT COUNT(*) FROM attendance 
            WHERE roll_number = %s 
            AND DATE(date) = CURDATE()
        ''', (roll_number,))
        
        count = cursor.fetchone()[0]
        
        if count > 0:
            return jsonify({
                'status': 'error',
                'message': f'Attendance already marked for {user_name} today'
            })
        
        # Mark attendance
        now = datetime.now()
        cursor.execute('''
            INSERT INTO attendance (roll_number, date, time, status)
            VALUES (%s, %s, %s, %s)
        ''', (roll_number, now.date(), now.time(), 'Present'))
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Attendance marked for {user_name} ({roll_number})'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error marking attendance: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/mark_attendance')
def mark_attendance_page():
    return render_template('attendance.html')

@app.route('/delete_attendance/<roll_number>', methods=['DELETE'])
@login_required
def delete_attendance(roll_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM attendance 
            WHERE roll_number = %s AND DATE(date) = CURDATE()
        ''', (roll_number,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Attendance record deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/delete_all_attendance', methods=['DELETE'])
@login_required
def delete_all_attendance():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM attendance WHERE DATE(date) = CURDATE()')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'All attendance records deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/admin_attendance')
@login_required
def admin_attendance():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all users for the dropdown
    cursor.execute('SELECT name, roll_number FROM users')
    users = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin_attendance.html', users=users)

@app.route('/admin_capture_attendance', methods=['POST'])
@login_required
def admin_capture_attendance():
    data = request.json
    image_data = data['image'].split(',')[1]
    roll_number = data['roll_number']
    img_bytes = base64.b64decode(image_data)
    
    # Convert to numpy array
    img = Image.open(io.BytesIO(img_bytes))
    img_array = np.array(img)
    
    # Convert to grayscale for face detection
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Detect faces in the captured image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    
    if len(faces) == 0:
        return jsonify({'status': 'error', 'message': 'No face detected'})
    elif len(faces) > 1:
        return jsonify({'status': 'error', 'message': 'Multiple faces detected. Please ensure only one person is in frame.'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get user details
        cursor.execute('SELECT name FROM users WHERE roll_number = %s', (roll_number,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            })
        
        user_name = user[0]
        
        # Check if attendance already marked for today
        cursor.execute('''
            SELECT COUNT(*) FROM attendance 
            WHERE roll_number = %s 
            AND DATE(date) = CURDATE()
        ''', (roll_number,))
        
        count = cursor.fetchone()[0]
        
        if count > 0:
            return jsonify({
                'status': 'error',
                'message': f'Attendance already marked for {user_name} today'
            })
        
        # Mark attendance
        now = datetime.now()
        cursor.execute('''
            INSERT INTO attendance (roll_number, date, time, status)
            VALUES (%s, %s, %s, %s)
        ''', (roll_number, now.date(), now.time(), 'Present'))
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Attendance marked for {user_name} ({roll_number})'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Error marking attendance: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        department_id = request.form['department']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('admin_register'))

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Check if username already exists
            cursor.execute('SELECT id FROM admins WHERE username = %s', (username,))
            if cursor.fetchone():
                flash('Username already exists!', 'error')
                return redirect(url_for('admin_register'))

            # Hash password and insert new admin
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('''
                INSERT INTO admins (username, password_hash, department_id)
                VALUES (%s, %s, %s)
            ''', (username, password_hash, department_id))

            conn.commit()
            flash('Admin registration successful!', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            conn.rollback()
            flash(f'Error registering admin: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    # Get departments for the registration form
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, name FROM departments ORDER BY name')
    departments = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('admin_register.html', departments=departments)

if __name__ == '__main__':
    app.run(debug=True) 