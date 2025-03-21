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
    page_title = _("Azure Key Vault")
    template_name = 'project/google/index.html'

    def get_data(self):
        try:
            search_opts = self.get_filters()
            secrets = project_api.get_key_data(**search_opts)

            return secrets
        except Exception:
            exceptions.handle(self.request, _("Unable to retrieve secrets."))
            return []

class AutoRotateSecretView(forms.ModalFormView):
    template_name = 'project/google/auto_rotate.html'
    form_id = "auto_rotate_google"
    form_class = project_forms.AutoRotateSecretForm
    submit_label = _("Submit")
    submit_url = reverse_lazy("horizon:project:google:auto_rotate")
    success_url = reverse_lazy('horizon:project:google:index')
    page_title = _("Auto Rotate Secret")
