document.getElementById("xoaSV").addEventListener("submit", async function(event) {
    event.preventDefault(); 
    
    const form = document.getElementById("xoaSV");
    const formData = new FormData(form);
    
    try {
        const response = await fetch("/XoaSV", {
            method: "POST",
            body: formData
        });

        const result = await response.json(); 
        
        const responseMessage = document.getElementById("responseMessage");
        if (result.success) {
            responseMessage.textContent = result.message;
            responseMessage.style.color = "green";
        } else {
            responseMessage.textContent = result.message;
            responseMessage.style.color = "red";
        }
    } catch (error) {
        console.error("Error:", error);
        const responseMessage = document.getElementById("responseMessage");
        responseMessage.textContent = "An unexpected error occurred.";
        responseMessage.style.color = "red";
    }
});