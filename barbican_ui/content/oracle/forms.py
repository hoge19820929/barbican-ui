import collections
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from . import api

class AutoRotateSecretForm(forms.SelfHandlingForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = collections.OrderedDict([
            (
                'key_name',
                forms.CharField(
                    label=_('Key Name'),
                    widget=forms.TextInput(attrs={'readonly': 'readonly'}),
                    initial=self.request.GET.get('key_name', ''),
                )
            ),
            (
                'vault_id',
                forms.CharField(
                    widget=forms.HiddenInput(),
                    initial=self.request.GET.get('vault_id', ''),
                )
            ),
            (
                'key_id',
                forms.CharField(
                    label=_('Key ID'),
                    widget=forms.TextInput(attrs={'readonly': 'readonly'}),
                    initial=self.request.GET.get('key_id', ''),
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
            api.auto_rotate_key(request.user.project_name, data['vault_id'], data['key_id'], data['key_name'], data['pattern'])
            messages.success(request, _("Successfully set auto rotation: %s") % data['key_name'])
            return True
        except Exception:
            exceptions.handle(request)
            return False