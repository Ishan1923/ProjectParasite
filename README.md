use this command to run the server script on server/machine u intend to use as a controller.

``` bash
uv run python3 -m  uvicorn server:app --host IP_SERVER --port 8000
```

use the below command on the machine which will be controlled.

``` bash
uv run client.py IP_SERVER
```