import collections
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from . import api

'''
class CreateSecretForm(forms.SelfHandlingForm):

    name = forms.RegexField(
        max_length=255,
        label=_('Secret Name'),
        help_text=_('Name of the secret to create.'),
        regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
        error_messages={'invalid':
                        _('Name must start with a letter and may '
                          'only contain letters, numbers, underscores, '
                          'periods and hyphens.')})

    def handle(self, request, data):
        try:
            api.byok_aws(request, data['name'], 'alias/' + data['name'])
            messages.success(request, _("Successfully create secret: %s") % data['name'])
            return True
        except Exception:
            exceptions.handle(request)
            return False
'''
            
class AutoRotateSecretForm(forms.SelfHandlingForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = collections.OrderedDict([
            (
                'name',
                forms.RegexField(
                    max_length=255,
                    label=_('Alias'),
                    initial=self.request.GET.get('alias', ''),
                    help_text=_('Name of the secret to create.'),
                    regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
                    error_messages={'invalid':
                                    _('Name must start with a letter and may '
                                    'only contain letters, numbers, underscores, '
                                    'periods and hyphens.')})
            ),
            (
                'pattern',
                forms.CharField(
                    max_length=255,
                    label=_('Cron Pattern'),
                    initial='* * * * *'
                )
            )
        ])

    def handle(self, request, data):
        try:
            api.auto_rotate_key(data['name'], 'alias/' + data['name'], data['pattern'])
            messages.success(request, _("Successfully set auto rotation: %s") % data['name'])
            return True
        except Exception:
            exceptions.handle(request)
            return False
