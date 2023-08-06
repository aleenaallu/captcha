from django.db import models
# Create your models here.
class CaptchaModel(models.Model):

    captcha_id = models.CharField(max_length=36)
    image = models.ImageField()

    def __str__(self):
        return str(self.captcha_id)
