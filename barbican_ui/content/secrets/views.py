from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from . import api as project_api
from . import forms as project_forms
from . import tables as project_tables

class IndexView(tables.PagedTableMixin, tables.DataTableView):
    table_class = project_tables.SecretsTable
    page_title = _("Barbican")
    template_name = 'project/secrets/index.html'

    def get_data(self):
        try:
            search_opts = self.get_filters()
            secrets = project_api.get_secrets(self.request, **search_opts)

            return secrets
        except Exception as e:
            exceptions.handle(self.request, _("Unable to retrieve secrets."))
            return []

class CreateSecretView(forms.ModalFormView):
    template_name = 'project/secrets/create.html'
    form_id = "create_secret"
    form_class = project_forms.CreateSecretForm
    submit_label = _("Create")
    submit_url = reverse_lazy("horizon:project:secrets:create")
    success_url = reverse_lazy('horizon:project:secrets:index')
    page_title = _("Create Secret")

class SendSecretOracleView(forms.ModalFormView):
    template_name = 'project/secrets/send_key_oracle.html'
    form_id = "send_key_oracle"
    form_class = project_forms.SendSecretOracleForm
    submit_label = _("Send")
    submit_url = reverse_lazy("horizon:project:secrets:send_key_oracle")
    success_url = reverse_lazy('horizon:project:secrets:index')
    page_title = _("Send Key(Oracle)")

class SendSecretAzureView(forms.ModalFormView):
    template_name = 'project/secrets/send_key_azure.html'
    form_id = "send_key_azure"
    form_class = project_forms.SendSecretAzureForm
    submit_label = _("Send")
    submit_url = reverse_lazy("horizon:project:secrets:send_key_azure")
    success_url = reverse_lazy('horizon:project:secrets:index')
    page_title = _("Send Key(Azure)")

class SendSecretGoogleView(forms.ModalFormView):
    template_name = 'project/secrets/send_key_google.html'
    form_id = "send_key_google"
    form_class = project_forms.SendSecretGoogleForm
    submit_label = _("Send")
    submit_url = reverse_lazy("horizon:project:secrets:send_key_google")
    success_url = reverse_lazy('horizon:project:secrets:index')
    page_title = _("Send Key(Google)")
