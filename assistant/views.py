import base64
import re
import cv2
import datetime
import os
import numpy as np
from io import BytesIO

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Info, QuickMessage

# imports for login and logout
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password


FACE_CASCADE_XML = "assets/face_cascade.xml"
EYE_CASCADE_XML  = "assets/eye_cascade.xml"
FACE_CASCADE     = cv2.CascadeClassifier(FACE_CASCADE_XML)
EYE_CASCADE      = cv2.CascadeClassifier(EYE_CASCADE_XML)
VISITORS_ROOT    = 'visitors/'


def verify_new_face(face) -> bool:
    face_grey = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    MIN_FACE_SIMILARITY_THRESH = 2000
    visitors_files = sorted(os.listdir(VISITORS_ROOT), reverse=True)[:9]
    for v in visitors_files:
        if v == '.gitignore': continue
        known_grey = cv2.imread(VISITORS_ROOT + v, cv2.IMREAD_GRAYSCALE)
        subtracted = cv2.subtract(face_grey, known_grey)
        _, thresholded = cv2.threshold(subtracted, 50, 255, cv2.THRESH_BINARY)
        count_non_zero = cv2.countNonZero(thresholded)
        print('Non zero for ' + v + ': ' + str(count_non_zero))
        if (count_non_zero < MIN_FACE_SIMILARITY_THRESH) and (datetime.datetime.now() - datetime.datetime.strptime(v.split('.')[0], '%Y-%m-%d %H-%M-%S')).total_seconds() < 300:  # if past 5 min, then that is a new face
            print('Face is similar to ' + v + ', skipping...')
            return False  # if faces are similar
    return True


# kudos to https://github.com/JeeveshN/Face-Detect/blob/master/detect_face.py
# for part of this function
def opencv_face_detection(imageBase64: str) -> str:
    face_detected = False
    image = cv2.imdecode(np.fromstring(base64.b64decode(imageBase64), np.uint8), cv2.IMREAD_COLOR)
    image_grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces = FACE_CASCADE.detectMultiScale(image_grey, scaleFactor=1.1, minNeighbors=6, minSize=(25, 25), flags=0)

    leeway = 10
    for x, y, w, h in faces:
        sub_img = cv2.resize(image[y - leeway:y + h + leeway, x - leeway:x + w + leeway], (180, 180))
        if verify_new_face(sub_img):
            face_detected = True
            # eye_img = image_grey[y - 10:y + h + 10, x - 10:x + w + 10]
            cv2.imwrite(VISITORS_ROOT + str(datetime.datetime.now()).replace(':', '-') + ".jpg", sub_img)
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
    visitors_dir = sorted(os.listdir(VISITORS_ROOT), reverse=True)
    # remove visitor images when there are too many of them
    if len(visitors_dir) > 100:
        for v in range(100, len(visitors_dir)):
            os.remove(VISITORS_ROOT + visitors_dir[v])
    visitors_files = visitors_dir[:9]
    return [opencv_image_to_base64(cv2.imread(VISITORS_ROOT + v)) for v in visitors_files], [v.split('.')[0].split(' ')[1].replace('-', ':') for v in visitors_files]


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
                return HttpResponseRedirect(reverse_lazy('assistant:send-message'))
            quick_message = get_object_or_404(QuickMessage, id=id)
            print('Hi ' + quick_message.message)
            save_info(quick_message.message)
        else:
            context = {}
            context['quick_messages'] = QuickMessage.objects.all()
            return render(request, 'assistant/send-message.html', context)
    return HttpResponseRedirect(reverse_lazy('assistant:index'))


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
        return HttpResponseRedirect(reverse_lazy('assistant:index'))
    else:
        context = {}
        return render(request, 'assistant/login.html', context)


def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse_lazy('assistant:index'))
