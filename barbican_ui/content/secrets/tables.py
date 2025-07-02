from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import exceptions
from horizon import tables

from . import api

class SecretsFilterAction(tables.FilterAction):
    filter_type = 'query'
    filter_choices = (('name', _('Secret Name ='), True, _('Case-sensitive')),
                      ('key_id', _('Key ID ='), True),
                      ('key_version', _('Key Version ='), True),
                      ('container_id', _('Container ID ='), True),
                      ('key_state', _('Key State ='), True),
                      ('time_created', _('Time Created ='), True))

class CreateSecret(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Secret")
    url = "horizon:kms:secrets:create"
    classes = ("ajax-modal",)
    icon = "plus"

class RotateSecret(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            "Rotate Key",
            "Rotate Keys",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            "Rotate Key",
            "Rotate Keys",
            count
        )
    
    name = "rotate"
    verbose_name = _("Rotate Key")
    icon = "cloud-upload"

    def action(self, request, key_id):
        try:
            api.rotate_key(request.user.project_name, key_id)
        except Exception:
            exceptions.handle(request, _("Unable to rotate key."))

class AutoRotateSecret(tables.LinkAction):
    name = "auto_rotate"
    verbose_name = _("Auto Rotate Key")
    url = "horizon:kms:secrets:auto_rotate"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"key_id": datum.key_id, "name": datum.name})

        return "?".join([base_url, params])

class SendAWSKey(tables.LinkAction):
    name = "send-aws"
    verbose_name = _("Send Key(AWS)")
    url = "horizon:kms:secrets:send_key_aws"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"name": datum.name, "key_id": datum.key_id})

        return "?".join([base_url, params])

class SendOracleKey(tables.LinkAction):
    name = "send-oracle"
    verbose_name = _("Send Key(Oracle)")
    url = "horizon:kms:secrets:send_key_oracle"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"name": datum.name, "key_id": datum.key_id})

        return "?".join([base_url, params])

class SendAzureKey(tables.LinkAction):
    name = "send-azure"
    verbose_name = _("Send Key(Azure)")
    url = "horizon:kms:secrets:send_key_azure"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"name": datum.name, "key_id": datum.key_id})

        return "?".join([base_url, params])

class SendGoogleKey(tables.LinkAction):
    name = "send-google"
    verbose_name = _("Send Key(Google)")
    url = "horizon:kms:secrets:select_google_connection"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"name": datum.name, "key_id": datum.key_id})

        return "?".join([base_url, params])

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
    key_id = tables.Column('key_id', verbose_name=_("Key ID"))
    key_version = tables.Column('key_version', verbose_name=_("Key Version"))
    container_id = tables.Column('container_id', verbose_name=_("Container ID"))
    key_state = tables.Column('key_state', verbose_name=_("Key State"))
    time_created = tables.Column('time_created', verbose_name=_("Time Created"))

    class Meta(object):
        name = "secrets"
        verbose_name = _("RKMS")
        table_actions = (SecretsFilterAction, CreateSecret, DeleteSecret,)
        row_actions = (RotateSecret, AutoRotateSecret, SendAWSKey, SendOracleKey, SendAzureKey, SendGoogleKey,)