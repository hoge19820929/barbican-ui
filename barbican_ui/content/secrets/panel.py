from django.utils.translation import gettext_lazy as _
import horizon

class Secrets(horizon.Panel):
    name = _("RKMS")
    slug = "secrets"
