import uvicorn
import google.cloud.logging
import os
import subprocess

workers = int(os.environ['workers'])

client = google.cloud.logging.Client()
client.setup_logging()
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('http_proxy', None)

if __name__ == "__main__":
    command = ['python', 'app/agent/a2a.py']
    print(subprocess.Popen(command, env=os.environ.copy()))
    uvicorn.run("web.ui.main:app", 
        host="0.0.0.0",
        port=12000,
        workers=workers
    )