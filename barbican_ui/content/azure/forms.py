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
                'conf_name',
                forms.CharField(
                    widget=forms.HiddenInput(),
                    initial=self.request.GET.get('conf_name', ''),
                )
            ),
            (
                'key_id',
                forms.CharField(
                    label=_('Key ID'),
                    widget=forms.TextInput(attrs={'readonly': 'readonly'}),
                    initial=self.request.GET.get('key_id', '')
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
            api.auto_rotate_key(request.user.project_name, data['conf_name'], data['key_id'], data['pattern'])
            messages.success(request, _("Successfully set auto rotation: %s") % data['key_id'])
            return True
        except Exception:
            exceptions.handle(request)
            return False

class SetConnectionForm(forms.SelfHandlingForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = collections.OrderedDict([
            (
                'azure_conn',
                forms.CharField(
                    max_length=255,
                    label=_('Azure Connection Name (to identify the connection destination)'),
                )
            ),
            (
                'client_id',
                forms.CharField(
                    max_length=255,
                    label=_('Client ID'),
                )
            ),
            (
                'tenant_id',
                forms.CharField(
                    max_length=255,
                    label=_('Tenant ID'),
                )
            ),
            (
                'client_secret',
                forms.CharField(
                    max_length=255,
                    label=_('Crient Secret'),
                )
            ),
            (
                'subscription_id',
                forms.CharField(
                    max_length=255,
                    label=_('Subscription ID'),
                )
            ),
            (
                'key_vault',
                forms.CharField(
                    max_length=255,
                    label=_('Key Vault Name'),
                )
            )
        ])

    def handle(self, request, data):
        try:
            api.set_connection(request, data['azure_conn'], data['client_id'], data['tenant_id'], data['client_secret'], data['subscription_id'], data['key_vault'])
            messages.success(request, _("Successfully set Azure connection: %s") % data['azure_conn'])
            return True
        except Exception:
            exceptions.handle(request)
            return False