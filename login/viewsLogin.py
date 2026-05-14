from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse

from login.service import AuthService


authSvc = AuthService()


def getUserId(request: HttpRequest) -> str:
    # return userId from session or empty string
    return request.session.get("userId", "")


def loginRequired(request: HttpRequest) -> bool:
    # true if no active session exists
    return not getUserId(request)


def adminRequired(request: HttpRequest) -> bool:
    # true if user is not an admin
    return request.session.get("role", "") != "admin"


# Auth

def loginView(request: HttpRequest) -> HttpResponse:
    # redirect to forum if session already active
    if getUserId(request):
        return redirect("forum:home")

    if request.method == "POST":
        email    = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "login/login.html")

        result = authSvc.login(email, password)

        if not result["ok"]:
            messages.error(request, result["error"])
            return render(request, "login/login.html")

        # save minimal user data in session
        request.session["userId"]   = result["userId"]
        request.session["fullName"] = result["fullName"]
        request.session["role"]     = result["role"]
        request.session["career"]   = result["career"]

        return redirect("forum:home")

    return render(request, "login/login.html")


def registerView(request: HttpRequest) -> HttpResponse:
    # redirect to forum if session already active
    if getUserId(request):
        return redirect("forum:home")

    if request.method == "POST":
        fullName = request.POST.get("fullName", "").strip()
        email    = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        career   = request.POST.get("career", "").strip()
        role     = request.POST.get("role", "student").strip()
        phone    = request.POST.get("phone", "").strip()

        if not all([fullName, email, password, career, phone]):
            messages.error(request, "All fields are required.")
            return render(request, "login/register.html")

        result = authSvc.register(
            fullName = fullName,
            email    = email,
            password = password,
            career   = career,
            role     = role,
            phone    = phone,
        )

        if not result["ok"]:
            messages.error(request, result["error"])
            return render(request, "login/register.html")

        messages.success(request, "Account created. Please log in.")
        return redirect("login:login")

    return render(request, "login/register.html")


def logoutView(request: HttpRequest) -> HttpResponse:
    # clear all session data and redirect to login
    request.session.flush()
    return redirect("login:login")


# Profile (own account) 

def profileView(request: HttpRequest) -> HttpResponse:
    # show current user profile
    if loginRequired(request):
        return redirect("login:login")

    user = authSvc.getSessionUser(getUserId(request))
    if not user:
        request.session.flush()
        return redirect("login:login")

    return render(request, "login/profile.html", {"user": user})


def profileEditView(request: HttpRequest) -> HttpResponse:
    # allow user to edit their own profile fields
    if loginRequired(request):
        return redirect("login:login")

    userId = getUserId(request)
    user   = authSvc.getUserById(userId)

    if not user:
        return redirect("login:profile")

    if request.method == "POST":
        payload = {
            "fullName": request.POST.get("fullName", "").strip(),
            "career":   request.POST.get("career", "").strip(),
            "phone":    request.POST.get("phone", "").strip(),
            "password": request.POST.get("password", "").strip() or None,
        }

        # remove empty optional fields before updating
        payload = {k: v for k, v in payload.items() if v}

        updated = authSvc.updateUser(userId, payload)

        if updated:
            # keep session fullName in sync after edit
            request.session["fullName"] = updated["fullName"]
            messages.success(request, "Profile updated.")

        return redirect("login:profile")

    return render(request, "login/profile_edit.html", {"user": user})


def profileDeleteView(request: HttpRequest) -> HttpResponse:
    # permanently delete own account and clear session
    if loginRequired(request):
        return redirect("login:login")

    if request.method == "POST":
        authSvc.deleteUser(getUserId(request))
        request.session.flush()
        messages.success(request, "Account deleted.")
        return redirect("login:login")

    user = authSvc.getUserById(getUserId(request))
    return render(request, "login/profile_confirm_delete.html", {"user": user})


# Admin: user management 

def userListView(request: HttpRequest) -> HttpResponse:
    # list all users; admin only
    if loginRequired(request) or adminRequired(request):
        return redirect("login:login")

    users = authSvc.getAllUsers()
    return render(request, "login/user_list.html", {"users": users})


def userDetailView(request: HttpRequest, userId: str) -> HttpResponse:
    # show full profile of any user; admin only
    if loginRequired(request) or adminRequired(request):
        return redirect("login:login")

    user = authSvc.getUserById(userId)
    if not user:
        messages.error(request, "User not found.")
        return redirect("login:user_list")

    return render(request, "login/user_detail.html", {"user": user})


def userEditView(request: HttpRequest, userId: str) -> HttpResponse:
    # edit any user account; admin only
    if loginRequired(request) or adminRequired(request):
        return redirect("login:login")

    user = authSvc.getUserById(userId)
    if not user:
        messages.error(request, "User not found.")
        return redirect("login:user_list")

    if request.method == "POST":
        payload = {
            "fullName": request.POST.get("fullName", "").strip(),
            "email":    request.POST.get("email", "").strip(),
            "career":   request.POST.get("career", "").strip(),
            "phone":    request.POST.get("phone", "").strip(),
            "role":     request.POST.get("role", "").strip(),
            "password": request.POST.get("password", "").strip() or None,
        }

        payload = {k: v for k, v in payload.items() if v}

        authSvc.updateUser(userId, payload)
        messages.success(request, "User updated.")
        return redirect("login:user_detail", userId=userId)

    return render(request, "login/user_edit.html", {"user": user})


def userDeleteView(request: HttpRequest, userId: str) -> HttpResponse:
    # permanently delete any user account; admin only
    if loginRequired(request) or adminRequired(request):
        return redirect("login:login")

    user = authSvc.getUserById(userId)
    if not user:
        messages.error(request, "User not found.")
        return redirect("login:user_list")

    if request.method == "POST":
        authSvc.deleteUser(userId)
        messages.success(request, "User deleted.")
        return redirect("login:user_list")

    return render(request, "login/user_confirm_delete.html", {"user": user})