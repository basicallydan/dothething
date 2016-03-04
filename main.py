import flask
from flask import Flask, request, jsonify
import subprocess
import configparser
import os
import json
import hmac
import hashlib

app = Flask(__name__)
app.debug = True

config = configparser.ConfigParser()
config.read('config.ini')

def validate_signature(key, body, signature):
    signature_parts = signature.split('=')
    if signature_parts[0] != "sha1":
        return False
    generated_sig = hmac.new(str.encode(key), msg=body, digestmod=hashlib.sha1)
    return hmac.compare_digest(generated_sig.hexdigest(), signature_parts[1])

@app.route("/")
def root():
    return "<html><body><h1>Do The Thing</h1></body></html>"


@app.route("/handle-push", methods=['POST'])
def handle_push():

    resp = flask.Response('')
    if request.method == 'POST':
        # First thing first: no point in continuing in the sigs don't match up
        secret_key = config['DEFAULT']['SecretKey']
        text_body = request.get_data()
        github_signature = request.headers['x-hub-signature']
        print(github_signature)
        if not validate_signature(secret_key, text_body, github_signature):
            return jsonify(success=False, message='Invalid GitHub signature'), 403

        # At this point we are confident that it is legit
        # Gather more config data
        working_directory = config['DEFAULT']['WorkingDirectory']
        path_to_use = config['DEFAULT']['GlobalPath']
        deploy_key_location = config['DEFAULT']['DeployKeyLocation']
        resp = flask.Response(request.data)
        resp.headers['content-type'] = 'application/json'
        json_body = request.get_json()
        branch = None

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

