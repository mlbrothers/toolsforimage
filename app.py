from flask import Flask, render_template, request, send_file, jsonify, session, abort
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont
from html2image import Html2Image
import io
import time
import uuid
import os
import tempfile
import numpy as np
import json
import cv2
import base64

app = Flask(__name__)
hti = Html2Image()

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
            image = image.resize(new_size, Image.LANCZOS)

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
        return render_template('error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template('error.html', error="No selected file"), 400

    try:
        img_io, img_format, unique_filename = process_image(image_file)
        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/image-rotate')
def image_rotate():
    return render_template('rotate_en.html')

@app.route('/rotate-image', methods=['POST'])
def rotate_image():
    if 'image' not in request.files:
        return render_template('error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template('error.html', error="No selected file"), 400

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
        return render_template('error.html', error=str(e)), 500

@app.route('/image-crop')
def image_crop():
    return render_template('crop_en.html')

@app.route('/crop-image', methods=['POST'])
def crop_image():
    if 'image' not in request.files:
        return render_template('error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template('error.html', error="No selected file"), 400

    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format

        # Get crop dimensions from form data
        x = int(request.form.get('crop-x', 0))
        y = int(request.form.get('crop-y', 0))
        width = int(request.form.get('crop-width', 0))
        height = int(request.form.get('crop-height', 0))

        # Crop the image
        cropped_image = image.crop((x, y, x + width, y + height))

        # Save the cropped image
        img_io = io.BytesIO()
        cropped_image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"cropped_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/html-to-image')
def url_to_image():
    return render_template('html_to_image_en.html')

@app.route('/convert-url-to-image', methods=['POST'])
def convert_url_to_image():
    url = request.form.get('url')
    if not url:
        return render_template('error.html', error="No URL provided"), 400

    try:
        # Generate a unique filename for download purposes
        unique_filename = f"webpage_{uuid.uuid4().hex}_{int(time.time())}.png"

        # Create a BytesIO object to store the image in memory
        img_io = io.BytesIO()

        # Convert URL to image directly into BytesIO using Html2Image
        hti = Html2Image(
            output_path='.'
        )
        
        # Adding headless Chrome options to avoid dbus and GPU errors
        hti.screenshot(
            url=url, 
            save_as=unique_filename
        )
        
        # Write the generated image file to BytesIO
        with open(unique_filename, 'rb') as f:
            img_io.write(f.read())
        
        # Remove the temporary file after reading it
        os.remove(unique_filename)

        # Reset the pointer to the start of the BytesIO object
        img_io.seek(0)
        
        # Send the image directly from BytesIO
        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=unique_filename
        )

    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/image-resize')
def image_resize():
    return render_template('resize_en.html')

@app.route('/resize-image', methods=['POST'])
def resize_image():
    if 'image' not in request.files:
        return render_template('error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template('error.html', error="No selected file"), 400

    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format

        # Get resize dimensions and type from form data
        width = int(request.form.get('width', 0))
        height = int(request.form.get('height', 0))
        resize_type = request.form.get('resizeType', 'pixel')

        # Resize the image
        if resize_type == 'percentage':
            width = int(image.width * (width / 100))
            height = int(image.height * (height / 100))

        resized_image = image.resize((width, height), Image.LANCZOS)

        # Save the resized image
        img_io = io.BytesIO()
        resized_image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"resized_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/image-effects')
def image_effects():
    return render_template('image_effects_en.html')

@app.route('/apply-effects', methods=['POST'])
def apply_effects():
    if 'image' not in request.files:
        return render_template('error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template('error.html', error="No selected file"), 400

    try:
        # Open the image file
        image = Image.open(image_file)
        img_format = image.format

        # Get all active effects from the form data
        active_effects = request.form.get('effect', '').split(',')
        print(active_effects)
        # Apply all active effects
        if 'grayscale' in active_effects:
            image = image.convert('L').convert('RGB')
        
        if 'blur' in active_effects:
            image = image.filter(ImageFilter.GaussianBlur(radius=5))
        
        if 'sharpen' in active_effects:
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
        
        if 'sepia' in active_effects:
            sepia_matrix = [
                0.393, 0.769, 0.189, 0,
                0.349, 0.686, 0.168, 0,
                0.272, 0.534, 0.131, 0
            ]
            image = image.convert('RGB', matrix=sepia_matrix)
        
        if 'invert' in active_effects:
            if image.mode == 'RGBA':
                r, g, b, a = image.split()
                rgb_image = Image.merge('RGB', (r, g, b))
                inverted_image = ImageOps.invert(rgb_image)
                r2, g2, b2 = inverted_image.split()
                image = Image.merge('RGBA', (r2, g2, b2, a))
            else:
                image = ImageOps.invert(image)
        
        if 'brightness' in active_effects:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.5)
        
        if 'contrast' in active_effects:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
        
        if 'saturation' in active_effects:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(1.5)

        # Save the edited image
        img_io = io.BytesIO()
        image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        effects_applied = '_'.join(active_effects) if active_effects else 'no_effect'
        unique_filename = f"{effects_applied}_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/convert-image-format')
def convert_image_format():
    return render_template('convert_en.html')

@app.route('/convert-image', methods=['POST'])
def convert_image():
    if 'image' not in request.files:
        return render_template('error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template('error.html', error="No selected file"), 400

    output_format = request.form.get('output_format', 'png').lower()

    try:
        # Open the image file
        image = Image.open(image_file)

        # Convert the image
        img_io = io.BytesIO()
        image.save(img_io, format=output_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"converted_{uuid.uuid4().hex}_{int(time.time())}.{output_format}"

        return send_file(img_io, mimetype=f'image/{output_format}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/image-watermarking')
def image_watermarking():
    return render_template('watermark_en.html')

@app.route('/watermark-image', methods=['POST'])
def watermark_image():
    if 'image' not in request.files:
        return render_template('error.html', error="No image file provided"), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return render_template('error.html', error="No selected file"), 400

    try:
        # Open the image file
        image = Image.open(image_file).convert('RGBA')
        img_format = image.format or 'PNG'  # Default to PNG if format is not detected

        # Get watermark data from form with default values
        watermark_data = json.loads(request.form.get('watermark-data', '{}'))
        print(watermark_data)
        default_data = {
            'text': 'Watermark',
            'fontSize': 24,
            'fontFamily': 'arial.ttf',
            'color': '#000000',
            'opacity': 0.5,
            'x': '50%',
            'y': '50%'
        }
        watermark_data = {**default_data, **watermark_data}
        print(watermark_data)
        # Create a transparent overlay image
        overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))

        # Set font
        try:
            font = ImageFont.truetype(watermark_data['fontFamily'], watermark_data['fontSize'])
        except IOError:
            font = ImageFont.load_default()

        # Create drawing object
        draw = ImageDraw.Draw(overlay)

        # Convert color from hex to RGBA
        color = tuple(int(watermark_data['color'].lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        opacity = int(float(watermark_data['opacity']) * 255)
        color_with_alpha = color + (opacity,)

        # Calculate text size
        text_bbox = draw.textbbox((0, 0), watermark_data['text'], font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Calculate position
        x = watermark_data['x']
        y = watermark_data['y']
        
        if isinstance(x, str) and x.endswith('%'):
            x = int(image.width * float(x.rstrip('%')) / 100) - text_width // 2
        else:
            x = int(x)

        if isinstance(y, str) and y.endswith('%'):
            y = int(image.height * float(y.rstrip('%')) / 100) - text_height // 2
        else:
            y = int(y)

        # Draw watermark on the overlay
        draw.text((x, y), watermark_data['text'], font=font, fill=color_with_alpha)

        # Combine the original image with the overlay
        watermarked_image = Image.alpha_composite(image, overlay)

        # Save the watermarked image
        img_io = io.BytesIO()
        watermarked_image.convert('RGB').save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"watermarked_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route('/blur-face')
def image_blur():
    return render_template('blur_en.html')

@app.route('/apply-blur', methods=['POST'])
def apply_blur():
    try:
        # Get blur data from the request
        blur_data = request.json
        # Get the image data from the request
        image_data = blur_data.get('image')
        if not image_data:
            return render_template('error.html', error="No image data provided"), 400

        # Strip base64 prefix if present and decode
        try:
            base64_data = image_data.split(',')[1] if ',' in image_data else image_data
            image = Image.open(io.BytesIO(base64.b64decode(base64_data)))
        except Exception as decode_err:
            return render_template('error.html', error=f"Error decoding base64 image data: {str(decode_err)}"), 500
        
        # Check the format of the image
        img_format = image.format or 'PNG'  # Default to PNG if format is not detected

        # Calculate blur coordinates
        x = int(blur_data['x'] * image.width)
        y = int(blur_data['y'] * image.height)
        width = int(blur_data['width'] * image.width)
        height = int(blur_data['height'] * image.height)

        # Ensure the region to blur is within the image boundaries
        x = max(0, min(x, image.width - 1))
        y = max(0, min(y, image.height - 1))
        width = max(1, min(width, image.width - x))
        height = max(1, min(height, image.height - y))

        # Convert PIL Image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Apply blur to the specified region
        roi = cv_image[y:y+height, x:x+width]
        if roi.size == 0:
            return render_template('error.html', error="Invalid blur region"), 400
        blurred_roi = cv2.GaussianBlur(roi, (157, 157), 0)
        cv_image[y:y+height, x:x+width] = blurred_roi

        # Convert back to PIL Image
        blurred_image = Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))

        # Save the image to a BytesIO stream
        img_io = io.BytesIO()
        blurred_image.save(img_io, format=img_format)
        img_io.seek(0)

        # Generate a unique filename
        unique_filename = f"blurred_{uuid.uuid4().hex}_{int(time.time())}.{img_format.lower()}"

        return send_file(img_io, mimetype=f'image/{img_format.lower()}', as_attachment=True, download_name=unique_filename)
    except Exception as e:
        print(f"Error in apply_blur function: {str(e)}")
        return render_template('error.html', error=str(e)), 500

# Consolidate static page routes
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/media')
def media():
    return render_template('media.html')

@app.route('/legal')
def legal():
    return render_template('legal.html')

@app.route('/blogs')
def blogs():
    return render_template('blogs.html')

@app.route('/our-story')
def our_story():
    return render_template('our_story.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/languages')
def languages():
    return render_template('languages.html')

@app.route('/tools')
def tools():
    return render_template('tools.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="404 - Page Not Found"), 404

if __name__ == '__main__':
    app.run(debug=True)
