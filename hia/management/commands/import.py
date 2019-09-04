'''
Created on Sep 4, 2019

@author: theo
'''
from django.core.management.base import BaseCommand
import logging
from acacia.meetnet.models import Network
import csv
from django.contrib.gis.geos.point import Point
from acacia.meetnet.util import register_well, register_screen
from datetime import datetime
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    args = ''
    help = 'Import csv with well data'
    
    def add_arguments(self,parser):
        
        parser.add_argument('--file','-f',
                action='store',
                dest = 'fname',
                default = '',
                help = 'csv file with well data')

    def handle(self, *args, **options):
        # get the first superuser
#         user=User.objects.filter(is_superuser=True).first()
        fname = options.get('fname')
        if not fname:
            raise('csv file missing')
        net = Network.objects.first()
        with open(fname,'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['label']
                filter = 1
                x = float(row['x'])
                y = float(row['y'])
                datum = row['plaatsing [date]'].strip()
                if len(datum):
                    datum = datetime.strptime(datum,'%m/%d/%Y').date()
                bkb = row['bovenkant peilbuis [mNAP]'] or None
                top = row['filter bovenkant [mNAP]'] or None
                bottom = row['filter onderkant [mNAP]'] or None
                dia = row['Filter-diameter'] or None
                loc = Point(x=x,y=y,srid=28992)
                loc.transform(4326)
                print(name,loc.x,loc.y)
                well,created = net.well_set.update_or_create(name=name,defaults={'location':loc,'date':datum or None})
                register_well(well)
                screen,created = well.screen_set.get_or_create(nr=filter,defaults={'top':top,'bottom':bottom,'diameter':dia,'refpnt':bkb})
                register_screen(screen)
                