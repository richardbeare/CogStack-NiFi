# Configuration file for jupyter-hub
# source : https://github.com/jupyterhub/jupyterhub-deploy-docker/blob/master/jupyterhub_config.py

import os
import pwd
import subprocess
import dockerspawner 
from jupyterhub.auth import LocalAuthenticator
from nativeauthenticator import NativeAuthenticator

class LocalNativeAuthenticator(NativeAuthenticator, LocalAuthenticator):
  pass

def pre_spawn_hook(spawner):
    username = spawner.user.name
    try:
        pwd.getpwnam(username)
    except KeyError:
        subprocess.check_call(["useradd", "-ms", "/bin/bash", username])

c = get_config()

# Spawn single-user servers as Docker containers
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

c.DockerSpawner.extra_create_kwargs = {"user": "root"}
c.DockerSpawner.environment = {
  "GRANT_SUDO": "1",
  "UID": "0", # workaround https://github.com/jupyter/docker-stacks/pull/420
}

# Spawn containers from this image
c.DockerSpawner.image = os.getenv("DOCKER_NOTEBOOK_IMAGE", "jupyterhub/singleuser:latest")

# JupyterHub requires a single-user instance of the Notebook server, so we
# default to using the `start-singleuser.sh` script included in the
# jupyter/docker-stacks *-notebook images as the Docker run command when
# spawning containers.  Optionally, you can override the Docker run command
# using the DOCKER_SPAWN_CMD environment variable.
spawn_cmd = os.environ.get("DOCKER_SPAWN_CMD", "start-singleuser.sh --SingleUserNotebookApp.default_url=/lab")

c.DockerSpawner.extra_create_kwargs.update({"command": spawn_cmd})

# Connect containers to this Docker network
# IMPORTANT, THIS MUST MATCH THE NETWORK DECLARED in "services.yml", by default: "cogstack-net"
network_name = os.environ.get("DOCKER_NETWORK_NAME", "cogstack-net")

c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name
# Pass the network name as argument to spawned containers
c.DockerSpawner.extra_host_config = { "network_mode": network_name }

# Explicitly set notebook directory because we"ll be mounting a host volume to
# it.  Most jupyter/docker-stacks *-notebook images run the Notebook server as
# user `jovyan`, and set the notebook directory to `/home/jovyan/work`.
# We follow the same convention.
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR") or "/home/jovyan/work"

shared_content_dir = os.environ.get("DOCKER_SHARED_DIR", "/home/jovyan/scratch")

c.DockerSpawner.notebook_dir = notebook_dir
# Mount the real user"s Docker volume on the host to the notebook user"s
# notebook directory in the container
c.DockerSpawner.volumes = { "jupyterhub-user-{username}": notebook_dir, "jupyter-hub-shared-scratch": shared_content_dir}
# volume_driver is no longer a keyword argument to create_container()
# c.DockerSpawner.extra_create_kwargs.update({ "volume_driver": "local" })

# Remove containers once they are stopped
c.DockerSpawner.remove_containers = True
# For debugging arguments passed to spawned containers
c.DockerSpawner.debug = False

# AUTHENTICATION
#c.Spawner.pre_spawn_hook = pre_spawn_hook
#c.Spawner.ip = "127.0.0.1"
c.DockerSpawner.environment = {"NO_PROXY" : os.environ["NO_PROXY"], "HTTP_PROXY" : os.environ["HTTP_PROXY"], "HTTPS_PROXY" : os.environ["HTTPS_PROXY"]}
c.Spawner.environment = {"NO_PROXY" : os.environ["NO_PROXY"], "HTTP_PROXY" : os.environ["HTTP_PROXY"], "HTTPS_PROXY" : os.environ["HTTPS_PROXY"]}

#c.Authenticator.allowed_users = {"admin"}
c.Authenticator.admin_users = admin = {"admin"}

# By default all users that make sign up on Native Authenticator
# need an admin approval so they can actually log in the system.
c.Authenticator.open_signup = False

c.LocalAuthenticator.create_system_users = True
c.SystemdSpawner.dynamic_users = True
c.PAMAuthenticator.admin_groups = {"wheel"}
c.Authenticator.whitelist = whitelist = set()

pwd = os.path.dirname(__file__)
with open(os.path.join(pwd, "userlist")) as f:
    for line in f:
        if not line:
            continue
        parts = line.split()
        # in case of newline at the end of userlist file
        if len(parts) >= 1:
            name = parts[0]
            whitelist.add(name)
            if len(parts) > 1 and parts[1] == "admin":
                admin.add(name)

# Get team memberships
team_map = {user: set() for user in whitelist}
with open(os.path.join(pwd, "teamlist")) as f:
    for line in f:
        if not line:
            continue
        parts = line.split()
        if len(parts) > 1:
            team = parts[0]
            members = set(parts[1:])
            for member in members:
                team_map[member].add(team)


# Spawn single-user servers as Docker containers
class DockerSpawner(dockerspawner.DockerSpawner):
    def start(self):
        # username is self.user.name
        self.volumes = {"jupyterhub-user-{}".format(self.user.name): notebook_dir}
        for team in team_map[self.user.name]:
            self.volumes["jupyterhub-team-{}".format(team)] = {
                "bind": os.path.join(shared_content_dir, team),
                "mode": "rw",  # or ro for read-only
            }

        subprocess.run(["chmod", "-R", "777", shared_content_dir])
        subprocess.run(["chown", "-R", "jovyan:users", shared_content_dir])
        return super().start()

#c.JupyterHub.authenticator_class = LocalNativeAuthenticator

c.FirstUseAuthenticator.create_users = True
c.JupyterHub.authenticator_class = "firstuseauthenticator.FirstUseAuthenticator" #"nativeauthenticator.NativeAuthenticator"

# User containers will access hub by container name on the Docker network
c.JupyterHub.ip = "*"
c.JupyterHub.hub_ip = "0.0.0.0"
c.JupyterHub.hub_port = 8888

# TLS config
c.JupyterHub.port = 443
c.JupyterHub.ssl_key = os.environ.get("SSL_KEY", "/etc/jupyterhub/root-ca.key")
c.JupyterHub.ssl_cert = os.environ.get("SSL_CERT", "/etc/jupyterhub/root-ca.pem")

# Persist hub data on volume mounted inside container
data_dir = os.environ.get("DATA_VOLUME_CONTAINER", "./")

c.JupyterHub.cookie_secret_file = os.path.join(data_dir, "jupyterhub_cookie_secret")

#------------------------------------------------------------------------------
# Application(SingletonConfigurable) configuration
#------------------------------------------------------------------------------
## This is an application.

## The date format used by logging formatters for %(asctime)s
#  Default: "%Y-%m-%d %H:%M:%S"
# c.Application.log_datefmt = "%Y-%m-%d %H:%M:%S"

## The Logging format template
#  Default: "[%(name)s]%(highlevel)s %(message)s"
# c.Application.log_format = "[%(name)s]%(highlevel)s %(message)s"

## Set the log level by value or name.
#  Choices: any of [0, 10, 20, 30, 40, 50, "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
#  Default: 30
# c.Application.log_level = 30

## Instead of starting the Application, dump configuration to stdout
#  Default: False
# c.Application.show_config = False

## Instead of starting the Application, dump configuration to stdout (as JSON)
#  Default: False
# c.Application.show_config_json = False

#------------------------------------------------------------------------------
# JupyterApp(Application) configuration
#------------------------------------------------------------------------------
## Base class for Jupyter applications

# c.ServerApp.port = 8888
# c.ServerApp.ip = "0.0.0.0"

# c.JupyterHub.ip = "0.0.0.0"
# c.ConfigurableHTTPProxy.api_url = "http://127.0.0.1:8887"
# c.JupyterHub.port = 443

# ideally a private network address
# c.JupyterHub.proxy_api_ip = "10.0.1.4"
# c.JupyterHub.proxy_api_port = 8887