import collections
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from . import api
from barbican_ui.content.oracle import api as oracle_api
from barbican_ui.content.azure import api as azure_api
from barbican_ui.content.google import api as google_api

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
            conn = api.create_connection(request)
            res = api.create_secret(conn, data['name'])
            messages.success(request, _("Successfully create secret: %s") % data['name'])
            return res
        except Exception:
            exceptions.handle(request)
            return False

class SendSecretOracleForm(forms.SelfHandlingForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = collections.OrderedDict([
            (
                'vault',
                forms.ChoiceField(
                    label=_("Vault Name / Vault ID"),
                    widget=forms.SelectWidget(),
                    choices=self.get_vault_choices()
                )
            ),
            (
                'key_id',
                forms.CharField(
                    widget=forms.HiddenInput(),
                    initial=self.request.GET.get('key_id', ''),
                )
            ),
            (
                'name',
                forms.RegexField(
                    max_length=255,
                    label=_('Key Name'),
                    initial=self.request.GET.get('name', ''),
                    help_text=_('Name of the Oracle KMS key.'),
                    regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
                    error_messages={'invalid':
                                    _('Name must start with a letter and may '
                                    'only contain letters, numbers, underscores, '
                                    'periods and hyphens.')})
            )
        ])
    
    def get_vault_choices(self):
        vault_names = oracle_api.list_vault_names()
        choices = [(name, name) for name in vault_names]

        return choices

    def handle(self, request, data):
        try:
            # data['vault']: {vault_name} / {vault_id}
            vault_id = data['vault'].split(' / ')[1]
            secret = api.get_secret(request, data['key_id'])
            oracle_api.byok_oci(vault_id, data['name'], secret)
            messages.success(request, _("Successfully send a key: %s") % data['name'])
            return True
        except Exception:
            exceptions.handle(request)
            return False

class SendSecretAzureForm(forms.SelfHandlingForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = collections.OrderedDict([
            (
                'vault',
                forms.ChoiceField(
                    label=_("Vault Name"),
                    widget=forms.SelectWidget(),
                    choices=self.get_vault_choices()
                )
            ),
            (
                'key_id',
                forms.CharField(
                    widget=forms.HiddenInput(),
                    initial=self.request.GET.get('key_id', ''),
                )
            ),
            (
                'name',
                forms.RegexField(
                    max_length=255,
                    label=_('Key Name'),
                    initial=self.request.GET.get('name', ''),
                    help_text=_('Name of the Azure KMS key.'),
                    regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
                    error_messages={'invalid':
                                    _('Name must start with a letter and may '
                                    'only contain letters, numbers, underscores, '
                                    'periods and hyphens.')})
            )
        ])
    
    def get_vault_choices(self):
        vault_names = azure_api.list_vault_names()
        choices = [(name, name) for name in vault_names]

        return choices

    def handle(self, request, data):
        try:
            azure_api.byok_azure(request.user.project_name, data['vault'], data['name'], data['key_id'])
            messages.success(request, _("Successfully send a key: %s") % data['name'])
            return True
        except Exception:
            exceptions.handle(request)
            return False

class SendSecretGoogleForm(forms.SelfHandlingForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = collections.OrderedDict([
            (
                'key_ring',
                forms.ChoiceField(
                    label=_("Key Ring Name"),
                    widget=forms.SelectWidget(),
                    choices=self.get_key_ring_choices()
                )
            ),
            (
                'key_id',
                forms.CharField(
                    widget=forms.HiddenInput(),
                    initial=self.request.GET.get('key_id', ''),
                )
            ),
            (
                'name',
                forms.RegexField(
                    max_length=255,
                    label=_('Key Name'),
                    initial=self.request.GET.get('name', ''),
                    help_text=_('Name of the Google KMS key.'),
                    regex=r"^[a-zA-Z][a-zA-Z0-9_.-]*$",
                    error_messages={'invalid':
                                    _('Name must start with a letter and may '
                                    'only contain letters, numbers, underscores, '
                                    'periods and hyphens.')})
            )
        ])
    
    def get_key_ring_choices(self):
        key_ring_ids = google_api.list_key_ring_ids()
        choices = [(key_ring_id, key_ring_id) for key_ring_id in key_ring_ids]

        return choices

    def handle(self, request, data):
        try:
            secret = api.get_secret(request, data['key_id'])
            google_api.byok_google(request.user.project_name, data['key_ring'], data['name'], False, secret)
            messages.success(request, _("Successfully send a key: %s") % data['name'])
            return True
        except Exception:
            exceptions.handle(request)
            return False