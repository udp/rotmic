from django.contrib import admin
from django.db.models.query import QuerySet as Q

import datetime

from rotmic.models import DnaComponent, DnaComponentType
from rotmic.utils.customadmin import ViewFirstModelAdmin
from rotmic.forms import DnaComponentForm
import rotmic.initialTypes as T


class BaseAdminMixin:
    """
    Automatically save and assign house-keeping information like by whom and
    when a record was saved.
    """

    def save_model(self, request, obj, form, change):
        """Override to save user who created this record"""
        if not change:
            obj.registeredBy = request.user
            obj.registeredAt = datetime.datetime.now()

        obj.save()

    def registrationDate(self, obj):
        """extract date from date+time"""
        return obj.registeredAt.date().isoformat()
    registrationDate.short_description = 'registered'
    
    def registrationTime(self, obj):
        """extract time from date+time"""
        return obj.registeredAt.time()
    registrationTime.short_description = 'at'
    

class DnaCategoryListFilter( admin.SimpleListFilter):
    """
    Provide filter for DnaComponentType.category (all root types)
    """
    title = 'Category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        categories = DnaComponentType.objects.filter(subTypeOf=None)
        return ( (c.name, c.name) for c in categories )
    

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        q = queryset
        
        if not self.value():
            return q
        
        return q.filter(componentType__subTypeOf__name=self.value())


class DnaTypeListFilter( admin.SimpleListFilter):
    """
    Provide filter for DnaComponentType.category (all root types)
    
    This filter has one cosmetic problem, which is that it's setting is not
    automatically deleted if the category filter is changed. I tried but the
    request and queryset are all immutable. Instead, the queryset method is 
    checking for any missmatch between category and filter name and filtering
    is ignored if the category name doesn't match the current subType name.
    """
    title = 'Type'
    parameter_name = 'type'
    
    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        if not u'category' in request.GET:
            return ()
        
        category_name = request.GET[u'category']
        types = DnaComponentType.objects.filter(subTypeOf__name=category_name)
        return ( (t.name, t.name) for t in types )
    
    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if not u'category' in request.GET:
            return queryset
        
        category = request.GET[u'category']
        subtypes = DnaComponentType.objects.filter(subTypeOf__name=category)
        
        r = queryset.filter(componentType__subTypeOf__name=category)
        
        if not self.value():
            return r
        
        ## special case: missmatch between subtype and category
        if len(subtypes.filter(name=self.value())) == 0:
            return r
        
        return r.filter(componentType__name=self.value())


class DnaComponentAdmin( BaseAdminMixin, ViewFirstModelAdmin ):
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
                        ('sequence'),
##                        ('attachements',)
                        )
        }
         ),            
    )

    list_display = ('displayId', 'name', 'registrationDate', 'registeredBy',
                    'insert','vectorBackbone', 'comment','status')
    
    list_filter = ( DnaCategoryListFilter, DnaTypeListFilter, 'status','registeredBy')
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Override queryset of ForeignKey fields without overriding the field itself.
        This preserves the "+" Button which is otherwise lost.
        See http://djangosnippets.org/snippets/1558/#c4674
        """
        form = super(DnaComponentAdmin,self).get_form(request, obj,**kwargs)

        field = form.base_fields['componentType']
        field.queryset = field.queryset.exclude(subTypeOf=None)
        field.initial = DnaComponentType.objects.get(name='generic plasmid').id
        
        field = form.base_fields['insert']
        field.queryset = field.queryset.filter(\
            componentType__subTypeOf=T.dcFragment,
            componentType__isInsert=True)
        field.empty_label = '---no insert---'
        
        field = form.base_fields['marker']
        field.queryset = field.queryset.filter(componentType__subTypeOf=T.dcMarker)
        ## field.widget.widget.allow_multiple_selected = True
        field.help_text = 'select multiple with Control/Command key'
        
        field = form.base_fields['vectorBackbone']
        field.queryset = field.queryset.filter(componentType__subTypeOf=T.dcVectorBB)
        field.empty_label = '---specifiy vector---'
        
        return form


class DnaComponentTypeAdmin( admin.ModelAdmin ):
    
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
                       

admin.site.register(DnaComponent, DnaComponentAdmin)
admin.site.register(DnaComponentType, DnaComponentTypeAdmin)
