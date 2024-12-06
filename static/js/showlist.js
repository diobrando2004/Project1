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
            <th>Ngày sinh</th>`;
        table.appendChild(header);
        data.students.forEach(student => {
            const row = document.createElement('tr');
            row.innerHTML = `
            <td>${student.ID}</td>
            <td>${student.Name}</td>
            <td>${student.DateOfBirth}</td`;
            table.appendChild(row);
        });
        studentList.appendChild(table);
    }else {
        studentList.innerHTML=`<p>${data.message}</p>`;
    }
    }
    catch(error) {
        console.error('Error fetching student data:', error);
        document.getElementById('student-list').innerHTML = `<p>Failed to load student data</p>`;
    }
}   
document.addEventListener('DOMContentLoaded', fetchStudents);