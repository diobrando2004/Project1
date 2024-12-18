from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import base64

def extract_student_info(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 375, "height": 812},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()

        page.goto(url)
        page.wait_for_selector("text=MSSV:")

        html_content = page.content()

        browser.close()

        soup = BeautifulSoup(html_content, "html.parser")

        full_name = soup.find("div", {"class": "full-name center"}).get_text(strip=True) 
        mssv_tags = soup.find_all("div", class_="center")
        mssv_strong_tags = mssv_tags[1].find_all("strong")
        mssv = mssv_strong_tags[1].text.strip()
        img_tag = soup.find("img", class_="img-avatar")
        img_src = img_tag["src"]
        
        if img_src.startswith("data:image"):
            base64_data = img_src.split(",")[1]  
            img_data = base64.b64decode(base64_data)

            output_file = "avatar.jpg"
            with open(output_file, "wb") as f:
                f.write(img_data)
            print(f"Image saved as {output_file}")
        print("Full Name:", full_name)
        print("MSSV:", mssv)

url = "https://ctsv.hust.edu.vn/#/card/20225175/PHAM_HAI_DANG/8BjUekZAH09TkvRBfwQUjDi82e4%3D"
extract_student_info(url)