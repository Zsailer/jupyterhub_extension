from jupyterhub.handlers import BaseHandler as JupyterHubBaseHandler
from jupyterhub.services.auth import HubAuthenticated

class ServiceHandler(HubAuthenticated, JupyterHubBaseHandler):

    @property
    def hub_auth(self):
        return self.settings.get('hub_auth')

    @property
    def csp_report_uri(self):
        return self.settings.get('csp_report_uri',
            url_path_join(self.settings.get('hub_base_url', '/hub'), 'security/csp-report')
        )

    def finish(self):
        return super(JupyterHubBaseHandler, self).finish()
