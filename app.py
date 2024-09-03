from flask import Flask, render_template, request, send_file
from PIL import Image
import io
import time
import uuid

app = Flask(__name__)

def process_image(image_file):
    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format
        
        # Optionally resize the image to a smaller dimension (e.g., max width/height = 1024)
        max_dimension = 1024
        if max(image.size) > max_dimension:
            ratio = max_dimension / float(max(image.size))
            new_size = tuple([int(x * ratio) for x in image.size])
            image = image.resize(new_size, Image.ANTIALIAS)

        # Compress the image
        img_io = io.BytesIO()
        image.save(img_io, format=img_format, optimize=True, quality=50)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return img_io, img_format, unique_filename
    except Exception as e:
        raise e

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image-compression')
def image_compression():
    return render_template('compress_en.html')

@app.route('/compress-image', methods=['POST'])
def compress_image():
    if 'image' not in request.files:
        return "No image file provided", 400

    image_file = request.files['image']
    if image_file.filename == '':
        return "No selected file", 400

    try:
        img_io, img_format, unique_filename = process_image(image_file)
        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return str(e), 500

@app.route('/image-rotate')
def image_rotate():
    return render_template('rotate_en.html')

@app.route('/rotate-image', methods=['POST'])
def rotate_image():
    if 'image' not in request.files:
        return "No image file provided", 400

    image_file = request.files['image']
    if image_file.filename == '':
        return "No selected file", 400

    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format

        # Get rotation angle from form data
        rotation = int(request.form.get('rotation', 0))

        # Rotate the image
        rotated_image = image.rotate(-rotation, expand=True)

        # Save the rotated image
        img_io = io.BytesIO()
        rotated_image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"rotated_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return str(e), 500

# Consolidate static page routes
static_pages = [
    'image-resize', 'image-crop', 'convert-image-format', 'image-effects',
    'image-upscale', 'html-to-image', 'image-watermarking', 'about', 'contact-us', 'help',
    'faq', 'media', 'legal', 'blogs', 'our-story', 'team', 'features', 'pricing', 'languages', 'tools'
]

for page in static_pages:
    app.add_url_rule(f'/{page}', page, lambda page=page: render_template('index.html'))

if __name__ == '__main__':
    app.run(debug=True)
