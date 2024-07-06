from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadImageForm
from PIL import Image, ImageDraw, ImageEnhance
import pytesseract
import io
import base64

# Desired dimensions
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080

pytesseract.pytesseract.tesseract_cmd = r'B:\program files\Tesseract-OCR\tesseract.exe'

# Format: (left, upper, right, lower)
ROIS = {
    'player_name': (170, 350, 420, 400),
    #'goals': (1700, 290, 1765, 325),
    #'assists': (1693, 325, 1765, 365),
    'goals': (490, 360, 560, 400),
    'assists': (570, 360, 640, 400),
    'shots': (1700, 365, 1765, 405),
    'shot_accuracy': (1700, 405, 1765, 440),
    'passes': (1700, 440, 1765, 480),
    'pass_accuracy': (1700, 480, 1765, 520),
    'dribbles': (1700, 520, 1765, 560),
    'driblles_success_rate': (1700, 560, 1765, 600),
    'tackles': (1700, 600, 1765, 640),
    'tackle_success_rate': (1700, 640, 1765, 680),
    'offsides': (1700, 680, 1765, 720),
    'fouls_committed': (1700, 720, 1765, 755),
    'possession_won': (1700, 755, 1765, 795),
    'possesion_lost': (1700, 795, 1765, 840),
    # Add more ROIs as needed
}

# Create your views here.
def say_hello(request):
    return HttpResponse('Hello World!')

def index(request):
    return render(request, 'index.html') 

def resize_image(img):
    width, height = img.size
    if width != TARGET_WIDTH or height != TARGET_HEIGHT:
        img = img.resize((TARGET_WIDTH, TARGET_HEIGHT))
    return img

def preprocess_image(img):
    # # old version of making image black and white
    # Convert to grayscale
    # img = img.convert('L')

    # Apply a threshold to make it black and white
    # threshold = 128
    # img = img.point(lambda p: p > threshold and 255)

    # image -> black & white
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.0)

    # Sharpening
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)
    # Lower brightness
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.1)  # Adjust this value as needed

    # Boost contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(0.5)  # Adjust this value as needed

    return img

def upload_image(request):
    extracted_data = {}

    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            img = Image.open(image)

            # Resize the image
            img = resize_image(img)

            # Preprocess the image
            img = preprocess_image(img)

            for property, coordinates in ROIS.items():
                region = img.crop(coordinates)
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
                text = pytesseract.image_to_string(region, config=custom_config)  # Try with config to improve accuracy
                extracted_data[property] = text.strip()

    else:
        form = UploadImageForm()

    return render(request, 'upload.html', {'form': form, 'extracted_data': extracted_data})

# # display image and the value
# def upload_image(request):
#     extracted_data = {}

#     if request.method == 'POST':
#         form = UploadImageForm(request.POST, request.FILES)
#         if form.is_valid():
#             image = form.cleaned_data['image']
#             img = Image.open(image)

#             # Resize the image
#             img = resize_image(img)

#             # Preprocess the image
#             img = preprocess_image(img)

#             draw = ImageDraw.Draw(img)  # Create a drawing object

#             for property, coordinates in ROIS.items():
#                 region = img.crop(coordinates)
#                 custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789'
#                 text = pytesseract.image_to_string(region, config=custom_config)  # Try with config to improve accuracy
#                 extracted_data[property] = {
#                     'text': text.strip(),
#                     'region': region,  # Save the PIL region object
#                 }
                
#                 # Draw a rectangle around the ROI for visualization
#                 draw.rectangle(coordinates, outline='red', width=3)

#                 buffered = io.BytesIO()
#                 region.save(buffered, format="JPEG")
#                 encoded_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
#                 extracted_data[property]['encoded_img'] = f"data:image/jpeg;base64,{encoded_img}"

#     else:
#         form = UploadImageForm()

#     return render(request, 'upload.html', {'form': form, 'extracted_data': extracted_data})
