
## Copyright 2013 Raik Gruenberg

## This file is part of the rotmic project (https://github.com/graik/rotmic).
## rotmic is free software: you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.

## rotmic is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
## You should have received a copy of the GNU Affero General Public
## License along with rotmic. If not, see <http://www.gnu.org/licenses/>.
"""Admin interface for Component and derrived classes"""

import StringIO

from django.contrib import admin, messages
from django.utils import safestring, html

import reversion
from Bio import SeqIO

from . import models as M
from . import forms
from . import initialTypes as I
from .templatetags import rotmicfilters as F
from .utils import adminFilters as filters
from .utils import ids
from .utils.customadmin import ViewFirstModelAdmin

from .adminBase import BaseAdminMixin

class ComponentAttachmentInline(admin.TabularInline):
    model = M.ComponentAttachment
    form = forms.AttachmentForm
    template = 'admin/rotmic/componentattachment/tabular.html'
    can_delete=True
    extra = 1
    max_num = 5

class ComponentAdmin( ViewFirstModelAdmin ):
    """
    Derived from ViewFirstModelAdmin -- Custom version of admin.ModelAdmin
    which shows a read-only View for a given object instead of the normal
    ChangeForm. The changeForm is accessed by admin/ModelName/id/edit.
    
    In addition, there is extra_context provided to the change_view:
    * dnaTypes -- all registered instances of DnaComponentType
    * cellTypes -- all CellComponentTypes
    * dnaCategories -- all "super" or base-level DnaComponentTypes
    * cellCategories -- all "super" or base-level CellComponentTypes
    
    Component-specific methods:
    * showComment -- truncated comment with html mouse-over full text for tables
    """
    
    def queryset(self, request):
        """
        Return actual sub-class instances instead of generic Component super-class
        This method builds on the custom InheritanceManager replacing Component.objects
        """
        return super(ViewFirstModelAdmin,self).queryset(request).select_subclasses()

    def change_view(self, request, object_id, form_url='', extra_context=None):
        "The 'Edit' admin view for this model."
        extra_context = extra_context or {}
        
        extra_context['dnaTypes'] = M.DnaComponentType.objects.all()
        extra_context['dnaCategories'] = M.DnaComponentType.objects.filter(subTypeOf=None)
        extra_context['cellTypes'] = M.CellComponentType.objects.all()
        extra_context['cellCategories'] = M.CellComponentType.objects.filter(subTypeOf=None)
        
        return super(ComponentAdmin, self).change_view(\
            request, object_id, form_url, extra_context=extra_context)


    def add_view(self, request, form_url='', extra_context=None):
        "The 'Add new' admin view for this model."
        extra_context = extra_context or {}
        
        extra_context['dnaTypes'] = M.DnaComponentType.objects.all()
        extra_context['dnaCategories'] = M.DnaComponentType.objects.filter(subTypeOf=None)
        extra_context['cellTypes'] = M.CellComponentType.objects.all()
        extra_context['cellCategories'] = M.CellComponentType.objects.filter(subTypeOf=None)
        
        return super(ComponentAdmin, self).add_view(\
            request, form_url, extra_context=extra_context)

    def showComment(self, obj):
        """
        @return: str; truncated comment with full comment mouse-over
        """
        if not obj.comment: 
            return u''
        if len(obj.comment) < 40:
            return unicode(obj.comment)
        r = unicode(obj.comment[:38])
        r = '<a title="%s">%s</a>' % (obj.comment, F.truncate(obj.commentText(), 40))
        return r
    showComment.allow_tags = True
    showComment.short_description = 'Description'
    
    def showEdit(self, obj):
        """Small Edit Button for a direct link to Change dialog"""
        return safestring.mark_safe('<a href="%s"><img src="http://icons.iconarchive.com/icons/custom-icon-design/office/16/edit-icon.png"/></a>'\
                         % (obj.get_absolute_url_edit() ) )
    showEdit.allow_tags = True    
    showEdit.short_description = 'Edit'     

    def showStatus(self, obj):
        color = {u'available': '088A08', # green
                 u'planning': '808080', # grey
                 u'construction' : '0000FF', # blue
                 u'abandoned': 'B40404', # red
                 }
        return '<span style="color: #%s;">%s</span>' %\
               (color.get(obj.status, '000000'), obj.statusValue())
    showStatus.allow_tags = True
    showStatus.short_description = 'Status'


class DnaComponentAdmin( BaseAdminMixin, reversion.VersionAdmin, ComponentAdmin):
    """Admin interface description for DNA constructs."""
    inlines = [ ComponentAttachmentInline ]
    form = forms.DnaComponentForm
    
    fieldsets = (
        (None, {
            'fields': (('displayId', 'name','status'),
                       ('componentCategory', 'componentType'),
                       ('insert', 'vectorBackbone','markers' ),
                       )
        }
         ),
        ('Details', {
            'fields' : (('comment',),
                        ('sequence', 'genbankFile'),
                        ),
        }
         ),            
    )

    list_display = ('displayId', 'name', 'registrationDate', 'registeredBy',
                    'showInsertUrl', 'showVectorUrl', 'showMarkerUrls', 
                    'showComment','showStatus', 'showEdit')
    
    list_filter = ( filters.DnaCategoryListFilter, filters.DnaTypeListFilter, 
                    'status',filters.SortedUserFilter)
    
    search_fields = ('displayId', 'name', 'comment', 
                     'insert__name', 'insert__displayId',
                     'vectorBackbone__name', 'vectorBackbone__displayId')
    
    date_hierarchy = 'registeredAt'
    
    ordering = ('displayId', 'name')
    
    def queryset(self, request):
        """Revert modification made by ComponentModelAdmin"""
        return super(ComponentAdmin,self).queryset(request)
 
    def save_model(self, request, obj, form, change):
        """Extract uploaded genbank file from request"""

        ## copy genbank file content as string into DB field
        if request.FILES and 'genbankFile' in request.FILES:
            try:
                obj.genbank = ''.join(request.FILES['genbankFile'].readlines())

                f = StringIO.StringIO( obj.genbank )
                seqrecord = SeqIO.parse( f, 'gb' ).next()
                obj.sequence = seqrecord.seq.tostring()
                if not obj.name:
                    obj.name = seqrecord.name
                if not obj.comment:
                    obj.comment = seqrecord.description
            except StopIteration:
                messages.error(request, 'Empty or corrupted genbank file')
            except ValueError, why:
                messages.error(request, 'Error reading genbank file: %r' % why)
        
        super(DnaComponentAdmin, self).save_model( request, obj, form, change)
 
        
    def get_form(self, request, obj=None, **kwargs):
        """
        Override queryset of ForeignKey fields without overriding the field itself.
        This preserves the "+" Button which is otherwise lost.
        See http://djangosnippets.org/snippets/1558/#c4674
        """
        form = super(DnaComponentAdmin,self).get_form(request, obj,**kwargs)

        field = form.base_fields['markers']
        field.queryset = field.queryset.filter(componentType__subTypeOf=I.dcMarker)
        field.help_text = 'select multiple with Control/Command key'
        
        field = form.base_fields['vectorBackbone']
        field.empty_label = '---specifiy vector---'
        
        ## suggest ID
        category = form.base_fields['componentCategory'].initial
        category = category.name[0].lower()
        prefix = request.user.profile.dcPrefix or request.user.profile.prefix
        prefix += category
        
        field = form.base_fields['displayId']
        field.initial = ids.suggestDnaId(request.user.id, prefix=prefix)
            
        return form

    def showInsertUrl(self, obj):
        """Table display of linked insert or ''"""
        assert isinstance(obj, M.DnaComponent), 'object missmatch'
        x = obj.insert
        if not x:
            return u''
        url = x.get_absolute_url()
        return html.mark_safe('<a href="%s" title="%s">%s</a>- %s' \
                              % (url, x.comment, x.displayId, x.name))
    showInsertUrl.allow_tags = True
    showInsertUrl.short_description = 'Insert'
        
    def showVectorUrl(self, obj):
        """Table display of linked insert or ''"""
        assert isinstance(obj, M.DnaComponent), 'object missmatch'
        x = obj.vectorBackbone
        if not x:
            return u''
        url = x.get_absolute_url()
        return html.mark_safe('<a href="%s" title="%s">%s</a>- %s' \
                              % (url, x.comment, x.displayId, x.name))
    showVectorUrl.allow_tags = True
    showVectorUrl.short_description = 'Vector'
    
    def showMarkerUrls(self, obj):
        """Table display of Vector Backbone markers"""
        assert isinstance(obj, M.DnaComponent), 'object missmatch'
        urls = []
        for m in obj.allMarkers():
            u = m.get_absolute_url()
            urls += [ html.mark_safe('<a href="%s" title="%s">%s</a>' \
                                % (u, m.comment, m.name))]
        return ', '.join(urls)
    
    showMarkerUrls.allow_tags = True
    showMarkerUrls.short_description = 'Markers'

admin.site.register(M.DnaComponent, DnaComponentAdmin)


class CellComponentAdmin( BaseAdminMixin, reversion.VersionAdmin, ComponentAdmin ):
    """Admin interface description for DNA constructs."""
    inlines = [ ComponentAttachmentInline ]
    form = forms.CellComponentForm
    
    fieldsets = (
        (None, {
            'fields': (('displayId', 'name','status'),
                       ('componentCategory', 'componentType'),
                       ('plasmid', 'markers'),
                       )
        }
         ),
        ('Details', {
            'fields' : (('comment',),
                        )
        }
         ),            
    )

    list_display = ('displayId', 'name', 'registrationDate', 'registeredBy',
                    'showPlasmidUrl', 'showMarkerUrls', 'showComment','showStatus',
                    'showEdit')
    
    list_filter = ( filters.CellCategoryListFilter, filters.CellTypeListFilter, 
                    'status', filters.SortedUserFilter)
    
    search_fields = ('displayId', 'name', 'comment')
    
    date_hierarchy = 'registeredAt'
    
    ordering = ('displayId', 'name',)
    
    def queryset(self, request):
        """Revert modification made by ComponentModelAdmin"""
        return super(ComponentAdmin,self).queryset(request)

    def get_form(self, request, obj=None, **kwargs):
        """
        Override queryset of ForeignKey fields without overriding the field itself.
        This preserves the "+" Button which is otherwise lost.
        See http://djangosnippets.org/snippets/1558/#c4674
        """
        form = super(CellComponentAdmin,self).get_form(request, obj,**kwargs)
        
        field = form.base_fields['markers']
        field.queryset = field.queryset.filter(componentType__subTypeOf=I.dcMarker)
        field.help_text = ''
        return form
    
    def showPlasmidUrl(self, obj):
        """Table display of linked insert or ''"""
        assert isinstance(obj, M.CellComponent), 'object missmatch'
        x = obj.plasmid
        if not x:
            return u''
        url = x.get_absolute_url()
        return html.mark_safe('<a href="%s" title="%s">%s</a>- %s' \
                              % (url, x.comment, x.displayId, x.name))
    showPlasmidUrl.allow_tags = True
    showPlasmidUrl.short_description = 'Plasmid'
    
    def showMarkerUrls(self, obj):
        """Table display of Vector Backbone markers"""
        assert isinstance(obj, M.CellComponent), 'object missmatch'
        urls = []
        for m in obj.allMarkers():
            u = m.get_absolute_url()
            urls += [ html.mark_safe('<a href="%s" title="%s">%s</a>' \
                                % (u, m.comment, m.name))]
        return ', '.join(urls)    
    showMarkerUrls.allow_tags = True
    showMarkerUrls.short_description = 'Markers'

admin.site.register(M.CellComponent, CellComponentAdmin)


class OligoComponentAdmin( BaseAdminMixin, reversion.VersionAdmin, ComponentAdmin ):
    """Admin interface description for DNA constructs."""
    inlines = [ ComponentAttachmentInline ]
    form = forms.OligoComponentForm
    
    fieldsets = (
        (None, {
            'fields': (('displayId', 'name','status'),
                       ('componentType',),
                       )
        }
         ),
        ('Details', {
            'fields' : (('sequence',),('meltingTemp', 'templates'),('comment',),
                        )
        }
         ),            
    )

    list_display = ('displayId', 'name', 'registrationDate', 'registeredBy',
                    'componentType', 'showTm', 'showComment','showStatus','showEdit')
    
    list_filter = ( 'componentType', 'status', filters.SortedUserFilter)
    
    search_fields = ('displayId', 'name', 'comment')
    
    date_hierarchy = 'registeredAt'
    
    ordering = ('displayId', 'name',)
    
    def queryset(self, request):
        """Revert modification made by ComponentModelAdmin"""
        return super(ComponentAdmin,self).queryset(request)

    def showTm(self, obj):
        if obj.meltingTemp:
            return u'%02i\u00B0C' % obj.meltingTemp
        return ''
    showTm.allow_tags = True
    showTm.short_description = 'Tm'
    
    
admin.site.register(M.OligoComponent, OligoComponentAdmin)


class ChemicalComponentAdmin( BaseAdminMixin, reversion.VersionAdmin, ComponentAdmin ):
    """Admin interface description for DNA constructs."""
    inlines = [ ComponentAttachmentInline ]
    form = forms.ChemicalComponentForm
    
    fieldsets = (
        (None, {
            'fields': (('displayId', 'name','status'),
                       ('componentCategory', 'componentType'),
                       )
        }
         ),
        ('Details', {
            'fields' : (('cas','comment',),
                        )
        }
         ),            
    )

    list_display = ('displayId', 'name', 'registrationDate', 'registeredBy',
                    'cas', 'showComment','showStatus',
                    'showEdit')
    
    list_filter = ( filters.ChemicalCategoryListFilter, filters.ChemicalTypeListFilter, 
                    'status', filters.SortedUserFilter)
    
    search_fields = ('displayId', 'name', 'comment', 'cas')
    
    date_hierarchy = 'registeredAt'
    
    ordering = ('displayId', 'name',)
    
    def queryset(self, request):
        """Revert modification made by ComponentModelAdmin"""
        return super(ComponentAdmin,self).queryset(request)


admin.site.register(M.ChemicalComponent, ChemicalComponentAdmin)


