import flask
from flask import Flask, request
import subprocess
import configparser
import os
import json

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')


@app.route("/")
def root():
    return "<html><body><h1>Do The Thing</h1></body></html>"


@app.route("/handle-push", methods=['POST'])
def handle_push():
    resp = flask.Response('')
    if request.method == 'POST':
        working_directory = config['DEFAULT']['WorkingDirectory']
        d = request.data
        resp = flask.Response(d)
        resp.headers['content-type'] = 'application/json'
        json_body = request.get_json()
        env_flag = '--local'
        branch = None
        path_to_use = config['DEFAULT']['GlobalPath']
        deploy_key_location = config['DEFAULT']['DeployKeyLocation']

        if 'refs/heads' in json_body['ref']:
            branch = json_body['ref'].split('/')[2]

        if branch != None:
            fetch_cmd = "/usr/bin/ssh-agent /bin/sh -c '/usr/bin/ssh-add %s; /usr/bin/git fetch origin %s'" % (deploy_key_location, branch)
            print("Running %s" % fetch_cmd)
            git_process = subprocess.Popen(
                fetch_cmd,
                cwd=working_directory,
                shell=True, env=os.environ.copy()
            )
            git_process.communicate()
            git_process = subprocess.Popen(' '.join(['/usr/bin/git', 'checkout', json_body['after']]),
                                           cwd=working_directory, shell=True, env=os.environ.copy())

        commands = json.loads(config.get(branch, "commands"))

        for command in commands:
            print("Running %s" % command)
            p = subprocess.Popen(command, cwd=working_directory,
                    shell=True, env={'PATH': path_to_use})
            p.communicate()

    return resp


if __name__ == "__main__":
    app.debug = True
    app.run(host=config['DEFAULT']['host'])

