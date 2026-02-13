import cv2
import re
from paddleocr import PaddleOCR


def preprocess(img_path):
    img = cv2.imread(img_path)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    cv2.imwrite("processed.jpg", thresh)

    return "processed.jpg"


ocr = PaddleOCR(use_angle_cls=True, lang='en')

img_path = "uploads/aadhaar/front/f1.jpg"

processed = preprocess(img_path)
result = ocr.ocr(processed)

text = ""

for line in result[0]:
    text += line[1][0] + " "

print("\n🔹 RAW TEXT:\n", text)

aadhaar = re.search(r'\d{4}\s\d{4}\s\d{4}', text)
dob = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', text)

print("\n🔹 Extracted:")
print("Aadhaar:", aadhaar.group() if aadhaar else "Not found")
print("DOB:", dob.group() if dob else "Not found")
