from django.contrib import admin
import django.contrib.admin.widgets as widgets
import django.utils.html as html
from django.utils.safestring import mark_safe

import reversion

import datetime

from rotmic.models import DnaComponent, DnaComponentType, ComponentAttachment, \
     CellComponent, CellComponentType, Unit, Sample

from rotmic.utils.customadmin import ViewFirstModelAdmin, ComponentModelAdmin
from rotmic.utils.adminFilters import DnaCategoryListFilter, DnaTypeListFilter,\
     CellCategoryListFilter, CellTypeListFilter

from rotmic.forms import DnaComponentForm, CellComponentForm, AttachmentForm

import rotmic.initialTypes as T
import rotmic.templatetags.rotmicfilters as F


class BaseAdminMixin:
    """
    Automatically save and assign house-keeping information like by whom and
    when a record was saved.
    """

    def save_model(self, request, obj, form, change):
        """Override to save user who created this record"""
        ## do if new object or if object is being recovered by reversion
        if not change or '/recover/' in request.META['HTTP_REFERER']:
            obj.registeredBy = request.user
            obj.registeredAt = datetime.datetime.now()
            
        if change and form.has_changed():
            obj.modifiedBy = request.user
            obj.modifiedAt = datetime.datetime.now()

        obj.save()


class AttachmentInline(admin.TabularInline):
    model = ComponentAttachment
    form = AttachmentForm
    template = 'admin/rotmic/componentattachment/tabular.html'
    can_delete=True
    extra = 1
    max_num = 5


class DnaComponentAdmin( BaseAdminMixin, reversion.VersionAdmin, ViewFirstModelAdmin ):
    """Admin interface description for DNA constructs."""
    inlines = [ AttachmentInline ]
    form = DnaComponentForm
    
    fieldsets = (
        (None, {
            'fields': (('displayId', 'name','status'),
                       ('componentCategory', 'componentType'),
                       ('insert', 'vectorBackbone','marker' ),
                       )
        }
         ),
        ('Details', {
            'fields' : (('comment',),
                        ('sequence', 'genbankFile'),
                        )
        }
         ),            
    )

    list_display = ('displayId', 'name', 'registrationDate', 'registeredBy',
                    'showInsertUrl', 'showVectorUrl', 'showMarkerUrls', 'showComment','status')
    
    list_filter = ( DnaCategoryListFilter, DnaTypeListFilter, 'status','registeredBy')
    
    search_fields = ('displayId', 'name', 'comment', 
                     'insert__name', 'insert__displayId',
                     'vectorBackbone__name', 'vectorBackbone__displayId')
    
    date_hierarchy = 'registeredAt'
    
    ordering = ('displayId', 'name',)
    
 
    def save_model(self, request, obj, form, change):
        """Extract uploaded genbank file from request"""
        if request.FILES and 'genbankFile' in request.FILES:
            obj.genbank = ''.join(request.FILES['genbankFile'].readlines())
        super(DnaComponentAdmin, self).save_model( request, obj, form, change)
 
        
    def get_form(self, request, obj=None, **kwargs):
        """
        Override queryset of ForeignKey fields without overriding the field itself.
        This preserves the "+" Button which is otherwise lost.
        See http://djangosnippets.org/snippets/1558/#c4674
        """
        form = super(DnaComponentAdmin,self).get_form(request, obj,**kwargs)

        field = form.base_fields['marker']
        field.queryset = field.queryset.filter(componentType__subTypeOf=T.dcMarker)
        field.help_text = 'select multiple with Control/Command key'
        
        field = form.base_fields['vectorBackbone']
        field.empty_label = '---specifiy vector---'
            
        return form

    def showInsertUrl(self, obj):
        """Table display of linked insert or ''"""
        assert isinstance(obj, DnaComponent), 'object missmatch'
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
        assert isinstance(obj, DnaComponent), 'object missmatch'
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
        assert isinstance(obj, DnaComponent), 'object missmatch'
        urls = []
        for m in obj.allMarkers():
            u = m.get_absolute_url()
            urls += [ html.mark_safe('<a href="%s" title="%s">%s</a>' \
                                % (u, m.comment, m.name))]
        return ', '.join(urls)
    
    showMarkerUrls.allow_tags = True
    showMarkerUrls.short_description = 'Markers'

##
##
##        category = obj.componentType.category()
##        v = obj if category == T.dcVectorBB else obj.vectorBackbone
##        r = u''
##        if v:
##            markers = [ m.name for m in v.marker.all() ]
##            r += ', '.join(markers)
##        return r
    showMarkerUrls.allow_tags = True
    showMarkerUrls.short_description = 'Markers'
    
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
    

admin.site.register(DnaComponent, DnaComponentAdmin)


class CellComponentAdmin( BaseAdminMixin, reversion.VersionAdmin, ComponentModelAdmin ):
    """Admin interface description for DNA constructs."""
    inlines = [ AttachmentInline ]
    form = CellComponentForm
    
    fieldsets = (
        (None, {
            'fields': (('displayId', 'name','status'),
                       ('componentCategory', 'componentType'),
                       ('plasmid', 'marker'),
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
                    'showPlasmidUrl', 'showMarkerUrls', 'showComment','status')
    
    list_filter = ( CellCategoryListFilter, CellTypeListFilter, 'status','registeredBy')
    
    search_fields = ('displayId', 'name', 'comment')
    
    date_hierarchy = 'registeredAt'
    
    ordering = ('displayId', 'name',)
    

    def get_form(self, request, obj=None, **kwargs):
        """
        Override queryset of ForeignKey fields without overriding the field itself.
        This preserves the "+" Button which is otherwise lost.
        See http://djangosnippets.org/snippets/1558/#c4674
        """
        form = super(CellComponentAdmin,self).get_form(request, obj,**kwargs)
        
        field = form.base_fields['marker']
        field.queryset = field.queryset.filter(componentType__subTypeOf=T.dcMarker)
        field.help_text = ''
    
        return form
    
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
    
    def showPlasmidUrl(self, obj):
        """Table display of linked insert or ''"""
        assert isinstance(obj, CellComponent), 'object missmatch'
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
        assert isinstance(obj, CellComponent), 'object missmatch'
        urls = []
        for m in obj.allMarkers():
            u = m.get_absolute_url()
            urls += [ html.mark_safe('<a href="%s" title="%s">%s</a>' \
                                % (u, m.comment, m.name))]
        return ', '.join(urls)
    
    showMarkerUrls.allow_tags = True
    showMarkerUrls.short_description = 'Markers'

admin.site.register(CellComponent, CellComponentAdmin)


class DnaComponentTypeAdmin( reversion.VersionAdmin, admin.ModelAdmin ):
    
    fieldsets = (
        (None, {
            'fields': (('name', 'subTypeOf',),
                       ('description', 'isInsert',),
                       ('uri',),
                       )
            }
         ),
        )
    
    list_display = ('__unicode__','subTypeOf', 'description', 'isInsert')
    list_display_links = ('__unicode__',)
    list_editable = ('isInsert',)
    
    list_filter = ('subTypeOf', 'isInsert')
                       

admin.site.register(DnaComponentType, DnaComponentTypeAdmin)


class CellComponentTypeAdmin( reversion.VersionAdmin, admin.ModelAdmin ):
    
    fieldsets = (
        (None, {
            'fields': (('name', 'subTypeOf',),
                       ('description',),
                       ( 'allowPlasmids', 'allowMarkers'),
                       ('uri',),
                       )
            }
         ),
        )
    
    list_display = ('__unicode__','subTypeOf', 'description', 'allowPlasmids', 'allowMarkers')
    list_display_links = ('__unicode__',)
    list_editable = ('allowPlasmids','allowMarkers')
    
    list_filter = ('subTypeOf', 'allowPlasmids', 'allowMarkers')

admin.site.register(CellComponentType, CellComponentTypeAdmin)
    

class UnitAdmin( admin.ModelAdmin ):
    
    fieldsets = (
        (None, {
            'fields': (('name', 'unitType',),
                       ('conversion',),
                       )
            }
         ),
        )
    
    list_display = ('name','unitType', 'conversion')
    list_filter = ('unitType',)
    
admin.site.register( Unit, UnitAdmin )


class SampleAdmin( BaseAdminMixin, reversion.VersionAdmin, ViewFirstModelAdmin ):
##    form = PlasmidSampleForm     

    date_hierarchy = 'preparedAt'
    
    fieldsets = [
        (None, {
            'fields' : ((('displayId', 'status'),
                         ('preparedAt',),
                         ('concentration','concentrationUnit','amount','amountUnit',),
                         ('solvent','aliquotNr',),
                         ('comment'),
                         )
                        )
        }
        ), 
          
    ]
    list_display = ('displayId', 'preparedAt', 'registeredBy',
                    'showConcentration', 'showAmount',
                    'showComment','status','showSampleEdit')
    
    ordering = ('displayId',)

    save_as = True
    save_on_top = True

    search_fields = ('diplayId', 'name','comment')
    
    list_filter = ('status',)
    
    def showConcentration(self, o):
        conc = unicode(o.concentration or '')
        unit = unicode(o.concentrationUnit or '')
        return conc + ' '+ unit
    showConcentration.short_description = 'Concentration' 
    
    def showAmount(self, o):
        amount = unicode( o.amount or '' )
        unit   = unicode( o.amountUnit or '' )
        return amount + ' '+ unit
    showAmount.short_description = 'Amount' 
    
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

    def showSampleEdit(self, obj):
        return mark_safe('<a href="%s"><img src="http://icons.iconarchive.com/icons/custom-icon-design/office/16/edit-icon.png"/></a>'\
                         % (obj.get_absolute_url_edit() ) )
    showSampleEdit.allow_tags = True    
    showSampleEdit.short_description = 'Edit'     

admin.site.register( Sample, SampleAdmin )