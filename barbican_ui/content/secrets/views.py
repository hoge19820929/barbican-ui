from urllib.parse import urlencode
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
    page_title = _("RKMS")
    template_name = 'kms/secrets/index.html'

    def get_data(self):
        try:
            search_opts = self.get_filters()
            secrets = project_api.get_key_data(self.request, **search_opts)

            return secrets
        except Exception as e:
            exceptions.handle(self.request, _("Unable to retrieve secrets."))
            return []

class CreateSecretView(forms.ModalFormView):
    template_name = 'kms/secrets/create.html'
    form_id = "create_secret"
    form_class = project_forms.CreateSecretForm
    submit_label = _("Create")
    submit_url = reverse_lazy("horizon:kms:secrets:create")
    success_url = reverse_lazy('horizon:kms:secrets:index')
    page_title = _("Create Secret")

class AutoRotateSecretView(forms.ModalFormView):
    template_name = 'kms/secrets/auto_rotate.html'
    form_id = "auto_rotate"
    form_class = project_forms.AutoRotateSecretForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:kms:secrets:auto_rotate")
    success_url = reverse_lazy('horizon:kms:secrets:index')
    page_title = _("Auto Rotate Secret")

class SendSecretAWSView(forms.ModalFormView):
    template_name = 'kms/secrets/send_key_aws.html'
    form_id = "send_key_aws"
    form_class = project_forms.SendSecretAWSForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:kms:secrets:send_key_aws")
    success_url = reverse_lazy('horizon:kms:secrets:index')
    page_title = _("Send Key(AWS)")

class SendSecretOracleView(forms.ModalFormView):
    template_name = 'kms/secrets/send_key_oracle.html'
    form_id = "send_key_oracle"
    form_class = project_forms.SendSecretOracleForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:kms:secrets:send_key_oracle")
    success_url = reverse_lazy('horizon:kms:secrets:index')
    page_title = _("Send Key(Oracle)")

class SendSecretAzureView(forms.ModalFormView):
    template_name = 'kms/secrets/send_key_azure.html'
    form_id = "send_key_azure"
    form_class = project_forms.SendSecretAzureForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:kms:secrets:send_key_azure")
    success_url = reverse_lazy('horizon:kms:secrets:index')
    page_title = _("Send Key(Azure)")

class SelectGoogleConnectionView(forms.ModalFormView):
    template_name = 'kms/secrets/select_google_connection.html'
    form_id = "select_google_connection"
    form_class = project_forms.SelectGoogleConnectionForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:kms:secrets:select_google_connection")
    success_url = reverse_lazy('horizon:kms:secrets:send_key_google')
    page_title = _("Select Google Connection")

    def form_valid(self, form):
        conn_name = form.cleaned_data.get('conn_name')
        key_id = form.cleaned_data.get('key_id')
        name = form.cleaned_data.get('name')

        query_string = urlencode({
            'conn_name': conn_name,
            'key_id': key_id,
            'name': name,
        })
        self.success_url = f"{self.success_url}?{query_string}"

        return super().form_valid(form)

class SendSecretGoogleView(forms.ModalFormView):
    template_name = 'kms/secrets/send_key_google.html'
    form_id = "send_key_google"
    form_class = project_forms.SendSecretGoogleForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:kms:secrets:send_key_google")
    success_url = reverse_lazy('horizon:kms:secrets:index')
    page_title = _("Send Key(Google)")
