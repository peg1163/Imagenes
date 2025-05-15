import tempfile
import os
from flask import Flask, request, redirect, send_file
from skimage import io
import base64
import glob
import numpy as np
import cv2
import uuid

app = Flask(__name__)

main_html = """
<html>
<head>
  <title>Dibujador de Letras</title>
</head>
<script>
  var mousePressed = false;
  var lastX, lastY;
  var ctx;

  function getRndLetter() {
    const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
    const randomIndex = Math.floor(Math.random() * letters.length);
    return letters[randomIndex];
  }

  function InitThis() {
    ctx = document.getElementById('myCanvas').getContext("2d");

    const letra = getRndLetter();
    const esMayuscula = letra === letra.toUpperCase();
    const tipo = esMayuscula ? "mayúscula" : "minúscula";
    const tipoCateg = "AEIOUaeiou".includes(letra) ? "vocal" : "consonante";

    document.getElementById('mensaje').innerHTML = `Dibuja la letra: <b>${letra}</b> (${tipo})`;

    document.getElementById('letra').value = letra;
    document.getElementById('mayus_minus').value = esMayuscula ? "mayus" : "minus";
    document.getElementById('vocal_consonante').value = tipoCateg;

    $('#myCanvas').mousedown(function (e) {
        mousePressed = true;
        Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
    });

    $('#myCanvas').mousemove(function (e) {
        if (mousePressed) {
            Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
        }
    });

    $('#myCanvas').mouseup(function (e) {
        mousePressed = false;
    });

    $('#myCanvas').mouseleave(function (e) {
        mousePressed = false;
    });
  }

  function Draw(x, y, isDown) {
    if (isDown) {
        ctx.beginPath();
        ctx.strokeStyle = 'black';
        ctx.lineWidth = 11;
        ctx.lineJoin = "round";
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.closePath();
        ctx.stroke();
    }
    lastX = x; lastY = y;
  }

  function clearArea() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  }

  function prepareImg() {
    const canvas = document.getElementById('myCanvas');
    document.getElementById('myImage').value = canvas.toDataURL();
  }
</script>
<body onload="InitThis();">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js"></script>
    <div align="left">
      <img src="https://upload.wikimedia.org/wikipedia/commons/f/f7/Uni-logo_transparente_granate.png" width="300"/>
    </div>
    <div align="center">
        <h1 id="mensaje">Dibujando...</h1>
        <canvas id="myCanvas" width="200" height="200" style="border:2px solid black"></canvas>
        <br/><br/>
        <button onclick="javascript:clearArea();return false;">Borrar</button>
    </div>
    <div align="center">
      <form method="post" action="/upload" onsubmit="prepareImg();" enctype="multipart/form-data">
        <input id="letra" name="letra" type="hidden" value="">
        <input id="mayus_minus" name="mayus_minus" type="hidden" value="">
        <input id="vocal_consonante" name="vocal_consonante" type="hidden" value="">
        <input id="myImage" name="myImage" type="hidden" value="">
        <input type="submit" value="Enviar">
      </form>
    </div>
</body>
</html>
"""

@app.route("/")
def main():
    return main_html

@app.route('/upload', methods=['POST'])
def upload():
    try:
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        letra = request.form.get('letra')
        mayus = request.form.get('mayus_minus')       # "mayus" o "minus"
        vocal = request.form.get('vocal_consonante')  # "vocal" o "consonante"

        os.makedirs("data", exist_ok=True)
        filename = f"data/img_{uuid.uuid4().hex}_{letra}_{vocal}_{mayus}.png"

        with open(filename, "wb") as f:
            f.write(base64.b64decode(img_data))

        print(f"Guardado: {filename}")

    except Exception as err:
        print("Error occurred")
        print(err)

    return redirect("/", code=302)

@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    vc_labels = []
    mm_labels = []

    filelist = glob.glob('data/*.png')
    for filepath in filelist:
        try:
            img = io.imread(filepath, as_gray=True)
            if img.shape != (200, 200):
                continue
            img = cv2.resize(img, (28, 28))
            images.append(img)

            parts = filepath.split('_')
            letra = parts[-3]
            vocal_consonante = parts[-2]
            mayus_minus = parts[-1].replace('.png', '')

            vc_labels.append(1 if vocal_consonante == "vocal" else 0)
            mm_labels.append(1 if mayus_minus == "mayus" else 0)
        except:
            continue

    X = np.expand_dims(np.array(images), -1)
    y_vc = np.array(vc_labels)
    y_mm = np.array(mm_labels)

    np.save('X.npy', X)
    np.save('y_vc.npy', y_vc)
    np.save('y_mm.npy', y_mm)

    return "Dataset generado y guardado (X.npy, y_vc.npy, y_mm.npy)"

@app.route('/X.npy')
def download_X(): return send_file('X.npy')

@app.route('/y_vc.npy')
def download_y_vc(): return send_file('y_vc.npy')

@app.route('/y_mm.npy')
def download_y_mm(): return send_file('y_mm.npy')

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    app.run(debug=True)
