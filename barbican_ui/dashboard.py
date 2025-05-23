from django.utils.translation import gettext_lazy as _
import horizon

from barbican_ui.content.secrets import panel as barbican_panel
from barbican_ui.content.aws import panel as aws_panel
from barbican_ui.content.oracle import panel as oracle_panel
from barbican_ui.content.azure import panel as azure_panel
from barbican_ui.content.google import panel as google_panel

class BarbicanDashboard(horizon.Dashboard):
    name = _("KMS")
    slug = "kms"
    panels = (
        'secrets',
        'aws',
        'oracle',
        'azure',
        'google',
    )
    default_panel = 'secrets'

horizon.register(BarbicanDashboard)
BarbicanDashboard.register(barbican_panel.Secrets)
BarbicanDashboard.register(aws_panel.Secrets)
BarbicanDashboard.register(oracle_panel.Secrets)
BarbicanDashboard.register(azure_panel.Secrets)
BarbicanDashboard.register(google_panel.Secrets)