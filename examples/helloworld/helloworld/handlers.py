from jupyterhub_service import ServiceHandler


class HelloWorldHandler(ServiceHandler):

    def get(self):
        self.write("Hello, World!")


handlers = [
    ('/hello', HelloWorldHandler)
]