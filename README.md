# Face Recognition Attendance Management System

A modern web-based attendance management system using facial recognition technology. Built with Flask, OpenCV, and MySQL.

## Features

- Face Recognition based attendance marking
- Department-wise user organization
- Admin panel with department-specific access
- Real-time attendance tracking
- Modern and responsive UI
- Secure authentication system

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript, Bootstrap 5
- **Face Detection:** OpenCV (Haar Cascade)
- **Additional Libraries:** 
  - Pillow (PIL)
  - mysql-connector-python
  - python-dotenv

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/face-recognition-attendance.git
cd face-recognition-attendance
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # For Linux/Mac
venv\Scripts\activate     # For Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up MySQL database:
- Create a MySQL database
- Update database configuration in `app.py`

5. Run the application:
```bash
python app.py
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:
```
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=attendance_system
```


## Project Structure

```
face-recognition-attendance/
├── app.py                 # Main application file
├── requirements.txt       # Project dependencies
├── static/               # Static files
│   ├── css/             # CSS files
│   └── js/              # JavaScript files
└── templates/           # HTML templates
    ├── admin.html       # Admin dashboard
    ├── attendance.html  # Attendance marking page
    ├── base.html       # Base template
    ├── index.html      # Homepage
    ├── login.html      # Admin login
    └── register.html   # User registration
```

## Features in Detail

### 1. User Registration
- Photo capture for face recognition
- Department and branch selection
- Automatic face detection validation

### 2. Attendance Marking
- Real-time face detection
- Quick attendance verification
- Success/failure notifications

### 3. Admin Panel
- Department-wise admin access
- Attendance records management
- User management
- Bulk attendance operations

### 4. Security Features
- Password hashing
- Session management
- Protected admin routes
- Department-based access control

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Created By

Ashok

## Acknowledgments

- OpenCV for face detection
- Flask for the web framework
- Bootstrap for the UI components 
