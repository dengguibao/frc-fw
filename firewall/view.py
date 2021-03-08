from django.http import FileResponse


def read_api_ref_endpoint(request):
    fp = open('api_ref.md', 'rb')
    response = FileResponse(fp)
    return response