from django.urls import path

from .views import LoginView, LogoutView, ProfileView, RegisterView


urlpatterns = [
    path("register", RegisterView.as_view(), name="auth-register"),
    path("register/", RegisterView.as_view(), name="auth-register-slash"),
    path("login", LoginView.as_view(), name="auth-login"),
    path("login/", LoginView.as_view(), name="auth-login-slash"),
    path("logout", LogoutView.as_view(), name="auth-logout"),
    path("logout/", LogoutView.as_view(), name="auth-logout-slash"),
    path("profile", ProfileView.as_view(), name="auth-profile"),
    path("profile/", ProfileView.as_view(), name="auth-profile-slash"),
]
