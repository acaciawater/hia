# -*- coding: utf-8 -*-
'''
Created on Oct 27, 2017

@author: theo
'''

import os
import csv 
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from acacia.data.models import Generator
from acacia.data.util import RDNEW, WGS84
from acacia.meetnet.models import Network, Well, Datalogger, LoggerDatasource
from acacia.meetnet.util import register_well, register_screen
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

def asfloat(x):
    try:
        return float(x)
    except:
        return None

def asdate(x):
    try:
        if x:
            start = x.strip()
        return datetime.strptime(start or '2019-09-18','%Y-%m-%d').date
    except:
        return None
    
class Command(BaseCommand):
    help = 'Import metadata.csv'
    
    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        files = options['files']
        net = Network.objects.first()
        ellitrack = Generator.objects.get(name='Ellitrack')
        admin = User.objects.get(username='theo')
        tz = pytz.timezone('Europe/Amsterdam')
        for fname in files:
            logger.info('Importing wells from {}'.format(fname))
            with open(fname) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['ID'].strip()
                    logger.info('Importing {}'.format(name))
                    x = asfloat(row['X'])
                    y = asfloat(row['Y'])
                    if x is None or y is None:
                        logger.info('Well {} skipped: No coordinates'.format(name))
                        continue
                    location=Point(x,y,srid=RDNEW)
                    location.transform(WGS84)
                    try:
                        defaults = {
                            'location': location,
                            'postcode': row['Postcode'],
                            'straat': row['Straat'],
                            'huisnummer': row['Huisnummer'],
                            'plaats': row.get('Plaats', 'Hendrik-Ido-Ambacht'),
                            'description': unicode(row['Opmerkingen locatie'],'iso8859'),
                            'maaiveld': asfloat(row['Maaiveld']),
                            'date': asdate(row.get('Constructiedatum'))
                            }
                        well, created = Well.objects.update_or_create(network=net,name=name,defaults=defaults)
                        register_well(well)
                        
                        fotodir = os.path.join(os.path.dirname(fname),'fotos')
                        for nr in range(1,6):
                            fotoname = row['Foto %d'%nr]
                            if fotoname:
                                fotopath = os.path.join(fotodir,fotoname)
                                if os.path.exists(fotopath):
                                    with open(fotopath,'rb') as f:
                                        well.add_photo(fotoname,f)
                            else:
                                break                            
   
                        logdir = os.path.join(os.path.dirname(fname),'boorstaten')
                        logname = row['Boorstaat']
                        if logname:
                            logpath = os.path.join(logdir,logname)
                            if os.path.exists(logpath):
                                with open(logpath,'rb') as f:
                                    well.set_log(logname,f)
                               
#                         #continue # only update well data, photos and logs 

                        defaults = {
                            'top': asfloat(row['Bovenkant filter m-MV']),
                            'bottom': asfloat(row['Onderkant filter m-MV']),
                            'refpnt': asfloat(row['Bovenkant buis']),
                            'depth': asfloat(row['Diepte']),
                            'diameter': asfloat(row['Diameter buis'])
                            }
                        screen, created = well.screen_set.update_or_create(nr=1,defaults=defaults)
                        register_screen(screen)
                        
                        if created:
                            logger.info('Added {screen}'.format(screen=str(screen)))
                        
                        serial = row['Logger ID']
                        if serial:
                            datalogger, created = Datalogger.objects.get_or_create(serial=serial,defaults={'model':'etd2'})
                            if created:
                                logger.info('Created logger {}'.format(serial))
                        
                            defaults = {
                                'screen': screen,
                                'start_date' : asdate(row.get('Datum installatie')),
                                'refpnt': screen.refpnt,
                                'depth': asfloat(row['Kabellengte']),
                                }
                            pos, created = datalogger.loggerpos_set.update_or_create(logger=datalogger,defaults=defaults)
                            if created:
                                logger.info('Installed {}'.format(pos))

                            ds, created = LoggerDatasource.objects.update_or_create(
                                logger = datalogger,
                                name = serial,
                                defaults={'description': 'Ellitrack datalogger {}'.format(serial),
                                          'meetlocatie': screen.mloc,
                                          'timezone': 'Europe/Amsterdam',
                                          'user': admin,
                                          'generator': ellitrack,
                                          'url': settings.FTP_URL,
                                          'username': settings.FTP_USERNAME,
                                          'password': settings.FTP_PASSWORD,
                                          })
                            if created:
                                ds.locations.add(screen.mloc)
                                logger.info('Created datasource {}'.format(ds))

#                             result = ds.download()
#                             if result:
#                                 # download succeeded, create timeseries
#                                 ds.update_parameters()
#                                 for p in ds.parameter_set.all():
#                                     series, created = p.series_set.get_or_create(
#                                         mlocatie = screen.mloc, 
#                                         name = p.name, 
#                                         defaults = {'description': p.description, 
#                                                     'unit': p.unit, 
#                                                     'user': admin})
#                                     if created:
#                                         logger.info('Created timeseries {}'.format(series))
#                                     else:
#                                         logger.info('Updating timeseries {}'.format(series))
#                                     series.update()
#                             else:
#                                 logger.info('No data for {}'.format(screen))
                    except Exception as e:
                        logger.error('{}: {}'.format(name,e))
                
        logger.info('Import completed')
