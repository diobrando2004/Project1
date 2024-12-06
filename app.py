from flask import Flask, render_template, request, flash, redirect, jsonify
import csv
import os
import json
from werkzeug.exceptions import RequestEntityTooLarge
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import date, datetime

app = Flask(__name__)
csv_path='students/students.csv'
app.secret_key = "watever"
app.config['MAX_CONTENT_LENGTH'] = 4*1024*1024

@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return jsonify({"success": False, "message":f"only files up to 4MB"}),413
    #return redirect('/Themsv')

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
                fragment.save(os.path.join(output_path, f'fragment_{count}.png'))
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
    os.makedirs('photos', exist_ok=True)
    Photo.save(temp_photo_path)
    fragment_dir = f'photos/{id}'
    fragment_image(temp_photo_path, fragment_dir)

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
        "DateOfBirth" : birth
    })
    with open(img_info_path, 'w', encoding='utf-8') as info:
        json.dump(metadata, info , ensure_ascii=False, indent=4)

    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent=4)
    save_to_csv(json_path, csv_path)
    return jsonify({"success": True, "message":f"them sinh vien {name} ma so {id} thanh cong"}),200

#    ids_exsited = set()
#    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
#        if os.path.isfile(csv_path):
#           with open(csv_path, 'r', newline='', encoding='utf-8') as fr:
#            read =  csv.reader(fr)
#            next(read)
#            for row in read:
#                ids_exsited.add(row[0])
#            if id in ids_exsited:
#                return jsonify({"success": False, "message":" ma so {id} da ton tai"}),409
#                #return redirect('/Themsv')      
#            csv.writer(f).writerow([id, name, birth])
#        else:
#            csv.writer(f).writerow(['Mã Sinh Viên','Tên Sinh Viên', 'Ngày sinh'])
#           csv.writer(f).writerow([id, name, birth])
#    return jsonify({"success": True, "message":f"them sinh vien {name} ma so {id} thanh cong"}),200
#    #return redirect('/Themsv')


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
                        "DateOfBirth": row['Ngày sinh']
                    })
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(students, json_file, ensure_ascii=False, indent=4)
    save_to_csv(json_path, csv_path)
    os.remove('students/temp.csv')
    return jsonify({"success": True, "message":f"them sinh vien thanh cong"}),200
#    ids_existed = set()
#    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
#        read =  csv.reader(f)
#        next(read)
#        for row in read:
#            ids_existed.add(row[0])
#    with open('students/temp.csv', 'r', newline='', encoding='utf-8') as uploaded_f:
#         read = csv.reader(uploaded_f)
#         if not os.path.isfile(csv_path):
#           csv.writer(f).writerow(['Mã Sinh Viên','Tên Sinh Viên', 'Ngày sinh'])
#
#         with open(csv_path, 'a', newline='', encoding='utf-8') as f:
#             write =csv.writer(f)
#             for row in read:
#                if row[0] not in ids_existed:
#                    write.writerow(row)
    #flash(f"added info to the list", "success")
#    os.remove('students/temp.csv')
#    return jsonify({"success": True, "message":f"them sinh vien thanh cong"}),200
    #return redirect('/ThemsvList')



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

if __name__ == '__main__':
    app.run(debug=True)