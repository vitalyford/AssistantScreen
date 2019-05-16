import base64
import re
import cv2
import datetime
from io import BytesIO

from PIL import Image, ImageFilter

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib import messages

from .models import Info, QuickMessage

# imports for login and logout
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password


CASCADE = "face_cascade.xml"
FACE_CASCADE = cv2.CascadeClassifier(CASCADE)


def opencv_face_detection(filename: str) -> str:
    image = cv2.imread(filename)
    image_grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = FACE_CASCADE.detectMultiScale(image_grey, scaleFactor=1.16, minNeighbors=5, minSize=(25, 25), flags=0)

    for x, y, w, h in faces:
        sub_img = image[y - 10:y + h + 10, x - 10:x + w + 10]
        cv2.imwrite('visitors/' + str(datetime.datetime.now()).replace(':', '-') + ".jpg", sub_img)
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 0), 2)

    return opencv_image_to_base64(image)


def detect_face(request):
    filename = 'temp.jpg'
    context = {}
    imageBase64 = re.search(r'base64,(.*)', request.POST.get('imageBase64')).group(1)
    img = save_image_from_base64(imageBase64, filename)
    img = img.filter(ImageFilter.FIND_EDGES)
    opencv_face_detection(filename)
    context['imgB64'] = 'data:image/jpeg;base64,' + opencv_face_detection(filename)
    # context['imgB64'] = 'data:image/jpeg;base64,' + PIL_image_to_base64(img)
    context['status'] = 'success'
    return JsonResponse(context)


def save_image_from_base64(imageBase64: str, filename: str) -> Image:
    imgdata = base64.b64decode(imageBase64)
    img = Image.open(BytesIO(imgdata))
    with open(filename, 'wb') as f:
        f.write(imgdata)
    return img


def opencv_image_to_base64(image) -> str:
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('UTF-8')


def PIL_image_to_base64(image: Image) -> str:
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('UTF-8')


def check_for_update(request):
    context = {}
    info = get_info()
    if info is not None:
        context['message'] = info.message
    context['status'] = 'success'
    return JsonResponse(context)


def send_message(request):
    if request.user.is_superuser:
        if 'message' in request.POST and request.POST.get('message') != '':
            save_info(request.POST.get('message'))
        elif 'quickSelect' in request.POST:
            try:
                id = int(request.POST.get('quickSelect'))
            except:
                messages.warning(request, 'Do not mess with the ID field')
                return HttpResponseRedirect(reverse('assistant:send-message'))
            quick_message = get_object_or_404(QuickMessage, id=id)
            print('Hi ' + quick_message.message)
            save_info(quick_message.message)
        else:
            context = {}
            context['quick_messages'] = QuickMessage.objects.all()
            return render(request, 'assistant/send-message.html', context)
    return HttpResponseRedirect(reverse('assistant:index'))


def save_info(message: str):
    info = Info.objects.all()
    if info.count() > 0:
        info = info[0]
        info.message = message
    else:
        info = Info(message=message)
    info.save()


def get_info():
    info = Info.objects.all()
    if info.count() > 0:
        return info[0]
    return None


def index(request):
    context = {}
    info = get_info()
    if info is not None:
        context['info'] = info
    return render(request, 'assistant/index.html', context)


def login_user(request):
    if request.method == 'POST' and 'username' in request.POST and 'password' in request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            # request.session.set_expiry(settings.SESSION_EXPIRY_TIME)
            login(request, user)
        return HttpResponseRedirect(reverse('assistant:index'))
    else:
        context = {}
        return render(request, 'assistant/login.html', context)


def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse('assistant:index'))
