import re
from flask import Flask, render_template, request, flash, redirect, jsonify, make_response, send_file
import csv
import os
import tempfile
import json
import pytesseract
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import date, datetime
from deepface import DeepFace
import zxingcpp
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import base64
import io
from scipy.spatial.distance import cosine


app = Flask(__name__)
csv_path='students/students.csv'
app.secret_key = "watever"
app.config['MAX_CONTENT_LENGTH'] = 4*1024*1024

@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return jsonify({"success": False, "message":f"only files up to 4MB"}),413
    #return redirect('/Themsv')

def get_dob_from_ID(img_path):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    image_path = img_path  
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    date_pattern = r"\b\d{2}/\d{2}/\d{4}\b"
    dates = re.findall(date_pattern, text)
    dob = dates[0]
    dob_formatted = datetime.strptime(dob, "%d/%m/%Y").strftime("%Y-%m-%d")
    return dob_formatted

def compare_face(json1, json2, threshold= 0.4):
    with open(json1, "r") as f:
            embedding1 = json.load(f)
        
    with open(json2, "r") as f:
            embedding2 = json.load(f)

    try:
        similarity = 1 - cosine(embedding1[0]["embedding"], embedding2[0]["embedding"])
        
        if similarity > threshold:
            return True
        else:
            return False
    except Exception as e:
         raise RuntimeError("error") from e



def get_url(img_path):
    image = Image.open(img_path)
    results = zxingcpp.read_barcode(image)
    return results

def get_student_info_from_web(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 375, "height": 812},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()
        page.goto(url)
        page.wait_for_selector("text=MSSV:")
        html_content = page.content()
        browser.close()

        soup = BeautifulSoup(html_content, "html.parser")

        full_name = soup.find("div", {"class": "full-name center"}).get_text(strip=True) 
        mssv_tags = soup.find_all("div", class_="center")
        mssv_strong_tags = mssv_tags[1].find_all("strong")
        mssv = mssv_strong_tags[1].text.strip()
        img_tag = soup.find("img", class_="img-avatar")
        img_src = img_tag["src"]
        
        output_path = f"photos"
        if img_src.startswith("data:image"):
            base64_data = img_src.split(",")[1]  
            img_data = base64.b64decode(base64_data)

            output_file = os.path.join(output_path, f"{mssv}.jpg")
            with open(output_file, "wb") as f:
                f.write(img_data)
        student = ["", ""]
        student[0] = full_name
        student[1] = mssv
        return student


def extract_image_data(image_path):
    metadata = {}
    try:
        with Image.open(image_path) as img:
            metadata['Format'] = img.format
            metadata['Mode'] = img.mode
            metadata['Size'] = img.size
            modified_time = os.path.getmtime(image_path)
            metadata['Date uploaded'] = datetime.fromtimestamp(modified_time).isoformat()

            exif_data= img.getexif()
            if exif_data:

                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == "DateTimeOriginal":
                        metadata[tag_name] = value
                    elif tag_name == "DateTimeDigitized":
                        metadata[tag_name] = value
#            else:
#                modified_time = os.path.getmtime(image_path)
#                metadata['last modified'] = datetime.fromtimestamp(modified_time).isoformat()
#                if hasattr(os, 'path'):
#                        created_time = os.path.getctime(image_path)
#                        metadata['Created'] = datetime.fromtimestamp(created_time).isoformat()
#                    except Exception:
#                        metadata['Created'] = "Unavailable" 
#                    else: metadata['Created'] = "Unavailable" 
    except Exception as e:
        metadata['error'] = str(e)
    return metadata

def save_face_to_json(image_path, json_path):
    try:
        embedding = DeepFace.represent(img_path=image_path, model_name="VGG-Face")

        with open(json_path, "w") as f:
            json.dump(embedding, f)
    
    except Exception as e:
        raise RuntimeError("No face detected") from e

def save_to_csv(json_path, csv_path):
    if os.path.isfile(json_path):
        with open(json_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    else: return
    with open(csv_path, 'w',encoding='utf-8-sig', newline='') as csv_file:
        writer=csv.writer(csv_file)
        writer.writerow(['Mã Sinh Viên', 'Tên Sinh Viên', 'Ngày sinh'])
        for student in data:
            writer.writerow([student['ID'], student['Name'], student['DateOfBirth']])

def fragment_image(image_path, output_path, frag_numv = 4):
    os.makedirs(output_path, exist_ok=True)
    with Image.open(image_path) as img:
        width, height = img.size
        frag_width = width //2
        frag_height = height // 2
        count = 1
        for i in range(2):
            for j in range(2):
                upper = i*frag_height
                left = j*frag_width
                box= (left, upper, min(left+frag_width, width), min(upper+frag_height, height))
                fragment = img.crop(box)
                fragment.save(
                    os.path.join(output_path, f'fragment_{count}.bin'),
                    format='PNG'
                    )
                count+=1

@app.route('/')
def home():
     return render_template('index.html')

@app.route('/Themsv', methods=['GET'])
def show_form():
    return render_template('Themsv.html')

@app.route('/Themsv', methods=['POST'])
def ThemSV():
    name= request.form['Name']
    id = request.form['ID']
    birth = request.form['dob']
    Photo = request.files['photo']
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    if '.' not in Photo.filename or Photo.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
       return jsonify({"success": False, "message" : "Invalid file format, only png, jpg, jpeg allowed"}), 400
        #return redirect('/Themsv')
    now = datetime.now().date()
    dateOfBirth = datetime.strptime(birth, "%Y-%m-%d").date()
    if dateOfBirth>= now:
        return jsonify({"success": False, "message": "Invalid date of birth"}), 400
        #return redirect('/Themsv')
#save and fragment image
    os.makedirs('photos', exist_ok=True)
    temp_photo_path = f'photos/{id}.png'
    Photo.save(temp_photo_path)
    fragment_dir = f'photos/{id}'
    fragment_image(temp_photo_path, fragment_dir)

    save_face_to_json(temp_photo_path, f'photos/{id}/{id}face.json')
    
    metadata= extract_image_data(temp_photo_path)
    os.remove(temp_photo_path)
    img_info_path = f'photos/{id}/{id}info.json'

    json_path = 'students/students.json'
    students = []
    if os.path.isfile(json_path):
        with open(json_path, 'r', encoding='utf-8') as json_file:
            students = json.load(json_file)
    if any(student['ID'] == id for student in students):
        return jsonify({"success": False, "message":f"ma so {id} da ton tai"}),409
    students.append({
        "ID" : id,
        "Name" : name,
        "DateOfBirth" : birth,
        "CheckedIn" : False
    })
    with open(img_info_path, 'w', encoding='utf-8') as info:
        json.dump(metadata, info , ensure_ascii=False, indent=4)

    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent=4)
    save_to_csv(json_path, csv_path)
    return jsonify({"success": True, "message":f"them sinh vien {name} ma so {id} thanh cong"}),200

#add student by uploading csv file
@app.route('/ThemsvList', methods=['GET'])
def show_formList():
    return render_template('ThemsvList.html')
@app.route('/ThemsvList', methods=['Post'])
def ThemSVList():
    file=request.files['List']
    file.save('students/temp.csv')
    json_path = 'students/students.json'
    students = []
    if os.path.isfile(json_path):
        with open(json_path, 'r', encoding='utf-8') as json_file:
            students = json.load(json_file)
    id_existed= {student['ID'] for student in students}
    with open('students/temp.csv', 'r', newline='', encoding='utf-8-sig') as uploaded_f:
        reader = csv.DictReader(uploaded_f)
        for row in reader:
            if row['Mã số sinh viên'] not in id_existed:
                dobTemp = datetime.strptime(row['Ngày sinh'], "%m/%d/%Y").date()
                if dobTemp > datetime.now().date():
                    return jsonify({"success": False, "message":f"Ngay sinh cua sinh vien ma so {row['Mã số sinh viên']} khong hop le"}),400
                else:
                    students.append({
                        "ID": row['Mã số sinh viên'],
                        "Name": row['Tên Sinh Viên'],
                        "DateOfBirth": row['Ngày sinh'],
                        "CheckedIn": False
                    })
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent=4)
    save_to_csv(json_path, csv_path)
    os.remove('students/temp.csv')
    return jsonify({"success": True, "message":f"them sinh vien thanh cong"}),200




@app.route('/XoaSV', methods=['GET'])
def show_deleteform():
    return render_template('XoaSV.html')
@app.route('/XoaSV', methods=['Post'])
def XoaSV():
    json_path = f'students/students.json'
    id_to_delete = request.form['ID']

    if not os.path.isfile(json_path):
        return jsonify({"success": False, "message": "Không tìm thấy file sinh viên"}), 404
    
    with open(json_path, 'r', encoding='utf-8') as json_file:
        students = json.load(json_file)
    id_existed = {student['ID'] for student in students}
    if id_to_delete not in id_existed:
        return jsonify({"success": False, "message": f"sinh viên mã số {id_to_delete} không tồn tại trong danh sách"}), 404

    students = [student for student in students if student['ID'] != id_to_delete]
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent = 4)
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as csv_file:
        writer=csv.writer(csv_file)
        writer.writerow(['Mã Sinh Viên', 'Tên Sinh Viên', 'Ngày sinh'])
        for student in students:
            writer.writerow([student['ID'], student['Name'], student['DateOfBirth']])
    img_to_delete = f'photos/{id_to_delete}'
    if os.path.isdir(img_to_delete):
        for file in os.listdir(img_to_delete):
            os.remove(os.path.join(img_to_delete, file))
        os.rmdir(img_to_delete)
    return jsonify({"success": True, "message": f"sinh viên mã số {id_to_delete} đã xóa thành công"}), 200

@app.route('/api/students', methods=['GET'])
def get_students():
    json_path = f'students/students.json'
    if not os.path.isfile(json_path):
        return jsonify({"success": False, "message": "Không tìm thấy file sinh viên"}), 404
    with open(json_path,'r', encoding='utf-8') as json_file:
        students = json.load(json_file)
    return jsonify({"success":True, "students": students}), 200



@app.route('/AddPhoto', methods=['GET'])
def showphotoform():
     return render_template('bosunganh.html')
@app.route('/AddPhoto', methods=['Post'])
def add_photo():
    json_path = f'students/students.json'
    id_to_add_photo = request.form['ID']
    photo_path = f'photos/{id_to_add_photo}.png'
    photo_to_add = request.files['photo']

    allowed_extensions = {'png', 'jpg', 'jpeg'}
    if '.' not in photo_to_add.filename or photo_to_add.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
       return jsonify({"success": False, "message" : "Invalid file format, only png, jpg, jpeg allowed"}), 400
    frag_dir_to_add = f'photos/{id_to_add_photo}'

    if not os.path.isfile(json_path):
        return jsonify({"success": False, "message": "Không tìm thấy file sinh viên"}), 404
    
    with open(json_path, 'r', encoding='utf-8') as json_file:
        students = json.load(json_file)
    id_existed = {student['ID'] for student in students}
    if id_to_add_photo not in id_existed:
        return jsonify({"success": False, "message": f"sinh viên mã số {id_to_add_photo} không tồn tại trong danh sách"}), 404
    
    os.makedirs('photos', exist_ok=True)
    temp_photo_path_to_add = f'photos/{id_to_add_photo}.png'
    os.makedirs('photos', exist_ok=True)
    photo_to_add.save(temp_photo_path_to_add)

    fragment_image(temp_photo_path_to_add, frag_dir_to_add)

    save_face_to_json(temp_photo_path_to_add, f'photos/{id_to_add_photo}/{id_to_add_photo}face.json')

    metadata= extract_image_data(temp_photo_path_to_add)
    os.remove(temp_photo_path_to_add)
    img_info_path = f'photos/{id_to_add_photo}/{id_to_add_photo}info.json'

    with open(img_info_path, 'w', encoding='utf-8') as info:
        json.dump(metadata, info , ensure_ascii=False, indent=4)
    return jsonify({"success": True, "message": "Đã thêm ảnh thành công"}), 404

@app.route('/ThemsvID', methods=['GET'])
def showIDform():
    return render_template('ThemsvID.html')
@app.route('/ThemsvID', methods=['Post'])
def themsvID():
    Photo = request.files['photo']
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    if '.' not in Photo.filename or Photo.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
       return jsonify({"success": False, "message" : "Invalid file format, only png, jpg, jpeg allowed"}), 400
    os.makedirs('photos', exist_ok=True)
    temp_photo_path = f'photos/temp.png'
    Photo.save(temp_photo_path)
    url = get_url(temp_photo_path)
    if not url:
        return jsonify({"success": False, "message" : "no qr code detected"}), 400
    if not url.text.startswith("https://ctsv.hust"):
        return jsonify({"success": False, "message" : "Not school link"}), 400
    link = url.text
    student_info = get_student_info_from_web(link)
    id = student_info[1]
    name = student_info[0]
    dob = get_dob_from_ID(temp_photo_path)
    photo_path= f"photos/{id}.jpg"
    os.remove(temp_photo_path)
    

    fragment_dir = f'photos/{id}'
    fragment_image(photo_path, fragment_dir)

    save_face_to_json(photo_path, f'photos/{id}/{id}face.json')
    
    metadata= extract_image_data(photo_path)
    os.remove(photo_path)
    img_info_path = f'photos/{id}/{id}info.json'

    json_path = 'students/students.json'
    students = []
    if os.path.isfile(json_path):
        with open(json_path, 'r', encoding='utf-8') as json_file:
            students = json.load(json_file)
    if any(student['ID'] == id for student in students):
        return jsonify({"success": False, "message":f"ma so {id} da ton tai"}),409
    students.append({
        "ID" : id,
        "Name" : name,
        "DateOfBirth" : dob,
        "CheckedIn" : False
    })
    with open(img_info_path, 'w', encoding='utf-8') as info:
        json.dump(metadata, info , ensure_ascii=False, indent=4)

    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent=4)
    save_to_csv(json_path, csv_path)
    return jsonify({"success": True, "message":f"them sinh vien {name} ma so {id} thanh cong"}),200


@app.route('/checkin', methods=['GET'])
def showCheckInPage():
    return render_template('Diemdanh.html')


@app.route('/CheckInWithNameFace', methods=['GET'])
def showCheckInWithNamePage():
    return render_template('Diemdanhbangten.html')
@app.route('/CheckInWithNameFace', methods=['Post'])
def CheckInWithFaceAndName():
    name= request.form['Name']
    id = request.form['ID']
    Photo = request.files['photo']
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    if '.' not in Photo.filename or Photo.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
       return jsonify({"success": False, "message" : "Invalid file format, only png, jpg, jpeg allowed"}), 400
        #return redirect('/Themsv')
#save and fragment image
    json_path = 'students/students.json'
    with open(json_path, 'r', encoding='utf-8') as json_file:
        students = json.load(json_file)
    id_existed = {student['ID'] for student in students}
    if id not in id_existed:
        return jsonify({"success": False, "message": f"sinh viên mã số {id} không tồn tại trong danh sách"}), 404
    for student in students:
        if student['ID'] == id and student['Name'] != name:
            return jsonify({"success": False, "message": f"Thông tin sinh viên mã số {id} không đúng"}), 404
        if student['ID'] == id and student['CheckedIn'] == True:
            return jsonify({"success": True, "message": f"Thông tin sinh viên mã số {id} đã được check in từ trước"}), 200

    os.makedirs('photos', exist_ok=True)
    temp_photo_path = f'photos/temp{id}.png'
    Photo.save(temp_photo_path)

    save_face_to_json(temp_photo_path, f'photos/{id}/temp{id}face.json')
    os.remove(temp_photo_path)
    face_json_temp = f'photos/{id}/temp{id}face.json'
    face_json = f'photos/{id}/{id}face.json'
    if not os.path.isfile(face_json):
        os.remove(face_json_temp)
        return jsonify({"success": False, "message": f"Sinh viên mã số {id} chưa có ảnh trong hệ thống"}), 404
    if not compare_face(face_json, face_json_temp):
        os.remove(face_json_temp)
        return jsonify({"success": False, "message": f"Không trùng khuôn mặt"}), 404
    os.remove(face_json_temp)
    for student in students:
        if student['ID'] == id:
            student['CheckedIn'] = True
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent=4)
    return jsonify({"success": True, "message": f"Điểm danh thành công"}), 200

@app.route('/CheckInwithID', methods=['GET'])
def showCheckInWithIDPage():
    return render_template('Diemdanhbangthe.html')
@app.route('/CheckInwithID', methods=['Post'])
def checkInWithID():
    Photo = request.files['photo']
    allowed_extensions = {'png', 'jpg', 'jpeg'}
    if '.' not in Photo.filename or Photo.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
       return jsonify({"success": False, "message" : "Invalid file format, only png, jpg, jpeg allowed"}), 400
    json_path = 'students/students.json'
    with open(json_path, 'r', encoding='utf-8') as json_file:
        students = json.load(json_file)
    id_existed = {student['ID'] for student in students}
    temp_photo_path = f'photos/tempID.png'
    Photo.save(temp_photo_path)
    url = get_url(temp_photo_path)
    if not url:
        return jsonify({"success": False, "message" : "no qr code detected"}), 400
    if not url.text.startswith("https://ctsv.hust"):
        return jsonify({"success": False, "message" : "Not school link"}), 400
    link = url.text
    student_info = get_student_info_from_web(link)
    id = student_info[1]
    name = student_info[0]
    if id not in id_existed:
        return jsonify({"success": False, "message": f"sinh viên mã số {id} không tồn tại trong danh sách"}), 404
    for student in students:
        if student['ID'] == id and student['Name'] != name:
            return jsonify({"success": False, "message": f"Thông tin sinh viên mã số {id} không đúng"}), 404
        if student['ID'] == id and student['CheckedIn'] == True:
            return jsonify({"success": True, "message": f"Thông tin sinh viên mã số {id} đã được check in từ trước"}), 200
    os.remove(temp_photo_path)
    for student in students:
        if student['ID'] == id:
            student['CheckedIn'] = True
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent=4)
    os.remove(f"photos/{id}.jpg")
    return jsonify({"success": True, "message": f"Điểm danh thành công"}), 200


@app.route('/reset_checkin', methods=['POST'])
def reset_checkin():
    json_path = 'students/students.json'
    if not os.path.isfile(json_path):
        return jsonify({"success": False, "message": "Không tìm thấy file sinh viên"}), 404

    with open(json_path, 'r', encoding='utf-8') as json_file:
        students = json.load(json_file)

    for student in students:
        student["CheckedIn"] = False

    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent=4)

    save_to_csv(json_path, csv_path)

    return jsonify({"success": True, "message": "Đã reset trạng thái Điểm danh cho tất cả sinh viên"}), 200


@app.route('/download_failed_checkins', methods=['GET'])
def download_failed_checkins():
    json_path = 'students/students.json'
    with open(json_path, 'r', encoding='utf-8') as json_file:
        students = json.load(json_file)

    failed_students = [s for s in students if not s["CheckedIn"]]

    if not failed_students:
        return jsonify({"success": False, "message": "No students failed to check in."}), 400

    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8-sig', delete=False, newline='') as temp_file:
        writer = csv.writer(temp_file)
        writer.writerow(["MSSV", "Tên Sinh Viên", "Ngày sinh"])
        for student in failed_students:
            writer.writerow([student["ID"], student["Name"], student["DateOfBirth"]])

        temp_file_path = temp_file.name 

    response = send_file(temp_file_path, 
                         as_attachment=True, 
                         download_name='failed_checkins.csv', 
                         mimetype='text/csv')

    return response


if __name__ == '__main__':
    app.run(debug=True)
    