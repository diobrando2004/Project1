async function fetchStudents() {
    try{
    const response = await fetch('/api/students');
    const data = await response.json();
    const studentList = document.getElementById('student-list');
    studentList.innerHTML='';

    if(data.success){
        table = document.createElement('table');
        table.border = "1";
        table.className = "student-list"
        const header = document.createElement('tr');
        header.innerHTML = `
            <th>Mã Sinh Viên</th>
            <th>Tên Sinh Viên</th>
            <th>Ngày sinh</th>
            <th style="display: none;">Actions</th>`;
        table.appendChild(header);
        data.students.forEach(student => {
            const row = document.createElement('tr');
            if (student.CheckedIn === true) {
                row.style.backgroundColor = 'lightgreen';
            }
            else  {
                row.style.backgroundColor = 'white';
            }
            
            row.innerHTML = `
            <td>${student.ID}</td>
            <td>${student.Name}</td>
            <td>${student.DateOfBirth}</td>
            <td style="background-color: transparent !important;" ><button onclick="deleteStudent('${student.ID}')" 
            style="background-color:  red;
                    color: white;
                    border: 0cap;"
                    >Delete</button></td>`;
            table.appendChild(row);
        });
        studentList.appendChild(table);
    }else {
        studentList.innerHTML=`<p>${data.message}</p>`;
    }
    }
    catch(error) {
        console.error('Error fetching student data:', error);
        document.getElementById('student-list').innerHTML = `<p>Failed</p>`;
    }
}   
async function deleteStudent(studentId) {
    if (confirm(`Xóa sinh viên mã số ${studentId}?`)) {
        try {
            const response = await fetch('/api/delete-student', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ studentId: studentId }),
            });

            const data = await response.json();
            const deleteMessage = document.getElementById('deleteMessage');

            if (data.success) {
                deleteMessage.textContent = data.message;
                fetchStudents();
            } else {
                deleteMessage.textContent = `Error: ${data.message}`; 
            }
        } catch (error) {
            console.error('Lỗi khi xóa', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', fetchStudents);