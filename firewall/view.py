from django.shortcuts import render


def index_endpoint(request):
    return render(request, 'index/index.html', {
        'api_url': 'http://%s' % request.META['HTTP_HOST']
    })
