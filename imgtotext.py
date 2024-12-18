from PIL import Image
import pytesseract
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
image_path = "myfuckingID.jpg"  
image = Image.open(image_path)
text = pytesseract.image_to_string(image)
date_pattern = r"\b\d{2}/\d{2}/\d{4}\b"
dates = re.findall(date_pattern, text)
dob = dates[0]
print(dob)
