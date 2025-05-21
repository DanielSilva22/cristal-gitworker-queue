from flask import Flask, request, jsonify
import os
import json
import time
import threading
from git import Repo

app = Flask(__name__)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_URL = f"https://{GITHUB_TOKEN}@github.com/DanielSilva22/cristal-semantique-core1.git"
LOCAL_REPO = "/tmp/repo"

def process_queue():
    while True:
        try:
            if not os.path.exists(LOCAL_REPO):
                Repo.clone_from(REPO_URL, LOCAL_REPO)
            repo = Repo(LOCAL_REPO)
            queue_dir = os.path.join(LOCAL_REPO, "queue")
            os.makedirs(queue_dir, exist_ok=True)

            for filename in os.listdir(queue_dir):
                if filename.endswith(".json"):
                    queue_path = os.path.join(queue_dir, filename)
                    with open(queue_path, "r", encoding="utf-8") as f:
                        task = json.load(f)
                    path = task.get("path")
                    data = task.get("data")
                    if path and data is not None:
                        full_path = os.path.join(LOCAL_REPO, path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(data if isinstance(data, str) else json.dumps(data, indent=2, ensure_ascii=False))
                        repo.git.add(path)
                        repo.index.commit(f"[AutoPush] via queue: {filename}")
                        origin = repo.remote(name="origin")
                        origin.push()
                        os.remove(queue_path)
        except Exception as e:
            print("Error processing queue:", e)
        time.sleep(30)  # Vérifie toutes les 30 secondes

@app.route("/")
def home():
    return "Cristal GitWorker Queue is running"

# Lancer le thread de queue en arrière-plan
threading.Thread(target=process_queue, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
