# Do The Thing

Do The Thing is an easy-to-configure server for handling webhooks, written in
Python using the Flask framework.

## Get started

### Install

```bash
pip install dothething
```

### Configure

```json
{
  "port":3000,
  "endpoints": {
    "/github": "./Users/dan/projects/danhough.com/deploy.sh"
  }
}
```

Whenever the endpoint `https://localhost:3000/github` receives a `POST` request
the specified command, `./Users/dan/projects/danhough.com/deploy.sh`, will be
executed.

