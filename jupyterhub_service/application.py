import os
import logging
from urllib.parse import urlparse

from tornado import web
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from jupyter_core.application import JupyterApp
from jupyterhub.services.auth import HubAuth
from jupyterhub.log import CoroutineLogFormatter, log_request
from jupyterhub.utils import url_path_join

from traitlets import (
    default,
    Unicode,
    Integer,
    List,
    Dict
)

ROOT = os.path.dirname(__file__)
STATIC_FILES_DIR = os.path.join(ROOT, 'static')
TEMPLATES_DIR = os.path.join(ROOT, 'templates')

class UnicodeFromEnv(Unicode):
    """A Unicode trait that gets its default value from the environment
    Use .tag(env='VARNAME') to specify the environment variable to use.
    """
    def default(self, obj=None):
        env_key = self.metadata.get('env')
        if env_key in os.environ:
            return os.environ[env_key]
        else:
            return self.default_value


class ServiceApp(JupyterApp):
    """
    A JupyterHub Service made easy. Write a subclass and ServiceApp
    will handle the boilerplate code necessary to connect our app to 
    JupyterHub.
    """
    name = Unicode("")

    description = Unicode(__doc__)

    base_url = UnicodeFromEnv('').tag(
        env='JUPYTERHUB_SERVICE_PREFIX',
        config=True)

    # @default
    # def _default_base_url(self):
    #     return 

    hub_api_url = UnicodeFromEnv('http://127.0.0.1:8081/hub/api/').tag(
        env='JUPYTERHUB_API_URL',
        config=True)

    hub_api_token = UnicodeFromEnv('').tag(
        env='JUPYTERHUB_API_TOKEN',
        config=True,
    )

    hub_base_url = UnicodeFromEnv('http://127.0.0.1:8000/').tag(
        env='JUPYTERHUB_BASE_URL',
        config=True,
    )

    ip = Unicode('127.0.0.1').tag(config=True)

    @default('ip')
    def _ip_default(self):
        url_s = os.environ.get('JUPYTERHUB_SERVICE_URL')
        if not url_s:
            return '127.0.0.1'
        url = urlparse(url_s)
        return url.hostname

    port = Integer(9090).tag(config=True)

    @default('port')
    def _port_default(self):
        url_s = os.environ.get('JUPYTERHUB_SERVICE_URL')
        if not url_s:
            return 9090
        url = urlparse(url_s)
        return url.port

    template_paths = List(
        help="Paths to search for jinja templates.",
    ).tag(config=True)

    @default('template_paths')
    def _template_paths_default(self):
        return [TEMPLATES_DIR]

    tornado_settings = Dict()

    _log_formatter_cls = CoroutineLogFormatter

    @default('log_level')
    def _log_level_default(self):
        return logging.INFO

    @default('log_datefmt')
    def _log_datefmt_default(self):
        """Exclude date from default date format"""
        return "%Y-%m-%d %H:%M:%S"

    @default('log_format')
    def _log_format_default(self):
        """override default log format to include time"""
        return "%(color)s[%(levelname)1.1s %(asctime)s.%(msecs).03d %(name)s %(module)s:%(lineno)d]%(end_color)s %(message)s"

    def init_logging(self):
        """Initialize logging"""
        # This prevents double log messages because tornado use a root logger that
        # self.log is a child of. The logging module dipatches log messages to a log
        # and all of its ancenstors until propagate is set to False.
        self.log.propagate = False

        _formatter = self._log_formatter_cls(
            fmt=self.log_format,
            datefmt=self.log_datefmt,
        )

        # hook up tornado 3's loggers to our app handlers
        for log in (app_log, access_log, gen_log):
            # ensure all log statements identify the application they come from
            log.name = self.log.name
        logger = logging.getLogger('tornado')
        logger.propagate = True
        logger.parent = self.log
        logger.setLevel(self.log.level)

    def init_hub_auth(self):
        """Initialize hub authentication"""
        self.hub_auth = HubAuth()

    def init_tornado_settings(self):
        """Initialize tornado config."""
        settings = dict(
            log_function=log_request,
            config=self.config,
            log=self.log,
            base_url=self.base_url,
            hub_auth = self.hub_auth,
            login_url=self.hub_auth.login_url,
            hub_base_url = self.hub_base_url,
            logout_url=url_path_join(self.hub_base_url, 'hub/logout'),
            static_path=STATIC_FILES_DIR,
            static_url_prefix=url_path_join(self.base_url, 'static/'),
            template_path=self.template_paths,
            #jinja2_env=jinja_env,
            xsrf_cookies=True,
        )
        
        # Add traits in subclass to tornado settings.
        base_traits = self.__class__.class_trait_names()
        children_traits = super(self.__class__, self).class_trait_names()

        # Find new traits in subclass.
        new_traits = set(children_traits).difference(set(base_traits))
        
        # Add traits to tornado settings
        for trait in new_traits:
            settings[new_trait] = getattr(new_trait)
        
        # Set tornado settings.
        settings.update(self.tornado_settings)
        self.tornado_settings = settings

    def init_handlers(self):
        self._handlers = []
        for endpoint, handler in self.handlers:
            url = url_path_join('services', self.base_url, self.name, endpoint)
            print(url)
            self._handlers.append((url, handler))

    def init_tornado_application(self):
        self.tornado_application = web.Application(self._handlers, **self.tornado_settings)

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        if self.generate_config or self.subapp:
            return
        self.init_hub_auth()
        self.init_tornado_settings()
        self.init_handlers()
        self.init_tornado_application()

    def start(self):
        if self.subapp:
            self.subapp.start()
            return

        if self.generate_config:
            self.write_config_file()
            return

        self.http_server = HTTPServer(self.tornado_application, xheaders=True)
        self.http_server.listen(self.port, address=self.ip)

        self.log.info("Running {} at http://{}:{}{}".format(self.name, self.ip, self.port, self.base_url))
        IOLoop.current().start()