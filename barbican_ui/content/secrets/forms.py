import collections
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from . import api
from barbican_ui.content.oracle import api as oracle_api

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
                    label=_("Vault Name"),
                    widget=forms.SelectWidget(),
                    choices=self.get_vault_choices()
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
            oracle_api.byok_oci(data['vault'], data['name'], False)
            messages.success(request, _("Successfully send a key: %s") % data['name'])
            return True
        except Exception:
            exceptions.handle(request)
            return False
