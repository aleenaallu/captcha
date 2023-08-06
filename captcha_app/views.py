# from django.shortcuts import render
# # Create your views here.
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from django.utils.decorators import method_decorator
# from captcha_app.captcha_middleware import CaptchaMiddleware

# @method_decorator(CaptchaMiddleware.validate_captcha, name='dispatch')
# class CaptchaSubmitView(APIView):
#     def post(self,request,*args,**kwargs):       
#         user_input = request.POST.get('user_input') 
#         captcha = request.session.get('captcha','')

#         if user_input == captcha:
#             request.session['user_input'] == user_input
#             data = {'status':'success','message':"CAPTCHA SOLVED"}
#         else:
#             data = {'status': 'error','message':'CAPTCHA VALIDATION FAILED'}
#         return Response(data) 

from django.http import JsonResponse
from django.views import View
from .captcha_middleware import CaptchaMiddleware

class CaptchaAPI(View):
    def get(self, request):
        middleware = CaptchaMiddleware(get_response=None)
        return middleware(request)

    def post(self, request):
        middleware = CaptchaMiddleware(get_response=None)
        return middleware(request)

