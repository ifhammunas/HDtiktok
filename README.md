# TikTok Video Downloader

A simple Flask app for downloading TikTok videos by URL.

## Local run

```bash
python -m pip install -r requirements.txt
python main.py
```

Then open http://127.0.0.1:5000/

## Deploy on Render

1. Push this project to GitHub.
2. Create a new Render Web Service.
3. Connect the repository.
4. Render will use the included `render.yaml` configuration automatically.
5. Deploy.

## Production server

```bash
gunicorn main:app
```
