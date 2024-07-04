from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadImageForm
from PIL import Image
import pytesseract
import cv2
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'B:\program files\Tesseract-OCR\tesseract.exe'

# Format: (left, upper, right, lower)
ROIS = {
    'player_name': (170, 350, 420, 400),
    'goals': (1720, 285, 1770, 330),
    'assists': (1720, 330, 1770, 365),
    'shots': (1720, 365, 1770, 405),
    'shot_accuracy': (1720, 405, 1770, 445),
    'passes': (1720, 445, 1770, 485),
    'pass_accuracy': (1720, 480, 1775, 525),
    'dribbles': (1720, 525, 1770, 565),
    'driblles_success_rate': (1720, 565, 1770, 605),
    'tackles': (1720, 605, 1770, 645),
    'tackle_success_rate': (1720, 645, 1770, 685),
    'offsides': (1720, 685, 1770, 725),
    'fouls_committed': (1720, 725, 1770, 765),
    'possession_won': (1720, 765, 1770, 805),
    'possesion_lost': (1720, 800, 1770, 840),
    # Add more ROIs as needed
}

# Create your views here.
def say_hello(request):
    return HttpResponse('Hello World!')

def index(request):
    return render(request, 'index.html') 



def preprocess_image(image):
    # Convert image to grayscale
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Apply thresholding to get a binary image
    _, binary = cv2.threshold(blurred, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return Image.fromarray(binary)

def upload_image(request):
    extracted_data = {}

    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            img = Image.open(image)

            for property, coordinates in ROIS.items():
                region = img.crop(coordinates)
                processed_region = preprocess_image(region)
                text = pytesseract.image_to_string(processed_region, config='--psm 6')
                extracted_data[property] = text.strip()
    else:
        form = UploadImageForm()

    return render(request, 'upload.html', {'form': form, 'extracted_data': extracted_data})

# # older version
# def upload_image(request):
#     extracted_data = {}

#     if request.method == 'POST':
#         form = UploadImageForm(request.POST, request.FILES)
#         if form.is_valid():
#             image = form.cleaned_data['image']
#             img = Image.open(image)

#             for property, coordinates in ROIS.items():
#                 region = img.crop(coordinates)
#                 text = pytesseract.image_to_string(region)
#                 extracted_data[property] = text.strip()

#     else:
#         form = UploadImageForm()

#     return render(request, 'upload.html', {'form': form, 'extracted_data': extracted_data})
