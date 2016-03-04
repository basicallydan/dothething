# Do The Thing

Do The Thing is an easy-to-configure server for handling GitHub webhooks, written in
Python using the Flask framework.

## Install

### Pre-requisites

I have tested it only on Ubuntu 14.04.1 LTS. These requirements refer to _this_ guide. There are other ways to deploy `dothething` but this is how I do it.

* Python 3+
* nginx
* A GitHub repository

Installation is a little long-winded, and I might come up with a quicker, easier way to install it with time. For now, follow these instructions please.

#### Step 1: Get the stuff

First, **clone this repo**:

```
git@github.com:basicallydan/dothething.git
```

`cd` into the directory it's been cloned into, and use `virtualenv` to create a new virtual environment for `dothething`. You may put it into this directory using `env` or `venv` if you like.

#### Step 2: Get the requirements

```
# Replace the path for python3 with whatever your python3 path is.
virtualenv --python=/usr/bin/python3
```

Get your shell into that environment using `source venv/bin/activate`.

Install the requirements:

```
pip install -r requirements.txt
```

Now make a new upstart script in `/etc/init` called `dothething.conf`. The contents should be something like this, replacing directories to whatever you've been using thus far:

#### Step 4: Configure your server

Use `sample.config.ini` to come up with a suitable config file. There are two parts to it:

##### `DEFAULT` is used for application settings:

* `WorkingDirectory` is where to go to run all of your commands.
* `GlobalPath` is the `PATH` environment variable to send to any commands that you run. Keep in mind to execute binaries or scripts outside of the working directory you still need to use absolute paths, but those binaries or scripts will have access to the `PATH` you specify in `GlobalPath`.
* `DeployKeyLocation` is the location of an SSH key that you want to use to communicate with GitHub. I use this for a read-only key that can be configured in the "Deploy Keys" section of your repo's Settings.

##### Branch sections

Next you can create a different config section for each branch that you'd like to handle the webhook requests for. By that I mean, if a commit is pushed to a certain branch, you can have certain commands that will run only for pushes to that branch.

In each section you can specify an array:

```
commands = [
  '/usr/bin/thingie',
  '/usr/bin/anotherthingie --output out.log'
  ]
```

The spaces before each line are important here so make sure you keep them in line with one another. Each array element is just a string with a command that you might write in bash.

##### uWSGI Section

The next section specifies options for loading the app into uWSGI.

#### Step 5: Hook up nginx

Create a new `nginx` site config file in `conf.d` or `sites-enabled` or wherever you put them, and fill it with something like this.

```
server {
    listen       hooks.yoursite.com:80;
    server_name  hooks.yoursite.com;
    client_max_body_size 10M;

    location / {
      include uwsgi_params;
      uwsgi_pass unix:/src/dothething/dothething.sock;
    }
}
```

#### Step 6: Create an upstart script for `dothething`

```
description "uWSGI server instance configured to serve dothething"

start on runlevel [2345]
stop on runlevel [!2345]

# Put your username here!
setuid dan
setgid www-data

env PATH=/src/dothething/venv/bin
chdir /src/dothething
exec uwsgi --ini config.ini
```
