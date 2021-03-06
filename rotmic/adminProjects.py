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
"""Extension of default User admin"""

from django.contrib import admin

import reversion

from .utils.customadmin import ViewFirstModelAdmin
from .adminBase import UserRecordProtectedMixin, export_csv, UpdateManyMixin
from .forms import selectLookups as L

import models as M

class ProjectAdmin(UserRecordProtectedMixin, reversion.VersionAdmin, ViewFirstModelAdmin, UpdateManyMixin):

    permit_delete = ['registeredBy'] ## only creator or superuser can delete
    
    fieldsets = [
        (None, {
            'fields' : ((('name',),
                         ('description',)
                        )),
            'description' : 'Describe a project to bundle constructs into.',
            }
         )
        ]

    list_display = ('name', 'showComments','showDescription')
    search_fields = ('name', 'description')

    save_as = True

    actions = ['make_update']
    exclude_from_update = ['name']
    model_lookup = L.ProjectLookup

admin.site.register( M.Project, ProjectAdmin )
