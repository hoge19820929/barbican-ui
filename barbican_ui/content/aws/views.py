from operator import attrgetter

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
    page_title = _("AWS KMS")
    template_name = 'project/aws/index.html'

    def get_data(self):
        try:
            search_opts = self.get_filters()
            secrets = project_api.get_secrets(self.request, **search_opts)

            return secrets
        except Exception as e:
            exceptions.handle(self.request, _("Unable to retrieve secrets."))
            return []

class IndexAllView(tables.PagedTableMixin, tables.DataTableView):
    table_class = project_tables.SecretsTable
    page_title = _("AWS Secrets")
    template_name = 'project/aws/index.html'

    def get_data(self):
        try:
            search_opts = self.get_filters()
            secrets = project_api.get_secrets(self.request, is_all=True, **search_opts)

            return secrets
        except Exception as e:
            exceptions.handle(self.request, _("Unable to retrieve secrets."))
            return []

class AutoRotateSecretView(forms.ModalFormView):
    template_name = 'project/aws/auto_rotate.html'
    form_id = "auto_rotate"
    form_class = project_forms.AutoRotateSecretForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:project:aws:auto_rotate")
    success_url = reverse_lazy('horizon:project:aws:index')
    page_title = _("Auto Rotate Secret")

class SetCredentialsView(forms.ModalFormView):
    template_name = 'project/aws/set_cred.html'
    form_id = "set_cred"
    form_class = project_forms.SetCredentialForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:project:aws:set_cred")
    success_url = reverse_lazy('horizon:project:aws:index')
    page_title = _("Set AWS Access Key")

'''
class CreateSecretView(forms.ModalFormView):
    template_name = 'project/aws/create.html'
    form_id = "create_secret"
    form_class = project_forms.CreateSecretForm
    submit_label = _("Create")
    submit_url = reverse_lazy("horizon:project:aws:create")
    success_url = reverse_lazy('horizon:project:aws:index')
    page_title = _("Create Secret")
'''
