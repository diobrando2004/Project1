document.getElementById('downloadFailedCheckinsButton').addEventListener('click', function () {
    fetch('/download_failed_checkins')
        .then(response => {
            if (response.ok) {
                return response.blob();
            } else {
                throw new Error('Failed');
            }
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'failed_checkins.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => console.error('Error:', error));
});
