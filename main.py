import flask
from flask import Flask, request
import subprocess
import configparser

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')


@app.route("/handle-push", methods=['POST'])
def handle_push():
    resp = flask.Response('')
    if request.method == 'POST':
        working_directory = config['DEFAULT']['WorkingDirectory']
        d = request.data
        resp = flask.Response(d)
        resp.headers['content-type'] = 'application/json'
        json = request.get_json()
        env_flag = '--local'
        branch = None

        if 'refs/heads' in json['ref']:
            branch = json['ref'].split('/')[2]

        if branch != None:
            git_process = subprocess.Popen(['git', 'fetch', 'origin', branch],
                                           cwd=working_directory)
            git_process.communicate()
            git_process = subprocess.Popen(['git', 'checkout', json['after']],
                                           cwd=working_directory)

        # If it's the master branch use master
        if branch == 'master':
            env_flag = '--live'
        # If it's the dev branch use dev
        elif branch == 'staging':
            env_flag = '--dev'
        else:
            return resp

        git_process.communicate()
        p = subprocess.Popen(['npm', 'install'], cwd=working_directory)
        p.communicate()

        p = subprocess.Popen(['./node_modules/gulp-cli/bin/gulp.js',
                              'deploy',
                              env_flag], cwd=working_directory)
        (out, err) = p.communicate()

        git_process = subprocess.Popen(['git', 'checkout', 'master'],
                                       cwd=working_directory)

        git_process.communicate()

        print("Output: %s" % str(out))
        print("Errors %s" % str(err))

    return resp


if __name__ == "__main__":
    app.debug = True
    app.run(host=config['DEFAULT']['host'])
