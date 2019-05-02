from jupyterhub_service import ServiceApp
from .handlers import handlers

class HelloWorld(ServiceApp):
    """A simple JupyterHub that says "Hello, World!" when you hit its endpoint.
    """
    name = "hello"
    handlers = handlers

main = HelloWorld.launch_instance

if __name__ == '__main__':
    main()