from django.utils.translation import gettext_lazy as _
import horizon

class BarbicanDashboard(horizon.Dashboard):
    name = _("Kms")
    slug = "kms"

horizon.register(BarbicanDashboard)