from jupyterhub_extension import ExtensionApp
from .handlers import handlers

class HelloWorld(ExtensionApp):
    """A simple JupyterHub that says "Hello, World!" when you hit its endpoint.
    """
    name = "hello"
    handlers = handlers

    

