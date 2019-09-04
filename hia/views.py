'''
Created on Sep 1, 2019

@author: theo
'''
import json

from django.conf import settings
from django.http.response import JsonResponse, HttpResponseServerError,\
    HttpResponse
from django.views.generic.detail import DetailView

from acacia.meetnet.models import Network, Well
from acacia.meetnet.views import NetworkView
import zipfile
from bro.gmw import registration_request
import StringIO
from xml.etree.ElementTree import ElementTree
from django.utils.text import slugify

class HomeView(NetworkView):
    template_name = 'hia/home.html'

    def get_context_data(self, **kwargs):
        context = NetworkView.get_context_data(self, **kwargs)
        options = {
            'center': [52.15478, 4.48565],
            'zoom': 12 }
        context['api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['options'] = json.dumps(options)
        return context

    def get_object(self):
        return Network.objects.first()

class PopupView(DetailView):
    """ returns html response for leaflet popup """
    model = Well
    template_name = 'meetnet/well_info.html'
    
def well_locations(request):
    """ return json response with well locations
    """
    result = []
    for p in Well.objects.all():
        try:
            pnt = p.location
            result.append({'id': p.id, 'name': p.name, 'nitg': p.nitg, 'description': p.description, 'lon': pnt.x, 'lat': pnt.y})
        except Exception as e:
            return HttpResponseServerError(unicode(e))
    return JsonResponse(result,safe=False)


def download_bro(request):
    ''' download ZIP file with BRO registration requests for all wells '''
    io = StringIO.StringIO()
    zf = zipfile.ZipFile(io,'w')
    for well in Well.objects.all():
        request = ElementTree(registration_request(well,kvk='73552739'))
        xml = StringIO.StringIO()
        request.write(xml,xml_declaration=True,encoding='utf-8')
        zf.writestr(slugify(well.nitg or well.name) + '.xml', xml.getvalue())
    zf.close()
    resp = HttpResponse(io.getvalue(), content_type = "application/x-zip-compressed")
    resp['Content-Disposition'] = 'attachment; filename=bro.zip'
    return resp
