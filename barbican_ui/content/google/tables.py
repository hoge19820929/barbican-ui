from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import exceptions
from horizon import tables

from . import api

class SecretsFilterAction(tables.FilterAction):
    filter_type = 'query'
    filter_choices = (('name', _('Key Name ='), True, _('Case-sensitive')),
                      ('key_id', _('Key ID ='), True),
                      ('key_version_count', _('Key Version Count ='), True),
                      ('key_ring_id', _('Key Ring ID ='), True),
                      ('key_status', _('Key Status ='), True),
                      ('time_created', _('Created At ='), True),
                      ('origin_key_id', _('Origin Key ID ='), True))

class RotateSecret(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            u"Rotate Key",
            u"Rotate Keys",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Rotate Key",
            u"Rotate Keys",
            count
        )
    
    name = "rotate"
    verbose_name = _("Rotate Key")
    icon = "cloud-upload"

    def action(self, request, obj_id):
        try:
            conf_name = obj_id.split(',')[0]
            key_id = obj_id.split(',')[1]
            api.rotate_key(request.user.project_name, conf_name, key_id)
        except Exception:
            exceptions.handle(request, _("Unable to rotate key."))

class AutoRotateSecret(tables.LinkAction):
    name = "auto_rotate"
    verbose_name = _("Auto Rotate Key")
    url = "horizon:kms:google:auto_rotate"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        conf_name = datum.id.split(',')[0]
        params = urlencode({
            "conf_name": conf_name,
            "key_id": datum.key_id,
        })

        return "?".join([base_url, params])

class SetGoogleConnection(tables.LinkAction):
    name = "set_connection"
    verbose_name = _("Set Google Connection")
    url = "horizon:kms:google:set_connection"
    classes = ("ajax-modal",)
    icon = "plus"

class DeleteSecret(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            u"Delete Key Version",
            u"Delete Key Versions",
            count
        )
    
    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Deleted Key Version",
            u"Deleted Key Versions",
            count
        )
    
    def delete(self, request, obj_id):
        try:
            conf_name = obj_id.split(',')[0]
            key_id = obj_id.split(',')[1]
            api.delete_key_versions(request, conf_name, key_id)
        except Exception:
            exceptions.handle(request, _("Unable to delete key versions."))

class SecretsTable(tables.DataTable):

    name = tables.Column('name', verbose_name=_("Name"))
    key_id = tables.Column('key_id', verbose_name=_("Key ID"))
    key_version_count = tables.Column('key_version_count', verbose_name=_("Key Version Count"))
    key_ring_id = tables.Column('key_ring_id', verbose_name=_("Key Ring ID"))
    key_status = tables.Column('key_status', verbose_name=_("Key Status"))
    time_created = tables.Column('time_created', verbose_name=_("Created At"))
    origin_key_id = tables.Column('origin_key_id', verbose_name=_("Origin Key ID"))

    class Meta(object):
        name = "google"
        verbose_name = _("Google")
        table_actions = (SecretsFilterAction, SetGoogleConnection, DeleteSecret,)
        row_actions = (AutoRotateSecret, RotateSecret,)