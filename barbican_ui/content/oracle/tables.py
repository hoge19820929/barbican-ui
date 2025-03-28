from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import exceptions
from horizon import tables

from . import api

class SecretsFilterAction(tables.FilterAction):
    filter_type = 'server'
    filter_choices = (('name', _('Key Name ='), True, _('Case-sensitive')),
                      ('key_id', _('Key ID ='), True),
                      ('key_version_count', _('Key Version Count ='), True),
                      ('vault_name', _('Vault Name ='), True),
                      ('key_state', _('Status ='), True),
                      ('time_created', _('Created At ='), True),
                      ('origin_key_id', _('Origin Key ID ='), True))

class SendSecret(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            u"Send Key(Oracle)",
            u"Send Key(Oracle)",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Send Key(Oracle)",
            u"Send Key(Oracle)",
            count
        )
    
    name = "send"
    verbose_name = _("Send Key(Oracle)")
    icon = "cloud-upload"

    def action(self, request, row_id):
        try:
            # row_id: {vault_id}/{key_id}
            vault_id = row_id.split('/')[0]
            key_id = row_id.split('/')[1]
            api.rotate_key(vault_id, key_id)
        except Exception:
            exceptions.handle(request, _("Unable to send key."))

class AutoRotateSecret(tables.LinkAction):
    name = "auto_rotate"
    verbose_name = _("Auto Rotate Key")
    url = "horizon:project:oracle:auto_rotate"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        # datum.id: {vault_id}/{key_id}
        vault_id = datum.id.split('/')[0]
        key_id = datum.id.split('/')[1]
        params = urlencode({
            "key_name": datum.name,
            "vault_id": vault_id,
            "key_id": key_id
        })

        return "?".join([base_url, params])

class DeleteSecret(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            u"Delete Key",
            u"Delete Keys",
            count
        )
    
    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Deleted Key",
            u"Deleted Keys",
            count
        )
    
    def delete(self, request, row_id):
        try:
            # row_id: {vault_id}/{key_id}
            vault_id = row_id.split('/')[0]
            key_id = row_id.split('/')[1]
            api.delete_key(vault_id, key_id)
        except Exception:
            exceptions.handle(request, _("Unable to delete keys."))

class SecretsTable(tables.DataTable):

    name = tables.Column('name', verbose_name=_("Name"))
    key_id = tables.Column('key_id', verbose_name=_("Key ID"))
    key_version_count = tables.Column('key_version_count', verbose_name=_("Key Version Count"))
    vault_name = tables.Column('vault_name', verbose_name=_("Vault Name"))
    key_state = tables.Column('key_state', verbose_name=_("Status"))
    time_created = tables.Column('time_created', verbose_name=_("Created At"))
    origin_key_id = tables.Column('origin_key_id', verbose_name=_("Origin Key ID"))

    class Meta(object):
        name = "oracle"
        verbose_name = _("Oracle")
        table_actions = (SecretsFilterAction, DeleteSecret,)
        row_actions = (AutoRotateSecret, SendSecret,)