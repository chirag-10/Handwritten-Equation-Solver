import imghdr
import os
from flask import Flask, render_template, request, redirect, url_for, abort,send_from_directory,Response,g
from werkzeug.utils import secure_filename
import cv2, json, time
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from flask_session import Session
from PIL import Image
import pandas as pd
import numpy as np
import keras
import matplotlib.pyplot as plt 
from keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Dropout
from keras.models import Sequential, model_from_json
from keras.utils import to_categorical
from os.path import isfile, join
from keras import backend as K
from os import listdir
from IPython.display import Image
from io import BytesIO
import base64

app = Flask(__name__,static_folder="static")

app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = 'uploads'
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"

app.config['SESSION-TYPE'] = 'sqlalchemy'
db = SQLAlchemy(app)
app.config['SESSION_SQLALCHEMY'] = db

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

sess = Session(app)

index_by_directory = {
    '0': 0,
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    '+': 10,
    '-': 11,
    'times': 12
}

def get_index_by_directory(directory):
        return index_by_directory[directory]

def extract_imgs(img):
    img = ~img # Invert the bits of image 255 -> 0
    _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY) # Set bits > 127 to 1 and <= 127 to 0
    ctrs, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cnt = sorted(ctrs, key=lambda ctr: cv2.boundingRect(ctr)[0]) # Sort by x

    img_data = []
    rects = []
    for c in cnt :
        x, y, w, h = cv2.boundingRect(c)
        rect = [x, y, w, h]
        rects.append(rect)

    bool_rect = []
    # Check when two rectangles collide
    for r in rects:
        l = []
        for rec in rects:
            flag = 0
            if rec != r:
                if r[0] < (rec[0] + rec[2] + 10) and rec[0] < (r[0] + r[2] + 10) and r[1] < (rec[1] + rec[3] + 10) and rec[1] < (r[1] + r[3] + 10):
                    flag = 1
                l.append(flag)
            else:
                l.append(0)
        bool_rect.append(l)

    dump_rect = []
    # Discard the small collide rectangle
    for i in range(0, len(cnt)):
        for j in range(0, len(cnt)):
            if bool_rect[i][j] == 1:
                area1 = rects[i][2] * rects[i][3]
                area2 = rects[j][2] * rects[j][3]
                if(area1 == min(area1,area2)):
                    dump_rect.append(rects[i])

    # Get the final rectangles
    final_rect = [i for i in rects if i not in dump_rect]
    for r in final_rect:
        x = r[0]
        y = r[1]
        w = r[2]
        h = r[3]

        im_crop = thresh[y:y+h+10, x:x+w+10] # Crop the image as most as possible
        im_resize = cv2.resize(im_crop, (28, 28)) # Resize to (28, 28)
        im_resize = np.reshape(im_resize, (1, 28, 28)) # Flat the matrix
        img_data.append(im_resize)

    return img_data


class ConvolutionalNeuralNetwork:

    def __init__(self):
            self.load_model()

    def load_model(self):
        print('Loading Model...')
        model_json = open('./model.json', 'r')
        loaded_model_json = model_json.read()
        model_json.close()
        loaded_model = model_from_json(loaded_model_json)

        print('Loading weights...')
        loaded_model.load_weights("./model_weights.h5")

        self.model = loaded_model

    def predict(self, path):
        print(path)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

        if img is not None:
            img_data = extract_imgs(img)

            operation = ''
            for i in range(len(img_data)):
                img_data[i] = np.array(img_data[i])
                img_data[i] = img_data[i].reshape(-1, 28, 28, 1)

                result = self.model.predict_classes(img_data[i])

                if result[0] == 10:
                    operation += '+'
                elif result[0] == 11:
                    operation += '-'
                elif result[0] == 12:
                    operation += '*'
                
                else:
                    operation += str(result[0])

            return operation            

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

@app.route('/write')
def write():
    return render_template('write.html')

@app.route('/file')
def file():
    value = ["",0] 
    return render_template('file.html', value = value)

@app.route('/predict',methods=['POST'])
def upload1():
    print("App_root: "+ APP_ROOT)
    target = os.path.join(APP_ROOT, 'images/')
    print("target:" + target)
    if not os.path.isdir(target):
            os.mkdir(target)
    else:
        print("Couldn't create upload directory: {}".format(target))
        print(request.files.getlist("file"))
    for upload in request.files.getlist("file"):
        filename = upload.filename
        destination = "/".join([target, filename])
        upload.save(destination)
        location = 'images/' + filename
        print(location)
    
    path = "./" + location
    print("path : "+path)
    CNN = ConvolutionalNeuralNetwork()
    operation = CNN.predict(path)
    print(operation)
    result=eval(operation)
    print(result)
    return render_template("file.html", value =[operation, result])

@app.route('/predictWrite', methods=['POST'])
def predict():
    target = os.path.join(APP_ROOT, 'images/')
    operation = request.form['operation']
    imgdata = base64.b64decode(operation)
    filename = target + 'image.jpg'  # I assume you have a way of picking unique filenames
    with open(filename, 'wb') as f:
        f.write(imgdata)
    CNN = ConvolutionalNeuralNetwork()
    operation = CNN.predict(filename)
    print(operation)
    res = eval(operation)
    print(res)
    
    return json.dumps({
        'operation': operation,
        'solution': res
    })


if __name__ == "__main__":
    app.run(host="localhost",port="3000",debug=True)

