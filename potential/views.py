from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Avg, Sum
from django.http import HttpResponse
from .forms import UploadImageForm, PlayerSelectForm
from .models import Player
from PIL import Image, ImageEnhance
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
    'dribbles_success_rate': (1700, 560, 1765, 600),
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
    players = Player.objects.all()
    return render(request, 'index.html', {'players': players})
# # old index
# def index(request):
#     return render(request, 'index.html') 

def resize_image(img):
    width, height = img.size
    if width != TARGET_WIDTH or height != TARGET_HEIGHT:
        img = img.resize((TARGET_WIDTH, TARGET_HEIGHT))
    return img

def process_extracted_data(extracted_data):
    processed_data = {}
    for key, value in extracted_data.items():
        try:
            processed_data[key] = int(value)
        except ValueError:
            processed_data[key] = 0
    return processed_data

def preprocess_image(img):
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

    # # old version of making image black and white
    # Convert to grayscale
    # img = img.convert('L')

    # Apply a threshold to make it black and white
    # threshold = 128
    # img = img.point(lambda p: p > threshold and 255)

    return img

def upload_image(request, player_id):
    # player = Player.objects.get(id=player_id)
    extracted_data = {}
    processed_data = {}
    potential = None
    aggregate_data = None

    form = UploadImageForm(request.POST, request.FILES)
    player = get_object_or_404(Player, id=player_id)



    if request.method == 'POST':
        if 'upload' in request.POST:
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

                # Debugging: Print extracted data
                # print("Extracted Data:", extracted_data)

                # Process the extracted data
                processed_data = process_extracted_data(extracted_data)

                # Debugging: Print processed data
                # print("Processed Data:", processed_data)

                # Update data for the player in the database
                player.goals += processed_data.get('goals', 0)
                player.assists += processed_data.get('assists', 0)
                player.shots += processed_data.get('shots', 0)
                player.passes += processed_data.get('passes', 0)
                player.dribbles += processed_data.get('dribbles', 0)
                player.tackles += processed_data.get('tackles', 0)
                player.offsides += processed_data.get('offsides', 0)
                player.fouls_committed += processed_data.get('fouls_committed', 0)
                player.possession_won += processed_data.get('possession_won', 0)
                player.possession_lost += processed_data.get('possession_lost', 0)

                player.shot_accuracy = (player.shot_accuracy + processed_data.get('shot_accuracy', 0)) / 2
                player.pass_accuracy = (player.pass_accuracy + processed_data.get('pass_accuracy', 0)) / 2
                player.dribbles_success_rate = (player.dribbles_success_rate + processed_data.get('dribbles_success_rate', 0)) / 2
                player.tackle_success_rate = (player.tackle_success_rate + processed_data.get('tackle_success_rate', 0)) / 2

                player.save()

                # Calculate potential
                potential = player.calculate_potential()

        elif 'clear' in request.POST:
            player.goals = 0
            player.assists = 0
            player.shots = 0
            player.shot_accuracy = 0
            player.passes = 0
            player.pass_accuracy = 0
            player.dribbles = 0
            player.dribbles_success_rate = 0
            player.tackles = 0
            player.tackle_success_rate = 0
            player.offsides = 0
            player.fouls_committed = 0
            player.possession_won = 0
            player.possession_lost = 0
            player.save()

        # Aggregate data
        total_count = Player.objects.filter(id=player_id).count()
        sum_data = Player.objects.filter(id=player_id).aggregate(
            Sum('goals'), Sum('assists'), Sum('shots'), Sum('passes'),
            Sum('dribbles'), Sum('tackles'), Sum('offsides'), Sum('fouls_committed'),
            Sum('possession_won'), Sum('possession_lost')
        )
        avg_data = Player.objects.filter(id=player_id).aggregate(
            Avg('shot_accuracy'), Avg('pass_accuracy'), Avg('dribbles_success_rate'), Avg('tackle_success_rate')
        )
        aggregate_data = {
            'goals': sum_data['goals__sum'],
            'assists': sum_data['assists__sum'],
            'shots': sum_data['shots__sum'],
            'passes': sum_data['passes__sum'],
            'dribbles': sum_data['dribbles__sum'],
            'tackles': sum_data['tackles__sum'],
            'offsides': sum_data['offsides__sum'],
            'fouls_committed': sum_data['fouls_committed__sum'],
            'possession_won': sum_data['possession_won__sum'],
            'possession_lost': sum_data['possession_lost__sum'],
            'shot_accuracy': avg_data['shot_accuracy__avg'],
            'pass_accuracy': avg_data['pass_accuracy__avg'],
            'dribbles_success_rate': avg_data['dribbles_success_rate__avg'],
            'tackle_success_rate': avg_data['tackle_success_rate__avg'],
            'total_count': total_count
        }

    else:
        form = UploadImageForm()

    return render(request, 'upload.html', {
        'form': form,
        'extracted_data': extracted_data,
        'processed_data': processed_data,
        'potential': potential,
        'aggregate_data': aggregate_data,
        'player': player
    })

