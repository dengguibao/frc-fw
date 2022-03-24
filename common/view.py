from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from common.captcha import Captcha
from django.core.cache import cache
from django.http.response import HttpResponse


@api_view(('GET',))
@permission_classes((AllowAny,))
def build_image_verify_code_endpoint(request):
    captcha = Captcha.instance()
    txt, img = captcha.generate_captcha()
    cache.set('img_verify_code_%s' % txt, True, 180)
    return HttpResponse(img, content_type="image/png")