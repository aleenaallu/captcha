from django.urls import path
from captcha_app.views import CaptchaAPI
urlpatterns = [
    path('captcha/', CaptchaAPI.as_view(),name='captcha')
]