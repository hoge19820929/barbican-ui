from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import exceptions
from horizon import tables

from . import api

class SecretsFilterAction(tables.FilterAction):
    filter_type = 'server'
    filter_choices = (('alias', _('Alias ='), True),
                      ('key_id', _('Key ID ='), True),
                      ('key_state', _('Key State ='), True),
                      ('key_type', _('Key Type ='), True),
                      ('key_spec', _('Key Spec ='), True),
                      ('key_usage', _('Key Usage ='), True),
                      ('description', _('Description ='), True),
                      ('aws_account', _('AWS Account ='), True),
                      ('region', _('Region ='), True),
                      ('origin', _('Origin ='), True),
                      ('creation_date', _('Creation Date ='), True),
                      ('expiration_date', _('Expiration Date ='), True))

class CreateSecret(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Secret")
    url = "horizon:project:aws:create"
    classes = ("ajax-modal",)
    icon = "plus"

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
            alias = api.get_key_alias(obj_id)
            api.byok_aws(request, alias, 'alias/' + alias, True)
        except Exception:
            exceptions.handle(request, _("Unable to rotate secrets."))

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
    
    def delete(self, request, id):
        try:
            api.schedule_key_deletion(id)
        except Exception as e:
            exceptions.handle(request, _("Unable to delete secrets."))

class SecretsTable(tables.DataTable):

    alias = tables.Column('alias', verbose_name=_("Alias"))
    key_id = tables.Column('key_id', verbose_name=_("Key ID"))
    key_state = tables.Column('key_state', verbose_name=_("Key State"))
    key_type = tables.Column('key_type', verbose_name=_("Key Type"))
    key_spec = tables.Column('key_spec', verbose_name=_("Key Spec"))
    key_usage = tables.Column('key_usage', verbose_name=_("Key Usage"))
    description = tables.Column('description', verbose_name=_("Description"))
    aws_account = tables.Column('aws_account', verbose_name=_("AWS Account"))
    region = tables.Column('region', verbose_name=_("Region"))
    origin = tables.Column('origin', verbose_name=_("Origin"))
    creation_date = tables.Column('creation_date', verbose_name=_("Creation Date"))
    expiration_date = tables.Column('expiration_date', verbose_name=_("Expiration Date"))

    class Meta(object):
        name = "aws"
        verbose_name = _("AWS Secrets")
        table_actions = (SecretsFilterAction, RotateSecret, DeleteSecret,)