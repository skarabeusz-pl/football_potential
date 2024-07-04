from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadImageForm
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'B:\program files\Tesseract-OCR\tesseract.exe'

ROIS = {
    'player_name': (50, 50, 300, 100),
    'age': (50, 150, 300, 200),
    'position': (50, 250, 300, 300),
    'rating': (50, 350, 300, 400),
    # Add more ROIs as needed
}

# Create your views here.
def say_hello(request):
    return HttpResponse('Hello World!')

def index(request):
    return render(request, 'index.html') 

def upload_image(request):
    extracted_data = {}

    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            img = Image.open(image)

            for property, coordinates in ROIS.items():
                region = img.crop(coordinates)
                text = pytesseract.image_to_string(region)
                extracted_data[property] = text.strip()

    else:
        form = UploadImageForm()

    return render(request, 'upload.html', {'form': form, 'extracted_data': extracted_data})
