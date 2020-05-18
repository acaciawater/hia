# -*- coding: utf-8 -*-
'''
Created on Sep 27, 2019

@author: theo
'''

import re 
import logging
import csv

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
    #TODO: store source files and add datasource/generator
    def add_arguments(self, parser):
        parser.add_argument('folder', help='Folder with csv files', type=str)
        parser.add_argument('--well','-w',
                action='store',
                dest = 'well',
                default = '',
                help = 'well number')

    def handle(self, *args, **options):
        pattern = r'csv_results_\d+_(?P<nr>\d+)_.+\.csv'
        tz = pytz.timezone('Europe/Amsterdam') # TODO: check timezone!
        end_date = datetime(2019,9,18,0,0,0,0,tz)
        folder = options['folder']
        single_target = options['well']
        logger.info('Importing data from folder {}'.format(folder))
        for path, _dirs, files in os.walk(folder):
            for fname in files:
                match = re.match(pattern,fname)
                if not match:
                    logger.info('File {} skipped: no filename match.'.format(fname))
                    continue
                nr = int(match.group('nr'))
                name = '{:03}'.format(nr)
                if single_target and name != single_target:
                    logger.info('File {} skipped: no match'.format(fname))
                    continue
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
                        
