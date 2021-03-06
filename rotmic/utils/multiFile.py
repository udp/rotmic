## code taken from: http://koensblog.eu/blog/7/multiple-file-upload-django

from django.utils.translation import ugettext_lazy as _
from django import forms
 

class MultiFileInput(forms.FileInput):

    def render(self, name, value, attrs={}):
        attrs['multiple'] = 'multiple'
        return super(MultiFileInput, self).render(name, None, attrs=attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        else:
            return [files.get(name)]
 

class MultiFileField(forms.FileField):

    widget = MultiFileInput

    default_error_messages = {
        'min_num': u"Please select at least %(min_num)s files (found %(num_files)s).",
        'max_num': u"Please select at most %(max_num)s files (found %(num_files)s).",
        'file_size' : u"File: %(uploaded_file_name)s, exceeded maximum upload size."
    }

    def __init__(self, *args, **kwargs):
        self.min_num = kwargs.pop('min_num', 0)
        self.max_num = kwargs.pop('max_num', None)
        self.max_size = kwargs.pop('max_size', None)
        self.extensions = kwargs.pop( 'extensions', [] )
        super(MultiFileField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        ret = []
        for item in data:
            ret.append(super(MultiFileField, self).to_python(item))
        return ret

    def validate(self, data):
        super(MultiFileField, self).validate(data)
        num_files = len(data)
        if len(data) and not data[0]:
            num_files = 0
            data = []

        if num_files < self.min_num:
            raise forms.ValidationError(self.error_messages['min_num'] % {'min_num': self.min_num, 'num_files': num_files})

        elif self.max_num and  num_files > self.max_num:
            raise forms.ValidationError(self.error_messages['max_num'] % {'max_num': self.max_num, 'num_files': num_files})

        for uploaded_file in data:
            if self.max_size and uploaded_file.size > self.max_size:
                raise forms.ValidationError(self.error_messages['file_size'] % { 'uploaded_file_name': uploaded_file.name})
            
        try:
            for f in data:
                ext = f.name.split('.')[-1].lower()  

                if self.extensions and not ext in self.extensions:
                    raise forms.ValidationError(
                        'Invalid file extension %s. Allowed are %r' \
                        % (ext, self.extensions),
                        code='invalid file')
        except:
            raise forms.ValidationError('Invalid file name %s' \
                                        % f.name,code='invalid file',)

