import subprocess
from fastapi import FastAPI, request

app = FastAPI()


@app.route('/menu')
def menu():
    command = request.form['suggestion']
    # command = 'echo ' + param + ' >> ' + 'menu.txt'

    subprocess.call(command, shell=True)

    return {"status": 'OK'}


@app.route('/clean')
def clean():
    subprocess.call('echo Menu: > menu.txt', shell=True)
    # more code here
    return {"status": 'OK'}


if __name__ == '__main__':
    app.run(debug=True)
