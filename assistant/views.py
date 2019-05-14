from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.contrib import messages

from .models import Info

# imports for login and logout
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password


def send_message(request):
    if request.user.is_superuser and 'message' in request.POST:
        message = request.POST.get('message')
        info = Info.objects.all()
        if info.count() > 0:
            info.message = message
            info.save()
        else:
            info = Info(message=message)
            info.save()
    elif request.user.is_superuser:
        return render(request, 'assistant/send-message.html', {})
    return render(request, 'assistant/index.html', {})


def index(request):
    context = {}
    info = Info.objects.all()
    if info.count() > 0:
        context['info'] = info[0]
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
