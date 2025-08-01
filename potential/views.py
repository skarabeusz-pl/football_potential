from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .forms import UploadImageForm
from .models import Player
from PIL import Image, ImageEnhance
import pytesseract
import io
import base64
from datetime import date, datetime, timedelta
from django.utils import timezone

# wymiary inputu
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080

pytesseract.pytesseract.tesseract_cmd = r'B:\program files\Tesseract-OCR\tesseract.exe'

# pixelowe ROI
ROIS = {
    #'player_name': (170, 350, 420, 400),
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
}

def say_hello(request):
    """Simple hello world endpoint."""
    return HttpResponse('Hello World!')

def show_potential(request, player_id):
    player = get_object_or_404(Player, id=player_id)

    # dane do filtracji daty
    days = request.GET.get("days")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")


    today = datetime.today().date()
    date_ranges = {
        "7": today - timedelta(days=7),
        "14": today - timedelta(days=14),
        "30": today - timedelta(days=30),
        "all": None
    }

    if days in date_ranges:
        start_date = date_ranges[days]
        end_date = today
    elif start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            start_date, end_date = None, None  # reset daty w przypadku złego inputu

    # zaciągnięcie z get_all_aggregate_data z modelu
    all_aggregate_data, stats = player.get_all_aggregate_data(start_date, end_date)
    position_potential_scores = player.calculate_position_based_potential(start_date, end_date)

    return render(request, "show_potential.html", {
        "player": player,
        "all_aggregate_data": all_aggregate_data,
        "stats": sorted(stats),
        "position_potential_scores": position_potential_scores,
        "filter_option": days if days else "custom",
        "custom_start": start_date,
        "custom_end": end_date,
    })

def index(request):
    players = Player.objects.all()
    return render(request, 'index.html', {'players': players})

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

# metoda do obróbki obrazu przed OCR
# L - grayscale
# point - binaryzacja
#  
def preprocess_image(img):

    img = img.convert('L')
    threshold = 128
    img = img.point(lambda p: 255 if p > threshold else 0)
    enhancers = [
    (ImageEnhance.Sharpness, 2.0),
    (ImageEnhance.Brightness, 0.9),
    (ImageEnhance.Contrast, 1.5),]

    for enhancer_class, val in enhancers:
        enhancer = enhancer_class(img)
        img = enhancer.enhance(val)
    return img

def upload_image(request, player_id):
    # inicjalizacja zmiennych
    extracted_data = {}
    processed_data = {}
    validation_data = {}
    potential = None
    aggregate_data = None
    all_aggregate_data = {}

    player = get_object_or_404(Player, id=player_id)
    form = UploadImageForm(request.POST, request.FILES) if request.method == 'POST' else UploadImageForm()
    today = timezone.now().date()
    today_str = today.strftime('%Y-%m-%d')

    if request.method == 'POST':
        # upload ------>
        if 'upload' in request.POST:
            if form.is_valid():
                position = request.POST.get("position", "Unknown")  # Default to "Unknown" if not provided
                
                # obróbka obrazu
                image = form.cleaned_data['image']
                img = Image.open(image)
                img = resize_image(img)
                img = preprocess_image(img)

                # wycięcie regionów z obrazu
                for property, coordinates in ROIS.items():
                    region = img.crop(coordinates)
                    buffer = io.BytesIO()
                    region.save(buffer, format="PNG")
                    roi_image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789' # skupia się na cyfrach
                    text = pytesseract.image_to_string(region, config=custom_config).strip()
                    extracted_data[property] = text
                    validation_data[property] = {
                        'value': text,
                        'roi': roi_image_base64,
                    }

                request.session['validation_data'] = validation_data
                request.session['player_id'] = player_id
                request.session['category'] = request.POST.get('category', 'random')
                request.session['position'] = position
                entry_date = form.cleaned_data.get('entry_date', date.today())
                request.session['entry_date'] = entry_date.strftime('%Y-%m-%d')

                return render(request, 'validate.html', {
                    'validation_data': validation_data,
                    'player': player,
                })

        # save ------->
        elif 'save' in request.POST:
            validation_data = request.session.get('validation_data', {})
            category = request.session.get('category', 'random')
            position = request.session.get('position', "Unknown")
            entry_date_str = request.session.get('entry_date', today_str)
            try:
                entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d').date()
            except ValueError:
                entry_date = today

            for key in validation_data.keys():
                validation_data[key]['value'] = request.POST.get(key, validation_data[key]['value'])

            processed_data = {
                key: int(value['value']) if value['value'].isdigit() else 0
                for key, value in validation_data.items()
            }

            player.calculate_aggregate(processed_data, category, entry_date, position)

            request.session.pop('validation_data', None)
            request.session.pop('category', None)
            request.session.pop('entry_date', None)
            request.session.pop('position', None)

            position_potential_scores = player.calculate_position_based_potential(start_date=entry_date, end_date=entry_date)

            # potencjał ze względu na pozycję i rodzaj spotkania
            potential = position_potential_scores.get(position, {}).get(category, "N/A")

            # zostawiamy na porównania z bazą danych
            aggregate_data = player.get_aggregate_data(category)
            all_aggregate_data = player.get_all_aggregate_data()

    return render(request, 'upload.html', {
        'form': form,
        'extracted_data': extracted_data,
        'processed_data': processed_data,
        'validation_data': validation_data,
        'potential': potential,
        'aggregate_data': aggregate_data,
        'all_aggregate_data': all_aggregate_data,
        'player': player,
        'today': today_str  # NIE ZMIENIAĆ - musi być string!
    })

# OUTDATED.

def clear_all_data(request, player_id):
    player = get_object_or_404(Player, id=player_id)

    if request.method == "POST":
        
        for category_field in ['training_stats', 'official_game_stats', 'random_stats']:
            setattr(player, category_field, {})  

        player.save()

    return redirect('show_potential', player_id=player.id) 
