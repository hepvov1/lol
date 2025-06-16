from flask import Flask, render_template, request, send_file
import socket
import whois
import requests
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from werkzeug.utils import secure_filename
import os
import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

SOCIALS = {
    "Telegram": "https://t.me/{}",
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
    "VK": "https://vk.com/{}",
    "Instagram": "https://instagram.com/{}",
    "Reddit": "https://reddit.com/user/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "TikTok": "https://www.tiktok.com/@{}"
}

def check_username(username):
    results = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    for name, url in SOCIALS.items():
        full_url = url.format(username)
        try:
            resp = requests.head(full_url, timeout=5, headers=headers)
            results[name] = full_url if resp.status_code == 200 else None
        except:
            results[name] = None
    return results

def get_whois(domain):
    try:
        w = whois.whois(domain)
        return w.text
    except:
        return "WHOIS info not found."

def get_dns(domain):
    try:
        return socket.gethostbyname(domain)
    except:
        return "DNS not resolved."

def get_ip_info(ip):
    try:
        data = requests.get(f"http://ip-api.com/json/{ip}").json()
        return data
    except:
        return {}

def get_exif(path):
    try:
        img = Image.open(path)
        exif_data = img._getexif()
        if not exif_data:
            return {}
        result = {}
        gps_info = {}
        for tag, val in exif_data.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for t in val:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_info[sub_decoded] = val[t]
                result["GPSInfo"] = gps_info
            else:
                result[decoded] = val
        return result
    except Exception as e:
        return {"error": str(e)}

def extract_coords(exif_data):
    if "GPSInfo" not in exif_data:
        return None
    gps_info = exif_data["GPSInfo"]
    def convert(value):
        d, m, s = value
        return d[0]/d[1] + m[0]/m[1]/60 + s[0]/s[1]/3600
    try:
        lat = convert(gps_info["GPSLatitude"])
        if gps_info["GPSLatitudeRef"] != "N":
            lat = -lat
        lon = convert(gps_info["GPSLongitude"])
        if gps_info["GPSLongitudeRef"] != "E":
            lon = -lon
        return lat, lon
    except:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    data = {}
    if request.method == 'POST':
        input_type = request.form.get('type')
        query = request.form.get('query')

        if input_type == 'username':
            data['type'] = 'username'
            data['results'] = check_username(query)

        elif input_type == 'email':
            data['type'] = 'email'
            data['email'] = query
            data['valid'] = "@" in query and "." in query.split("@")[-1]

        elif input_type == 'ip':
            data['type'] = 'ip'
            data['info'] = get_ip_info(query)

        elif input_type == 'domain':
            data['type'] = 'domain'
            data['whois'] = get_whois(query)
            data['dns'] = get_dns(query)

        elif input_type == 'photo':
            file = request.files['photo']
            if file:
                filename = secure_filename(file.filename)
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                exif = get_exif(path)
                coords = extract_coords(exif)
                data = {
                    "type": "photo",
                    "filename": filename,
                    "exif": exif,
                    "coords": coords
                }

        # Сохраняем результат в .html
        html_result = render_template("result_template.html", data=data)
        result_filename = f"result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(f"static/{result_filename}", "w", encoding="utf-8") as f:
            f.write(html_result)
        data["html_filename"] = result_filename

    return render_template("index.html", data=data)

@app.route("/download/<filename>")
def download(filename):
    return send_file(f"static/{filename}", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
