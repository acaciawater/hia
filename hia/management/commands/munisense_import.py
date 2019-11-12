# -*- coding: utf-8 -*-
'''
Created on Sep 27, 2019

@author: theo
'''

import re 
import logging
import csv

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from acacia.meetnet.models import Well
import os
from datetime import datetime
import pytz
from acacia.data.models import DataPoint
import itertools

logger = logging.getLogger(__name__)
    
class Command(BaseCommand):
    help = 'Import Munisense csv export'
    
    def add_arguments(self, parser):
        parser.add_argument('folder', help='Folder with csv files', type=str)

    def handle(self, *args, **options):
        pattern = r'csv_results_\d+_(?P<nr>\d+)_\d+\.csv'
        tz = pytz.timezone('Europe/Amsterdam')
        end_date = datetime(2019,9,18,0,0,0,0,tz)
        folder = options['folder']
        logger.info('Importing data from folder {}'.format(folder))
        for path, _dirs, files in os.walk(folder):
            for fname in files:
                match = re.match(pattern,fname)
                if not match:
                    logger.info('File {} skipped: no filename match.'.format(fname))
                    continue
                nr = int(match.group('nr'))
                name = '{:03}'.format(nr)
                try:
                    well = Well.objects.get(name=name)
                except Well.DoesNotExist:
                    logger.warning('File {} skipped: well {} not found.'.format(fname, name))
                    continue

                screen = well.screen_set.first() # there is only one screen!
                series = screen.find_series()
                
                logger.info('Loading file {}'.format(fname))
                with open(os.path.join(path,fname),'r') as f:
                    reader = csv.DictReader(f,delimiter=';')
                    points = []
                    for row in reader:
                        timestamp = row['result_timestamp']
                        level = row['water_level_validated_value']
                        if timestamp and level:
                            try:
                                date = tz.localize(datetime.strptime(timestamp,'%d/%m/%Y %H:%M:%S'))
                                if date < end_date:
                                    value = float(level)
                                    points.append((date,value))
                            except Exception as e:
                                logger.error(e)
                    try:
                        logger.info('Removing duplicates')
                        data = [DataPoint(series=series,date=a,value=next(b)[1]) for a,b in itertools.groupby(points, lambda y: y[0])]
                        dups = len(points)-len(data)
                        if dups:
                            logger.info('{} duplicates removed'.format(dups))
                        logger.info('Creating {} data points for well {}'.format(len(data), well))
                        series.datapoints.bulk_create(data)
                        series.update_properties()
                    except Exception as e:
                        logger.error(e)
                        
    #             span = [df.index.min(), df.index.max()]
    #             for col in df.columns:
    #                 serial, _peilbuis, name = map(lambda x: x.strip(),re.split('[:-]',col))
    #                 series = df[col]
    #                 logger.info(series.name)
    #                 try:
    #                     datalogger = Datalogger.objects.get(serial=serial)
    #                     datasource = LoggerDatasource.objects.get(logger=datalogger)
    #                     io = StringIO()
    #                     io.write('Datum\t{}\n'.format(name))
    #                     series.to_csv(io,sep='\t')
    #                     contents = io.getvalue()
    #                     crc = abs(binascii.crc32(contents))
    #                     filename = 'Export_{}_{:%Y%m%d%H%M}'.format(name,timezone.now())
    #                     sourcefile = datasource.sourcefiles.create(name=filename,user=admin,crc=crc)
    #                     sourcefile.file.save(name=filename, content=io)
    #                 except Exception as ex:
    #                     logger.error('Cannot create sourcefile for logger {}: {}'.format(serial,ex))
    #                 
    #                 # find out where logger is
    #                 # we could use the name from the header, but this is not equal to the id of the screen in the database
    #                 query = LoggerPos.objects.filter(logger=datalogger)
    #                 pos = None
    #                 if query.count() == 1:
    #                     pos = query.first()
    #                 else:
    #                     # TODO: klopt niet, de if-else hieronder
    #                     query1 = query.filter(start_date__range=span)
    #                     if query1.count == 1:
    #                         pos = query1.first()
    #                     else:
    #                         query2 = query.filter(end_date__range=span)
    #                         if query2.count == 1:
    #                             pos = query2.first()
    #                 if pos is None:
    #                     logger.error('Cannot find installation for logger {}'.format(serial))
    #                     continue
    #                 screens.add(pos.screen)
    # 
    #         logger.info('Import completed')
    #         if len(screens) > 0:
    #             wells = set()
    #             logger.info('Updating time series')
    #             for screen in screens:
    #                 series = screen.find_series()
    #                 if series:
    #                     series.replace()
    #                     wells.add(screen)
    #             if len(wells)>0:
    #                 logger.info('Updating well charts')
    #                 make_wellcharts(None,None,wells)
