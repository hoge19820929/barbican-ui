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
                'aws_conn',
                forms.CharField(
                    widget=forms.HiddenInput(),
                    initial=self.request.GET.get('aws_conn', ''),
                )
            ),
            (
                'name',
                forms.CharField(
                    label=_('Alias'),
                    widget=forms.TextInput(attrs={'readonly': 'readonly'}),
                    initial=self.request.GET.get('alias', ''),
                )
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
            api.auto_rotate_key(request, data['aws_conn'], request.user.project_name, data['name'], 'alias/' + data['name'], data['pattern'])
            messages.success(request, _("Successfully set auto rotation: %s") % data['name'])
            return True
        except Exception:
            exceptions.handle(request)
            return False

class SetCredentialForm(forms.SelfHandlingForm):
    aws_conn = forms.CharField(
        max_length=255,
        label=_('AWS Connection Name (to identify the connection destination)'),
    )

    key_id = forms.CharField(
        max_length=255,
        label=_('AWS Access Key ID'),
    )

    aws_secret = forms.CharField(
        max_length=255,
        label=_('AWS Secret Access Key'),
    )

    region = forms.CharField(
        max_length=255,
        label=_('Region'),
    )

    def handle(self, request, data):
        try:
            api.set_access_key(request, data['aws_conn'], data['key_id'], data['aws_secret'], data['region'])
            messages.success(request, _("Successfully set AWS connection: %s") % data['aws_conn'])
            return True
        except Exception:
            exceptions.handle(request)
            return False
