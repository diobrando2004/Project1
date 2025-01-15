const videoId = document.getElementById('video-id');
const canvasId = document.getElementById('canvas-id');
const contextId = canvasId.getContext('2d');
const responseId = document.getElementById('response-id');

const videoFace = document.getElementById('video-face');
const canvasFace = document.getElementById('canvas-face');
const contextFace = canvasFace.getContext('2d');
const responseFace = document.getElementById('response-face');

const startButton = document.getElementById('start-button');
const startSection = document.getElementById('start-section');


let processing = false;
let extractedId = "";

navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        videoId.srcObject = stream;
        videoFace.srcObject = stream;
    })
    .catch(err => {
        responseId.classList.remove('success-message');
        responseId.classList.add('fail-message');
        responseId.textContent = "Lỗi truy cập webcam.";
    });

startButton.addEventListener('click', () => {
    step = 1; 
    startSection.style.display = 'none'; 
    document.getElementById('step1').style.display = 'block';
});

//scan ID
setInterval(() => {
    if (step !== 1 || processing) return;

    processing = true;
    contextId.drawImage(videoId, 0, 0, canvasId.width, canvasId.height);
    const imageData = canvasId.toDataURL('image/png');

    fetch('/scan-id', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: imageData })
    })
        .then(response => response.json())
        .then(data => {
            responseId.textContent = data.message;
            responseId.classList.add('success-message');
            responseId.classList.remove('fail-message');
            if (data.success) {
                if(data.message.startsWith('Sinh')){
                    responseId.textContent = data.message;
                    setTimeout(() => {
                        resetToInitialState();
                    }, 2000);
                }
                else{
                extractedId = data.message.split(":")[1].trim();
                
                step = 2;
                document.getElementById('step1').style.display = 'none';
                document.getElementById('step2').style.display = 'block';
                }
            }
            responseId.classList.remove('success-message');
            responseId.classList.add('fail-message');
            processing = false;
        })
        .catch(err => {
            console.error("Error:", err);
            responseId.textContent = "Lỗi scan ID.";
            processing = false;
        });
}, 2000);

//scan face
setInterval(() => {
    if (step !== 2 || processing) return;

    processing = true;
    contextFace.drawImage(videoFace, 0, 0, canvasFace.width, canvasFace.height);
    const faceData = canvasFace.toDataURL('image/png');

    fetch('/scan-face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ face: faceData, id: extractedId })
    })
        .then(response => response.json())
        .then(data => {
            responseFace.textContent = data.message;

            if (data.success) {
                responseFace.textContent = data.message;
                responseFace.classList.remove('fail-message');
                responseFace.classList.add('success-message');
                fetchStudents();
                setTimeout(() => {
                    resetToInitialState();
                }, 2000);
            } else {
                responseFace.textContent = data.message;
                responseFace.classList.remove('success-message');
                responseFace.classList.add('fail-message');
                if(data.message.startsWith('Sinh viên mã số')){
                    setTimeout(() => {
                        resetToInitialState();
                    }, 2000);
                }
            }
            processing = false;
        })
        .catch(err => {
            console.error("Error:", err);
            responseFace.textContent = "Lỗi scan mặt";
            processing = false;
        });
}, 2000);


function resetToInitialState() {
    step = 0; 
    extractedId = "";
    if(document.getElementById('step1').style.display == 'block') document.getElementById('step1').style.display = 'none';
    else document.getElementById('step2').style.display = 'none'; 
    startSection.style.display = 'block'; 
    responseId.textContent = "Waiting for ID card...";
    responseFace.textContent = "Waiting for face capture...";
}
