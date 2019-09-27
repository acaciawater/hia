# -*- coding: utf-8 -*-
'''
Created on Sep 27, 2019

@author: theo
'''

import re 
import logging
import pandas as pd

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from acacia.meetnet.models import Datalogger, LoggerDatasource, LoggerPos
from StringIO import StringIO
from django.utils import timezone
import binascii
from acacia.meetnet.actions import make_wellcharts

logger = logging.getLogger(__name__)
    
class Command(BaseCommand):
    help = 'Import Ellitrack cluster dump'
    
    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        files = options['files']
        admin = User.objects.get(username='theo')
        screens = set()
        for fname in files:
            logger.info('Importing data from {}'.format(fname))
            df = pd.read_csv(fname,sep='\t',index_col='Datum',parse_dates=True)
            span = [df.index.min(), df.index.max()]
            for col in df.columns:
                serial, _peilbuis, name = map(lambda x: x.strip(),re.split('[:-]',col))
                series = df[col]
                logger.info(series.name)
                try:
                    datalogger = Datalogger.objects.get(serial=serial)
                    datasource = LoggerDatasource.objects.get(logger=datalogger)
                    io = StringIO()
                    io.write('Datum\t{}\n'.format(name))
                    series.to_csv(io,sep='\t')
                    contents = io.getvalue()
                    crc = abs(binascii.crc32(contents))
                    filename = 'Export_{}_{:%Y%m%d%H%M}'.format(name,timezone.now())
                    sourcefile = datasource.sourcefiles.create(name=filename,user=admin,crc=crc)
                    sourcefile.file.save(name=filename, content=io)
                except Exception as ex:
                    logger.error('Cannot create sourcefile for logger {}: {}'.format(serial,ex))
                
                # find out where logger is
                # we could use the name from the header, but this is not equal to the id of the screen in the database
                query = LoggerPos.objects.filter(logger=datalogger)
                pos = None
                if query.count() == 1:
                    pos = query.first()
                else:
                    query = query.filter(start_date__range=span)
                    if query.count == 1:
                        pos = query.first()
                    else:
                        query = query.filter(end_date__range=span)
                        if query.count == 1:
                            pos = query.first()
                if pos is None:
                    logger.error('Cannot find installation for logger {}'.format(serial))
                    continue
                screens.add(pos.screen)
                logger.info('{}->{}'.format(series.name, pos.screen))
        logger.info('Import completed')
        if len(screens) > 0:
            wells = set()
            logger.debug('Updating time series')
            for screen in screens:
                series = screen.find_series()
                if series:
                    series.replace()
                    wells.add(screen)
            if len(wells)>0:
                logger.info('Updating well charts')
                make_wellcharts(None,None,wells)
