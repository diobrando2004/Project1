    document.getElementById("themSV").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevent the default form submission
    
    const form = document.getElementById("themSV");
    const formData = new FormData(form); // Get form data including the file
    
    try {
        const response = await fetch("/Themsv", {
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