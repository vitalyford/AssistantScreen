import base64
import re
import cv2
import datetime
import os
import numpy as np
from io import BytesIO

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib import messages

from .models import Info, QuickMessage

# imports for login and logout
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password


FACE_CASCADE_XML = "faces/face_cascade.xml"
EYE_CASCADE_XML  = "faces/eye_cascade.xml"
FACE_CASCADE = cv2.CascadeClassifier(FACE_CASCADE_XML)
EYE_CASCADE  = cv2.CascadeClassifier(EYE_CASCADE_XML)


# kudos to https://github.com/JeeveshN/Face-Detect/blob/master/detect_face.py
# for part of this function
def opencv_face_detection(imageBase64: str) -> str:
    face_detected = False
    image = cv2.imdecode(np.fromstring(base64.b64decode(imageBase64), np.uint8), cv2.IMREAD_COLOR)
    image_grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = FACE_CASCADE.detectMultiScale(image_grey, scaleFactor=1.1, minNeighbors=6, minSize=(25, 25), flags=0)

    for x, y, w, h in faces:
        face_detected = True
        sub_img = image[y - 10:y + h + 10, x - 10:x + w + 10]
        # eye_img = image_grey[y - 10:y + h + 10, x - 10:x + w + 10]
        cv2.imwrite('visitors/' + str(datetime.datetime.now()).replace(':', '-') + ".jpg", cv2.resize(sub_img, (180, 180)))
        # cv2.rectangle(image, (x, y), (x + w, y + h), (255, 255, 0), 2)
        # circle the face
        # cv2.circle(image, (x + int(w / 2), y + int(h / 2)), int(max(w / 2, h / 2)), (255, 255, 0), 2)
        # detect eyes
        # eyes = EYE_CASCADE.detectMultiScale(eye_img, scaleFactor=1.1, minNeighbors=2, minSize=(25, 25), flags=0)
        # draw eyes
        # for x_eye, y_eye, w_eye, h_eye in eyes:
        #     cv2.circle(image, (x + x_eye + int(w_eye / 2) - 10, y + y_eye + int(h_eye / 2) - 10), int(min(w_eye / 2, h_eye / 2)), (0, 255, 0), 2)

    return face_detected  # opencv_image_to_base64(image)


def get_recent_visitors_base64_images() -> []:
    visitors_files = sorted(os.listdir('visitors/'), reverse=True)[:9]
    return [opencv_image_to_base64(cv2.imread('visitors/' + v)) for v in visitors_files], [v.split('.')[0].split(' ')[1].replace('-', ':') for v in visitors_files]


def detect_face(request):
    context = {}
    imageBase64 = re.search(r'base64,(.*)', request.POST.get('imageBase64')).group(1)
    context['face_detected'] = opencv_face_detection(imageBase64)
    if context['face_detected'] or 'firstRequest' in request.POST:
        context['visitors'], context['time'] = get_recent_visitors_base64_images()
    context['status'] = 'success'
    return JsonResponse(context)


def opencv_image_to_base64(image) -> str:
    _, buffer = cv2.imencode('.jpg', image)
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('UTF-8')


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
