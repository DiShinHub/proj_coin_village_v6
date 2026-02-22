from flask import Flask
import subprocess

app = Flask(__name__)
proc = None

@app.route("/start/rotate-urls")
def start_rotate_urls():
    global proc
    if not proc:
        proc = subprocess.Popen(
            ["python", "-m", "services.rotate_urls"]
        )
    return "started"

@app.route("/stop/rotate-urls")
def stop_rotate_urls():
    global proc
    if proc:
        proc.terminate()
        proc = None
    return "stopped"

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=20000)