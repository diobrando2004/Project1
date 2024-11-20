from flask import Flask, render_template, request, flash, redirect
import csv
import os
app = Flask(__name__)
csv_path='students/students.csv'
app.secret_key = "watever"
@app.route('/')
def home():
     return render_template('index.html')

@app.route('/Themsv', methods=['GET'])
def show_form():
    return render_template('Themsv.html')

@app.route('/Themsv', methods=['POST', 'GET'])
def ThemSV():
    name= request.form['Name']
    id = request.form['ID']
    Photo = request.files['photo']

    Photo.save(f'photos/{id}.png')
    
    ids_exsited = set()
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        if os.path.isfile(csv_path):
           with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            read =  csv.reader(f)
            next(read)
            for row in read:
                ids_exsited.add(row[1])
            if id in ids_exsited:
                flash(f" ma so {id} da ton tai", "error")
                return redirect('/Themsv')      
            csv.writer(f).writerow([name,id])
        else:
            csv.writer(f).writerow(['Tên Sinh Viên','Mã Sinh Viên'])
            csv.writer(f).writerow([name,id])
    flash(f"them sinh vien {name} ma so {id} thanh cong", "success")
    return redirect('/Themsv')



#add student by uploading csv file
@app.route('/ThemsvList', methods=['GET'])
def show_formList():
    return render_template('ThemsvList.html')
@app.route('/ThemsvList', methods=['Post','GET'])
def ThemSVList():
    file=request.files['List']
    file.save('students/temp.csv')
    ids_existed = set()
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        read =  csv.reader(f)
        next(read)
        for row in read:
            ids_existed.add(row[1])
    with open('students/temp.csv', 'r', newline='', encoding='utf-8') as uploaded_f:
         read = csv.reader(uploaded_f)
         if not os.path.isfile(csv_path):
            csv.writer(f).writerow(['Tên Sinh Viên','Mã Sinh Viên'])

         with open(csv_path, 'a', newline='', encoding='utf-8') as f:
             write =csv.writer(f)
             for row in read:
                if row[1] not in ids_existed:
                    write.writerow(row)
    flash(f"added info to the list", "success")
    os.remove('students/temp.csv')
    return redirect('/ThemsvList')
if __name__ == '__main__':
    app.run(debug=True)