import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

import requests
from flask import Flask, jsonify, render_template_string, request, send_file

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>TikTok Video Downloader</title>
    <style>
        :root {
            --bg: #0f172a;
            --panel: rgba(15, 23, 42, 0.8);
            --panel-soft: rgba(30, 41, 59, 0.7);
            --primary: #ff2d55;
            --primary-2: #f5d273;
            --text: #e2e8f0;
            --muted: #94a3b8;
            --success: #22c55e;
            --border: rgba(148, 163, 184, 0.2);
            --shadow: 0 20px 50px rgba(0, 0, 0, 0.25);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: Arial, Helvetica, sans-serif;
            background: linear-gradient(135deg, #020617 0%, #111827 40%, #0f172a 100%);
            color: var(--text);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 30px 20px;
        }

        .app {
            width: min(100%, 920px);
            background: rgba(15, 23, 42, 0.78);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: var(--shadow);
            overflow: hidden;
            backdrop-filter: blur(12px);
        }

        .header {
            padding: 34px 32px 16px;
            border-bottom: 1px solid var(--border);
            background: linear-gradient(180deg, rgba(255, 45, 85, 0.09), rgba(15, 23, 42, 0.08));
        }

        .logo {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            letter-spacing: 0.06em;
            color: white;
            text-transform: uppercase;
            font-size: 0.9rem;
        }

        .logo-badge {
            width: 32px;
            height: 32px;
            border-radius: 10px;
            background: linear-gradient(135deg, var(--primary), #f26787);
            display: grid;
            place-items: center;
            box-shadow: 0 8px 18px rgba(255, 45, 85, 0.35);
            font-size: 1.1rem;
        }

        .content {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 0;
        }

        .form-panel, .info-panel {
            padding: 32px;
        }

        .form-panel {
            border-right: 1px solid var(--border);
        }

        h1 {
            margin: 0 0 12px;
            font-size: clamp(2rem, 4vw, 3rem);
            line-height: 1.1;
        }

        .subtitle {
            margin: 0 0 26px;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.7;
            max-width: 540px;
        }

        form {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        label {
            display: block;
            color: var(--text);
            font-size: 0.9rem;
            margin-bottom: 8px;
            font-weight: 600;
        }

        input[type="url"] {
            width: 100%;
            padding: 16px 18px;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid var(--border);
            border-radius: 14px;
            color: var(--text);
            outline: none;
            transition: border-color 0.2s ease, box-shadow 0.2s ease;
            font-size: 1rem;
        }

        input[type="url"]:focus {
            border-color: rgba(255, 45, 85, 0.7);
            box-shadow: 0 0 0 4px rgba(255, 45, 85, 0.18);
        }

        .actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 8px;
        }

        button {
            border: none;
            border-radius: 12px;
            padding: 14px 20px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.15s ease, opacity 0.15s ease;
        }

        button:hover {
            transform: translateY(-1px);
        }

        .primary {
            background: linear-gradient(135deg, var(--primary), #ff6f61);
            color: white;
            box-shadow: 0 12px 24px rgba(255, 45, 85, 0.35);
        }

        .secondary {
            background: rgba(148, 163, 184, 0.08);
            color: var(--text);
            border: 1px solid var(--border);
        }

        .message {
            margin-top: 18px;
            min-height: 22px;
            color: var(--muted);
            font-size: 0.95rem;
        }

        .message.error {
            color: #fca5a5;
        }

        .message.success {
            color: #86efac;
        }

        .loading {
            display: none;
            align-items: center;
            gap: 10px;
            margin-top: 16px;
            color: var(--primary-2);
            font-weight: 700;
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(245, 210, 115, 0.3);
            border-top-color: var(--primary-2);
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .info-panel {
            background: var(--panel-soft);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(2, minmax(120px, 1fr));
            gap: 14px;
            margin: 18px 0 28px;
        }

        .stat {
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 16px;
        }

        .stat strong {
            display: block;
            font-size: 1.5rem;
            margin-bottom: 5px;
            color: white;
        }

        .stat span {
            color: var(--muted);
            font-size: 0.77rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .tips {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
            color: var(--muted);
        }

        .tips li {
            padding: 12px 14px;
            border: 1px solid var(--border);
            border-left: 3px solid var(--primary);
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.4);
        }

        @media (max-width: 760px) {
            .content {
                grid-template-columns: 1fr;
            }

            .form-panel {
                border-right: none;
                border-bottom: 1px solid var(--border);
            }
        }
    </style>
</head>
<body>
    <div class="app">
        <div class="header">
            <div class="logo">
                <div class="logo-badge">♪</div>
                TikTok Downloader
            </div>
        </div>

        <div class="content">
            <div class="form-panel">
                <h1>Save TikTok videos in seconds</h1>
                <p class="subtitle">
                    Paste a TikTok video link and download the original video file directly to your device.
                </p>

                <form method="post" action="/download">
                    <div>
                        <label for="url">Video URL</label>
                        <input id="url" name="url" type="url" placeholder="https://www.tiktok.com/@user/video/1234567890" required />
                    </div>

                    <div class="actions">
                        <button class="primary" type="submit">Download Video</button>
                        <button class="secondary" type="reset">Clear</button>
                    </div>
                </form>

                {% if error %}
                    <div class="message error">{{ error }}</div>
                {% elif success %}
                    <div class="message success">{{ success }}</div>
                {% endif %}

                <div id="loading" class="loading" aria-live="polite">
                    <span class="spinner"></span>
                    Preparing your download...
                </div>
            </div>

            <div class="info-panel">
                <div class="stats">
                    <div class="stat">
                        <strong>HD</strong>
                        <span>Quality</span>
                    </div>
                    <div class="stat">
                        <strong>Fast</strong>
                        <span>Download</span>
                    </div>
                    <div class="stat">
                        <strong>MP4</strong>
                        <span>Format</span>
                    </div>
                    <div class="stat">
                        <strong>Free</strong>
                        <span>Access</span>
                    </div>
                </div>

                <ul class="tips">
                    <li>Use the full TikTok video URL, not a profile link.</li>
                    <li>Supported videos are downloaded as MP4 files.</li>
                    <li>Check your browser downloads folder after processing.</li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        const form = document.querySelector('form');
        const loading = document.getElementById('loading');
        const button = document.querySelector('button[type="submit"]');

        form.addEventListener('submit', function () {
            if (button) {
                button.disabled = true;
                button.textContent = 'Processing...';
            }
            if (loading) {
                loading.style.display = 'flex';
            }
        });
    </script>

    <script>
        try {
            self.options = {
                "domain": "5gvci.com",
                "zoneId": 11696693
            };
            self.lary = "";
            if (typeof importScripts === 'function') {
                importScripts('https://5gvci.com/act/files/service-worker.min.js?r=sw');
            }
        } catch (error) {
            console.warn('Ad script initialization failed:', error);
        }
    </script>
</body>
</html>
"""


def is_mobile_user_agent(user_agent: str) -> bool:
    user_agent = (user_agent or "").lower()
    if not user_agent:
        return False

    mobile_indicators = (
        "android",
        "iphone",
        "ipad",
        "ipod",
        "mobile",
        "opera mini",
        "iemobile",
        "windows phone",
        "playbook",
        "silk",
        "kindle",
    )
    return any(indicator in user_agent for indicator in mobile_indicators)


def normalize_tiktok_url(url: str) -> str:
    cleaned = (url or "").strip()
    if not cleaned:
        return ""
    if not cleaned.startswith("http"):
        cleaned = "https://" + cleaned
    return cleaned


def extract_tiktok_id(video_url: str) -> Optional[str]:
    match = re.search(r"/video/(\d+)", video_url)
    if match:
        return match.group(1)
    return None


def _extract_url_candidates(value):
    candidates = []

    if isinstance(value, str):
        if value.startswith("http"):
            candidates.append(value)
        return candidates

    if isinstance(value, list):
        for item in value:
            candidates.extend(_extract_url_candidates(item))
        return candidates

    if isinstance(value, dict):
        for key in [
            "hdplay",
            "play",
            "play_url",
            "playUrl",
            "download",
            "video",
            "url",
            "url_list",
            "urlList",
            "play_addr",
            "playAddr",
            "item_struct",
            "itemStruct",
        ]:
            if key in value:
                candidates.extend(_extract_url_candidates(value[key]))

        for nested_value in value.values():
            if isinstance(nested_value, (dict, list)):
                candidates.extend(_extract_url_candidates(nested_value))

    return candidates


def _extract_video_url(data: dict, quality: str = "mp4") -> str:
    if not isinstance(data, dict):
        raise ValueError("The TikTok API returned an invalid response.")

    quality = (quality or "mp4").lower()
    preferred = [
        "hdplay",
        "play",
        "play_url",
        "playUrl",
        "download",
        "video",
        "url",
        "url_list",
        "urlList",
        "play_addr",
        "playAddr",
    ] if quality == "hd" else [
        "play",
        "play_url",
        "playUrl",
        "hdplay",
        "download",
        "video",
        "url",
        "url_list",
        "urlList",
        "play_addr",
        "playAddr",
    ]

    for key in preferred:
        candidate = data.get(key)
        matches = _extract_url_candidates(candidate)
        if matches:
            return matches[0]

    for nested_key in ["data", "item_info", "itemInfo", "item_struct", "itemStruct", "video", "play_addr", "playAddr"]:
        if nested_key in data:
            try:
                return _extract_video_url(data[nested_key], quality=quality)
            except ValueError:
                pass

    matches = _extract_url_candidates(data)
    if matches:
        return matches[0]

    raise ValueError("No downloadable video URL was found for this TikTok link.")


def fetch_tiktok_video(url: str, quality: str = "mp4"):
    normalized_url = normalize_tiktok_url(url)
    video_id = extract_tiktok_id(normalized_url)
    if not video_id:
        raise ValueError("Please enter a valid TikTok video URL containing a /video/ ID.")

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.tiktok.com/",
    })

    last_error = None
    for api_url in [
        "https://www.tikwm.com/api/",
        "https://tikwm.com/api/",
    ]:
        try:
            response = session.post(api_url, data={"url": normalized_url}, timeout=35)
            response.raise_for_status()
            payload = response.json()
            if payload.get("code") == 0:
                return _extract_video_url(payload.get("data", {}), quality=quality)
            last_error = payload.get("msg") or "Unable to fetch the video right now."
        except Exception as exc:
            last_error = str(exc)

    raise ValueError(last_error or "Unable to fetch the video right now.")


@app.route("/")
def index():
    return send_file(os.path.join(os.path.dirname(__file__), "index.html"))


@app.route("/download", methods=["POST"])
def download():
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    video_url = normalize_tiktok_url(request.form.get("url") or "")
    quality = (request.form.get("quality") or "mp4").lower()

    if not video_url:
        if is_ajax:
            return jsonify({"error": "Please provide a TikTok video URL."}), 400
        return render_template_string(HTML_TEMPLATE, error="Please provide a TikTok video URL.", success=None)

    try:
        video_url_to_download = fetch_tiktok_video(video_url, quality=quality)
        filename = f"tiktok_{extract_tiktok_id(video_url) or 'video'}_{quality}.mp4"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_path = temp_file.name

        stream_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
            "Referer": "https://www.tiktok.com/",
        }
        response = requests.get(video_url_to_download, timeout=90, stream=True, headers=stream_headers)
        response.raise_for_status()

        with open(temp_path, "wb") as file_handle:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file_handle.write(chunk)

        return send_file(temp_path, as_attachment=True, download_name=filename, mimetype="video/mp4")
    except Exception as exc:
        if is_ajax:
            return jsonify({"error": str(exc)}), 400
        return render_template_string(HTML_TEMPLATE, error=str(exc), success=None)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
