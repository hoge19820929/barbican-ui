from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import exceptions
from horizon import tables

from . import api
from barbican_ui.content.secrets import api as barbican_api

class SecretsFilterAction(tables.FilterAction):
    filter_type = 'query'
    filter_choices = (('alias', _('Alias ='), True),
                      ('key_id', _('Key ID ='), True),
                      ('key_state', _('Key State ='), True),
#                      ('key_type', _('Key Type ='), True),
#                      ('key_spec', _('Key Spec ='), True),
                      ('key_usage', _('Key Usage ='), True),
                      ('source_key', _('Source Key ='), True),
                      ('key_version', _('Key Version ='), True),
#                      ('description', _('Description ='), True),
                      ('aws_account', _('AWS Account ='), True),
                      ('region', _('Region ='), True),
#                      ('origin', _('Origin ='), True),
                      ('creation_date', _('Creation Date ='), True),
                      ('expiration_date', _('Expiration Date ='), True))

class CreateSecret(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Secret")
    url = "horizon:kms:aws:create"
    classes = ("ajax-modal",)
    icon = "plus"

class IndexAll(tables.LinkAction):
    name = "index_all"
    verbose_name = _("View All Sent Keys")
    url = "horizon:kms:aws:index_all"

class RotateSecret(tables.BatchAction):
    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            "Rotate Secret",
            "Rotate Secrets",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            "Rotate Secret",
            "Rotate Secrets",
            count
        )
    
    name = "rotate"
    verbose_name = _("Rotate Secret")
    icon = "pencil"

    def action(self, request, obj_id):
        try:
            aws_conn = obj_id.split(',')[0]
            key_id = obj_id.split(',')[1]
            conn = barbican_api.create_connection(request)
            alias = api.get_key_alias(conn, aws_conn, key_id)
            api.byok_aws(conn, aws_conn, alias, 'alias/' + alias, True)
        except Exception:
            exceptions.handle(request, _("Unable to rotate secrets."))

class AutoRotateSecret(tables.LinkAction):
    name = "auto_rotate"
    verbose_name = _("Auto Rotate Secret")
    url = "horizon:kms:aws:auto_rotate"
    classes = ("ajax-modal",)
    icon = "plus"

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"alias": datum.alias, "aws_conn": datum.aws_conn})

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
    
    def delete(self, request, obj_id):
        try:
            aws_conn = obj_id.split(',')[0]
            key_id = obj_id.split(',')[1]
            api.schedule_key_deletion(request, aws_conn, key_id)
        except Exception as e:
            exceptions.handle(request, _("Unable to delete secrets."))

class SetAWSCredentials(tables.LinkAction):
    name = "set_cred"
    verbose_name = _("Set Access Key")
    url = "horizon:kms:aws:set_cred"
    classes = ("ajax-modal",)
    icon = "plus"

class SecretsTable(tables.DataTable):

    alias = tables.Column('alias', verbose_name=_("Alias"))
    key_id = tables.Column('key_id', verbose_name=_("Key ID"))
    key_state = tables.Column('key_state', verbose_name=_("Key State"))
#    key_type = tables.Column('key_type', verbose_name=_("Key Type"))
#    key_spec = tables.Column('key_spec', verbose_name=_("Key Spec"))
    key_usage = tables.Column('key_usage', verbose_name=_("Key Usage"))
    source_key = tables.Column('source_key', verbose_name=_("Source Key"))
    key_version = tables.Column('key_version', verbose_name=_("Key Version"))
#    description = tables.Column('description', verbose_name=_("Description"))
    aws_account = tables.Column('aws_account', verbose_name=_("AWS Account"))
    region = tables.Column('region', verbose_name=_("Region"))
#    origin = tables.Column('origin', verbose_name=_("Origin"))
    creation_date = tables.Column('creation_date', verbose_name=_("Creation Date"))
    expiration_date = tables.Column('expiration_date', verbose_name=_("Expiration Date"))
    aws_conn = tables.Column('aws_conn', hidden=True)

    class Meta(object):
        name = "aws"
        verbose_name = _("AWS Secrets")
        table_actions = (SecretsFilterAction, IndexAll, SetAWSCredentials, DeleteSecret,)
        row_actions = (AutoRotateSecret, RotateSecret,)