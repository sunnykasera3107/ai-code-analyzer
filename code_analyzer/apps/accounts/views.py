# apps/accounts/views.py
import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout


def register(request):
    if request.method == "POST":
        data = request.POST

        username = data.get("username")
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")

        if User.objects.filter(username=username).exists():
            return render(request, "login.html", {"error": "User already exists"})

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        group = Group.objects.get(name="Authenticated")   # group must exist
        user.groups.add(group)

        return redirect("/auth/login/")  # or success page

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        data = request.POST

        user = authenticate(
            username=data.get("username"),
            password=data.get("password")
        )

        if user is None:
            return render(request, "login.html", {"error": "Invalid credentials"})

        login(request, user)

        return redirect("/")
    
    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect("/auth/login")