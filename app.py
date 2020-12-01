import imghdr
import os
from flask import Flask, render_template, request, redirect, url_for, abort,send_from_directory,Response,g
from werkzeug.utils import secure_filename
import cv2, json, time

from flask_sqlalchemy import SQLAlchemy

#import mysql.connector
from passlib.hash import sha256_crypt
from flask_session import Session



app = Flask(__name__,static_folder="static")



app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"

app.config['SESSION-TYPE'] = 'sqlalchemy'
db = SQLAlchemy(app)
app.config['SESSION_SQLALCHEMY'] = db



sess = Session(app)

db.create_all();
'''mydb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "toor2010",
    database = "flask"
)

cursor = mydb.cursor()'''

camera = cv2.VideoCapture(0)

def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield(b'--frame\r\n'
                  b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    camera.release()
    del (camera)
    cv2.destroyAllWindows()

def gen_pic():
    camera1 = cv2.VideoCapture(0)
    time.sleep(0.2)
    return_value, image = camera1.read()
    cv2.imwrite("uploads/opencv.png", image)

    del (camera1)


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def fav():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico')

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    else:
        username = request.form['username']
        password = request.form['password']
        print(sha256_crypt.verify("password",password))
        return redirect('/')

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        username = request.form['username']
        password = request.form['password']
        password = sha256_crypt.encrypt(password)
        #cursor.execute(f"INSERT INTO user VALUES ('{username}','{password}')")
        print(username, password)
        return render_template('index.html')

@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
                file_ext != validate_image(uploaded_file.stream):
            return "Invalid image", 400
        uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    return redirect('/file')

@app.route('/file')
def file():
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('file.html',files=files)

@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),mimetype='multipart/x-mixed-replace;boundary=frame')

@app.route('/pic')
def capture_pic():
    return Response(gen_pic(),mimetype='multipart/x-mixed-replace;boundary=frame')

@app.route('/write')
def write():
    return render_template('write.html')

@app.route('/predict',methods=['POST'])
def predict():
    return json.dumps(
        {
            'operation':'+',
            'solution':'Hello'
        }
    )


if __name__ == "__main__":
    app.run(host="localhost",port="3000",debug=True)

