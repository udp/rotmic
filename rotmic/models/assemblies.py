## Rotten Microbes (rotmic) -- Laboratory Sequence and Sample Management
## Copyright 2013 - 2014 Raik Gruenberg

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

from datetime import datetime

from django.db import models
from django.utils.safestring import mark_safe
import django.utils.html as html

from .usermixin import UserMixin, ReadonlyUrlMixin
from .components import ComponentBase, DnaComponent
from .annotations import Annotation
from .projects import Project

import rotmic.templatetags.rotmicfilters as F
import rotmic.utils.inheritance as I


class AssemblyLink(Annotation):
    """Point to a particular region of a source DNA (considered hard link)"""
    ## Annotion provides: bioStart, bioEnd, strand, preceedes
    
    assembly = models.ForeignKey('DnaAssembly', verbose_name='target assembly',
                                 null=False, blank=False, 
                                 related_name='partLinks')

    component = models.ForeignKey(DnaComponent, blank=True, null=True,
                                  verbose_name='source construct',
                               help_text='existing source DNA construct if any',
                               related_name='assemblyLinks')
    
    sequence = models.TextField(verbose_name='or specify sequence', 
                                help_text='or specify new nucleotide sequence', 
                                blank=True )
    
    position = models.SmallIntegerField()
    
    def __unicode__(self):
        r = u'%(id)s #%(pos)i: %(component)s[%(start)i : %(end)i]'
        d = dict(id=self.assembly.displayId, pos=0, 
                 component=self.component.__unicode__() if self.component else 'synthesis',
                 start=self.bioStart or 0,
                 end=self.bioEnd or -1)
        return r % d
    
    class Meta:
        app_label = 'rotmic'
        abstract = False
        verbose_name = 'Assembly Link'
        ordering = ['assembly', 'position']
        

class DnaAssembly(ReadonlyUrlMixin, ComponentBase):
    """Capture information for a DNA assembly design"""
    
    METHOD_CHOICES = ( ('gibson', 'Gibson assembly'),
                       ('golden', 'Golden Gate'),
                       ('classic', 'restriction/ligation'),
                       ('other', 'other') )
    
    method = models.CharField( max_length=30, choices=METHOD_CHOICES, 
                               default='gibson')
    
    preparedAt = models.DateField(default=datetime.now().date(), verbose_name="Prepared")
    
    STATUS_CHOICES = ( ('design', 'design'),
                       ('ordered', 'ordered'),
                       ('assembly', 'assembly'),
                       ('screening','screening'),
                       ('sequencing', 'sequencing'),
                       ('completed', 'completed'),
                       ('cancelled', 'cancelled'))

    status = models.CharField( max_length=30, choices=STATUS_CHOICES, 
                               default='design')
    
    def showStatus(self):
        color = {u'completed': '088A08', # green
                 u'design': '808080', # grey
                 u'ordered' : '0000FF', # blue
                 u'assembly' : '0000FF', # blue
                 u'screening' : '0000FF', # blue
                 u'sequencing' : '0000FF', # blue
                 u'cancelled': 'B40404', # red
                 }
        r = '<span style="color: #%s;">%s</span>' %\
               (color.get(self.status, '000000'), self.get_status_display())
        return html.mark_safe(r)
    showStatus.allow_tags = True
    showStatus.short_description = 'Status'
    
    
##    reactions = models.ManyToManyField(DnaReaction)
    
    class Meta:
        app_label = 'rotmic'
        abstract = False
        verbose_name = 'DNA Assembly'
        verbose_name_plural = 'DNA Assemblies'


class AssemblyProject(Project):

    STATUS_CHOICES = ( ('design', 'design'),
                       ('in progress', 'progress'),
                       ('completed', 'completed'),
                       ('cancelled', 'cancelled'))

    status = models.CharField( max_length=30, choices=STATUS_CHOICES, 
                               default='design')

    assemblies = models.ManyToManyField(DnaAssembly, blank=True, null=True,
                                        related_name='assemblyProjects')
    
    

##class DnaReaction(models.Model):
##    """
##    capture information for experimental preparation of a DNA fragment,
##    typically by PCR.
##    """
##    METHOD_CHOICES = ( ('PCR', 'PCR'),
##                       ('digest', 'restriction digest'),
##                       ('synthesis', 'gene synthesis'),
##                       ('other', 'other') )
##    
##    method = models.CharField( max_length=30, choices=METHOD_CHOICES, 
##                               default='PCR')
##    // or PartLink?
##    template = models.ForeignKey(DnaComponent, blank=True, null=True)
##    
##    product = models.ForeignKey(DnaComponent, blank=True, null=True)
##    
##    primer1 = models.ForeignKey(OligoComponent, blank=True, null=True)
##    primer2 = models.ForeignKey(OligoComponent, blank=True, null=True)
##    
##    flankLeft = models.CharField(max_length=100, blank=True)
##    flankRight = models.CharField(max_length=100, blank=True)
##
##    tm3 = models.FloatField(verbose_name="Tm3'")
##    tm  = models.FloatField(verbose_name='Tm full')
##    
##    overhangLeft = models.IntegerField()
##    overhangRight = models.IntegerField()
##    
##    class Meta:
##        app_label = 'rotmic'
##        abstract = False
##

