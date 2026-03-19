from flask import Flask
import subprocess
import sys
import os
import signal

"""
bot listner api
"""
app = Flask(__name__)
proc_cv_research_prod02_gen01 = None

@app.route("/rotate-urls/start")
def start_rotate_urls():
    global proc_cv_research_prod02_gen01
    if not proc_cv_research_prod02_gen01:
        proc_cv_research_prod02_gen01 = subprocess.Popen(
            [sys.executable, "-m", "services.cv_research_prod02_gen01"]
        )
    return "started"

@app.route("/rotate-urls/stop")
def stop_rotate_urls():
    global proc_cv_research_prod02_gen01
    if proc_cv_research_prod02_gen01:
        
        #proc_cv_research_prod02_gen01.terminate()
        os.kill(proc_cv_research_prod02_gen01.pid, signal.SIGTERM)
        proc_cv_research_prod02_gen01 = None
        
    return "stopped"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=20000)