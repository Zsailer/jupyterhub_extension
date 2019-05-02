# JupyterHub Service

The easy way to write a JupyterHub Extension. 

**Not ready for general use.**

## The purpose

[JupyterHub Services]() allow you to integrate a custom service with JupyterHub. **JupyterHub-Service** handles the boilerplate code for you. You can easily tranform your service into a Hub-authenticated, configurable service.


## How to use. 

See a simple "Hello, world" example [here]().

1. Install this package using `pip`:
    ```
    pip install jupyterhub_service
    ```
2. Write an endpoint handler that subclasses the `ServiceHandler`:
    ```python
    from jupyterhub_service import ServiceHandler

    class MyServiceHandler(ServiceHandler)

        def get(self):
            self.write("Hello, world!")
    ```
3. Write a simple service class for your service:
    ```python
    from jupyterhub_service import ServiceApp

    class MyService(ServiceApp):
        name = my_service
        handlers = [
            ('/my_service_endpoint', MyServiceHandler)
        ]
    ```
4. Tell JupyterHub about your service. Add this service to your JupyterHub's config file:
    ```python
    # jupyterhub_config.py
    
    c.JupyterHub.services = [
        {
            'name': 'my-service',
            'command': ['python', '/path/to/service/pyfile']
        }
    ]
    ```
5. Launch JupyterHub.
    ```
    jupyterhub
    ```
6. Try out your service!