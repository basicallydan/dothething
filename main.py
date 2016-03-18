#!/usr/bin/python
# -*- coding: utf-8 -*-
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


@app.route("/🙂")
def smile():
    return "<!DOCTYPE html><html><body><h1>Smile</h1></body></html>"


@app.route("/🙏")
def please():
    return "<!DOCTYPE html><html><body><h1>Please</h1></body></html>"


@app.route("/handle-push", methods=['POST'])
def handle_push():

    resp = flask.Response('')
    if request.method == 'POST':
        # First thing first: no point in continuing in the sigs don't match up
        secret_key = config['DEFAULT']['SecretKey']
        text_body = request.get_data()
        github_signature = request.headers['x-hub-signature']
        print(secret_key)
        print(github_signature)
        print(text_body)
        if not validate_signature(secret_key, text_body, github_signature):
            return jsonify(success=False, message='Invalid GitHub signature'), 403

        # At this point we are confident that it is legit
        # Gather more config data
        working_directory = config['DEFAULT']['WorkingDirectory']
        path_to_use = config['DEFAULT']['GlobalPath']
        if 'DeployKeyLocation' in config['DEFAULT']:
            deploy_key_location = config['DEFAULT']['DeployKeyLocation']
        else:
            deploy_key_location = None
        resp = flask.Response(request.data)
        resp.headers['content-type'] = 'application/json'
        reqbody = request.get_json()
        branch = None
        repository = None
        config_section = None

        if 'refs/heads' not in reqbody['ref']:
            return jsonify(success=False, message='Missing reference'), 400

        if ('repository' not in reqbody) or ('full_name' not in reqbody['repository']):
            return jsonify(success=False, message='Missing repo info'), 400

        branch = reqbody['ref'].split('/')[2]
        repository = reqbody['repository']['full_name']
        config_section = repository + '/' + branch

        # Load repo-specific configuration
        if config[config_section]['WorkingDirectory']:
            working_directory = config[config_section]['WorkingDirectory']

        if branch is not None:
            if deploy_key_location is not None:
                fetch_cmd = "/usr/bin/ssh-agent /bin/sh -c '/usr/bin/ssh-add %s; /usr/bin/git fetch origin %s'" % (deploy_key_location, branch)
            else:
                fetch_cmd = "/usr/bin/git fetch origin %s'" % branch
            print("Running %s" % fetch_cmd)
            git_process = subprocess.Popen(
                fetch_cmd,
                cwd=working_directory,
                shell=True, env=os.environ.copy()
            )
            git_process.communicate()
            git_process = subprocess.Popen(' '.join(['/usr/bin/git', 'checkout', reqbody['after']]),
                                           cwd=working_directory, shell=True, env=os.environ.copy())

        commands = json.loads(config.get(config_section, "commands"))

        for command in commands:
            print("Running %s" % command)
            p = subprocess.Popen(command, cwd=working_directory,
                    shell=True, env={'PATH': path_to_use})
            p.communicate()

    return resp


if __name__ == "__main__":
    app.debug = True
    app.run(host=config['DEFAULT']['host'])

