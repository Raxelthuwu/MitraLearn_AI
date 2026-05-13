from django.urls import path
from login import viewsLogin

app_name = "login"

urlpatterns = [
    # auth
    path("",          viewsLogin.loginView,    name="login"),
    path("register/", viewsLogin.registerView, name="register"),
    path("logout/",   viewsLogin.logoutView,   name="logout"),

    # own profile
    path("profile/",        viewsLogin.profileView,       name="profile"),
    path("profile/edit/",   viewsLogin.profileEditView,   name="profile_edit"),
    path("profile/delete/", viewsLogin.profileDeleteView, name="profile_delete"),

    # admin user management
    path("users/",                    viewsLogin.userListView,   name="user_list"),
    path("users/<str:userId>/",       viewsLogin.userDetailView, name="user_detail"),
    path("users/<str:userId>/edit/",  viewsLogin.userEditView,   name="user_edit"),
    path("users/<str:userId>/delete/",viewsLogin.userDeleteView, name="user_delete"),
]