document.getElementById('resetCheckinButton').addEventListener('click', function () {
    fetch('/reset_checkin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        const resetCheckinMessage = document.getElementById('resetCheckinMessage');
        if (data.success) {
            resetCheckinMessage.style.color = 'green';
            resetCheckinMessage.textContent = data.message;
            fetchStudents();
        } else {
            resetCheckinMessage.style.color = 'red';
            resetCheckinMessage.textContent = "Error: " + data.message;
        }
    })
    .catch(error => {
        const resetCheckinMessage = document.getElementById('resetCheckinMessage');
        resetCheckinMessage.style.color = 'red';
        resetCheckinMessage.textContent = "Error";
        console.error('Error:', error);
    });
});
