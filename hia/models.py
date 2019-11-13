'''
Created on Nov 12, 2019

@author: theo
'''
from django.db import models
from django.utils.translation import ugettext_lazy as _
import os

class Folder(models.Model):
    name = models.CharField(_('name'),max_length=100)
    description = models.TextField(_('description'),blank=True,null=True)
    parent = models.ForeignKey('Folder',on_delete=models.CASCADE, verbose_name=_('folder'), blank=True,null=True)
    created = models.DateTimeField(_('created'),auto_now_add=True)
    modified = models.DateTimeField(_('modified'),auto_now=True)
    
    def __unicode__(self):
        if self.parent:
            return '{}/{}'.format(self.parent, self.name)
        else:
            return self.name
    
    class Meta:
        verbose_name=_('Folder')        
        verbose_name_plural=_('Folders')
        unique_together = ('parent', 'name')
        
class Document(Folder):
    file = models.FileField(_('file'),upload_to='documents')
    
    @property
    def icon(self):
        if self.file:
            name, ext = os.path.splitext(self.file.name)
            if ext:
                return '/static/svg/{}.svg'.format(ext[1:])
        return None

    class Meta:
        verbose_name=_('Document')        
        verbose_name_plural=_('Documents')

class Link(Folder):
    url = models.URLField(_('url'))
    
    class Meta:
        verbose_name=_('Link')        
        verbose_name_plural=_('Links')
        