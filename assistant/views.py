from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib import messages

from .models import Info, QuickMessage

# imports for login and logout
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password


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
