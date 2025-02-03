from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import exceptions
from horizon import tables

from . import api

class SecretsFilterAction(tables.FilterAction):
    filter_type = 'server'
    filter_choices = (('name', _('Secret Name ='), True, _('Case-sensitive')),
                      ('status', _('Status ='), True),
                      ('secret_id', _('Secret ID ='), True),
                      ('algorithm', _('Algorithm ='), True),
                      ('bit_length', _('Bit Length ='), True),
                      ('mode', _('Mode ='), True),
                      ('created_at', _('Created At ='), True),
                      ('expires_at', _('Expires At ='), True))

class CreateSecret(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Secret")
    url = "horizon:project:secrets:create"
    classes = ("ajax-modal",)
    icon = "plus"

class DeleteSecret(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            u"Delete Secret",
            u"Delete Secrets",
            count
        )
    
    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Deleted Secret",
            u"Deleted Secrets",
            count
        )
    
    def delete(self, request, secret_id):
        try:
            api.delete_secret(request, secret_id)
        except Exception as e:
            exceptions.handle(request, _("Unable to delete secrets."))

class SecretsTable(tables.DataTable):

    name = tables.Column('name', verbose_name=_("Name"))
    status = tables.Column('status', verbose_name=_("Status"))
    secret_id = tables.Column('secret_id', verbose_name=_("Secret ID"))
    algorithm = tables.Column('algorithm', verbose_name=_("Algorithm"))
    bit_length = tables.Column('bit_length', verbose_name=_("Bit Length"))
    mode = tables.Column('mode', verbose_name=_("Mode"))
    created_at = tables.Column('created_at', verbose_name=_("Created At"))
    expires_at = tables.Column('expires_at', verbose_name=_("Expires At"))

    class Meta(object):
        name = "secrets"
        verbose_name = _("Secrets")
        table_actions = (SecretsFilterAction, CreateSecret, DeleteSecret,)