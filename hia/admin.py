'''
Created on Nov 12, 2019

@author: theo
'''
from django.contrib import admin
from django.contrib.admin.decorators import register
from models import Document, Folder, Link

@register(Folder)
class FolderAdmin(admin.ModelAdmin):
    search_fields = ('name','modified')
    exclude = ('created','modified')
          
@register(Document)
class DocumentAdmin(FolderAdmin):
    list_display = ('name','file')

@register(Link)
class LinkAdmin(FolderAdmin):
    list_display = ('name','url')
