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

        # If it's the master branch use master
        if json['ref'] == 'refs/heads/master':
            git_process = subprocess.Popen(['git', 'fetch',
                                            'origin', json['after']],
                                           cwd=working_directory)
            git_process.communicate()
            git_process = subprocess.Popen(['git', 'checkout', json['after']],
                                           cwd=working_directory)
        # If it's the dev branch use dev
        elif json['ref'] == 'refs/heads/staging':
            git_process = subprocess.Popen(['git', 'fetch',
                                            'origin', json['after']],
                                           cwd=working_directory)
            git_process.communicate()
            git_process = subprocess.Popen(['git', 'checkout', json['after']],
                                           cwd=working_directory)
            env_flag = '--dev'
        else:
            return resp

        git_process.communicate()

        p = subprocess.Popen(['./node_modules/gulp-cli/bin/gulp.js',
                              'deploy',
                              env_flag], cwd=working_directory)
        (out, err) = p.communicate()

        git_process = subprocess.Popen(['git', 'checkout', 'master'],
                                       cwd=working_directory)

        git_process.communicate()

        print(str(out))
        print(str(err))

    return resp


if __name__ == "__main__":
    app.debug = True
    app.run()
