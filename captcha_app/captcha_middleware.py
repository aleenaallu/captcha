from django.urls import reverse
from django.http import JsonResponse
from PIL import Image, ImageDraw, ImageFont, ImageOps
from functools import wraps
import uuid, base64, random, io ,os
from io import BytesIO
from datetime import datetime, timedelta
from user.User.UserLogin.models import UserLogin
from django.middleware.csrf import get_token
from utility.font_list import arial, times, verdana, georgia, calibri,data_base_dir 
class CaptchaMiddleware:

    alphabet_uppercase = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
    alphabet_lowercase = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
    number_list = ['0','1','2','3','4','5','6','7','8','9']
    captcha_length = 5
    captcha_font_size = 25
    img_width = 160
    img_height = 60
    border_width = 2
    border_color = (255,255,255)
    captcha_time_limt = 300 #5 minute in seconds
    captcha_max_attempt = 3

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from user.User.UserLogin.views import CustomerLogin, SuperAdminLogin
        print("Hi captcha")
        if request.method == 'GET' and request.path == '/captcha/':
            captcha_id = self.validate_captcha_id(request.GET.get('captcha_id'),request)
            
            captcha = CaptchaMiddleware.create_random_captcha_text(self) 
            image = self.create_image_captcha(captcha)    
            
            request.session['captcha_id'] = captcha_id
            request.session['captcha'] = captcha
            request.session['user_input'] = None
                 
            if image is None:
                return JsonResponse(
                    {
                    'status':'error',
                    'message':'Unable to create captcha image'
                    },
                    status=404,
                    content_type="application/json")
            data = {
                'status' : 'success',
                'captcha_id': captcha_id,
                "image": image,
            }
            return JsonResponse(data)
        
        elif request.method == 'POST' and request.path == reverse('captcha'):
            captcha_id = self.validate_captcha_id(request.POST.get('captcha_id'),request)
            
            # Check if the captcha_id is a URL and redirect to the appropriate login view
            if captcha_id.startswith('/'):
                if captcha_id == reverse('CustomerLogin'):
                    return self.CustomerLogin(request)
                elif captcha_id == reverse('SuperAdminLogin'):
                    return self.SuperAdminLogin(request)
         
            user_input = request.POST.get('user_input')
            stored_captcha = request.session.get('captcha','')
            
            if captcha_id != request.session.get('captcha_id'):
                return JsonResponse(
                    {
                    'status': 'error',
                    'message':'Invalid captcha id'
                    },
                    status=400,
                    content_type="application/json")

            elif user_input is None :
                if request.session.get('captcha_max_attempt',0) >=self.captcha_max_attempt: # captcha retry limit
                    return JsonResponse(
                        {
                        'status': 'error', 
                        'message': 'You have exceeded the captcha retry limit. Please try again later.'
                        }, 
                        status=429, 
                        content_type="application/json")
                
                elif user_input == stored_captcha or self.validate_captcha_text(request):
                    # Captcha successfully solved
                    request.session['user_input'] = user_input
                    request.session['captcha_max_attempt'] = 0 # Reset retry count on success
                    
                    # Update user authentication status
                    user = UserLogin.objects.filter(id=request.user.id).first()
                    if user:
                        user.is_captcha_solved = True
                        user.save()

                    return JsonResponse({
                        'status': 'success',
                        'message':'Captcha successfuly solved'
                        },
                        status=200,
                        content_type="application/json")
                else:
                    # invalid captcha
                    request.session['captcha_max_attempt'] = request.session.get('captcha_max_attempt',0) + 1 
                    return JsonResponse(
                        {
                        'status': 'error', 
                        'message':'Invalid captcha ,Please try again'
                        },
                        status=400,
                        content_type="application/json") 
            else:
                return JsonResponse(
                    {
                    'status':'error',
                    'message':'Missing captcha information'
                    },
                    status=405,
                    content_type="application/json")
            
        return self.get_response(request)
       
    def create_random_captcha_text(self, captcha_string_size = None):
        if captcha_string_size is None:
            captcha_string_size = self.captcha_length

        base_chr = self.alphabet_uppercase + self.alphabet_lowercase + self.number_list
        captcha = ''.join(random.choice(base_chr) for i in range(captcha_string_size))
        return captcha
    
    def create_image_captcha(self, captcha):
        image = Image.new('RGB', (self.img_width, self.img_height), color=(255, 255, 255))
        image = ImageOps.expand(image, border=(self.border_width, self.border_width), fill=self.border_color)
        draw = ImageDraw.Draw(image)     
        font_list = ['arial', 'times', 'verdana', 'georgia','calibri']
        font_name = random.choice(font_list)
        font_path = os.path.join(data_base_dir,font_name + '.ttf')
        font = ImageFont.truetype(font_path, self.captcha_font_size)
       
        text_width, text_height = draw.textsize(captcha, font=font)
        x = (self.img_width - text_width) // 2
        y = (self.img_height - text_height) // 2                
        draw.text((x, y), captcha, font=font, fill=(0, 0, 0))
        
        for i in range(50):         #point
            x = random.randint(0,self.img_width)
            y = random.randint(0,self.img_height)
            draw.point((x,y),fill=(0,0,0))
        
        for i in range(10):         #line
            x1 = random.randint(0,self.img_width)
            y1 = random.randint(0,self.img_height)
            x2 = random.randint(0,self.img_width)
            y2 = random.randint(0,self.img_height)
            draw.line([(x1,y1),(x2,y2)],fill=(255,255,255),width = 2)
        
        image.show(captcha)
        image_byte = io.BytesIO()
        image.save(image_byte,format = 'JPEG')
        image_base = base64.b64encode(image_byte.getvalue()).decode('utf-8')
        return image_base

    @staticmethod
    def validate_captcha_text(request):
        user_input = request.POST.get('user_input')
        captcha = request.session.get('captcha')
        captcha_time = request.session.get('captcha_time')

        if user_input == captcha and datetime.now() < captcha_time +timedelta(seconds=CaptchaMiddleware.captcha_time_limt):
            request.session['user_input'] = user_input
            return True
        else:
            return False
    
    @staticmethod   
    def validate_captcha_id(captcha_id,request):
            try:
                uuid.UUID(captcha_id)
                return captcha_id
            except (TypeError,ValueError):
                user_role = request.POST.get('user_role')

                if user_role == 'customer':
                    return reverse('CustomerLogin')
                elif user_role == 'superadmin':
                    return reverse('SuperAdminLogin')
                else:
                    return str(uuid.uuid4())    
       
    def validate_captcha(view_func):
        @wraps(view_func)
        def wrapped_view(request,*args,**kwargs):
            captcha_id = request.POST.get('captcha_id')
            user_input = request.POST.get('user_input')
            if not CaptchaMiddleware.validate_captcha_id(captcha_id):
                return JsonResponse(
                    {
                    'status':'error',
                    'message':'Invalid captcha ID'
                    },
                    status = 400)
            if not CaptchaMiddleware().validate_captcha_text(user_input):
                return JsonResponse(
                    {
                    'status':'error',
                    'message':'Invalid captcha text'
                    },
                    status = 400)
            
            # Check if the captcha is successfully solved
            user = UserLogin.objects.filter(id=request.user.id).first()
            if user and not user.is_captcha_solved:
                return JsonResponse(
                    {
                        'status':'error',
                        'message': 'Captcha validation failed'

                    },
                    status = 400
                )
            return view_func(request, *args ,**kwargs)
        return wrapped_view
    


