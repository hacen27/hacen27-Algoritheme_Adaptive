import base64
from io import BytesIO
from flask import Flask, flash, request, redirect, url_for, render_template
from statistics import mode
from warnings import filters

from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt 

import cv2
import numpy as np
from sklearn.cluster import KMeans

import os

from PIL import Image



 
app = Flask(__name__)
 
UPLOAD_FOLDER = 'static/uploads/'
 
app.secret_key = "cairocoders-ednalan"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
 
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
     
 
@app.route('/')
def home():
    return render_template('index.html')


def imageSegmentor(image_path,n_clusters=3,threshold=0):
    
    # Load image
    # image_path = "/content/drive/MyDrive/face_images/abdellahi.jpg"
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    print(image)
    # Define a threshold
    # threshold = 100  # This threshold can be adjusted depending on the specific area and intensity desired
    image = image.astype(np.uint8)
    # Apply threshold to get the pixels we are interested in
    mask = image > int(threshold)

    # We use the mask to select the region of interest
    selected_pixels = image[mask].reshape(-1, 1)

    # Apply K-means clustering to the sthresholdelected pixels
    kmeans = KMeans(n_clusters=int(n_clusters), random_state=42)
    kmeans.fit(selected_pixels)

    # Map the pixel labels back to the original image shape
    segmented_image = np.zeros(image.shape, dtype=np.uint8)
    segmented_image[mask] = kmeans.labels_
    
    # # Encode the segmented image as a JPEG
    # _, encoded_image = cv2.imencode('.jpg', segmented_image)

    # # Convert the encoded image to a base64 string
    # base64_string = base64.b64encode(encoded_image).decode('utf-8')
    # Display the original and the segmented image
    # Create figure and axes for the segmented image
    fig, ax = plt.subplots(figsize=(10, 5))

    # Display the segmented image
    ax.imshow(segmented_image, cmap='gray')
    ax.set_title('Segmented Image')
    ax.axis('off')

    # Use plt.tight_layout() before saving the figure to ensure everything fits without overlapping
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)

    # Encode the image in the buffer to Base64
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    # You can now embed 'image_base64' in an HTML image tag as follows:
    # <img src="data:image/png;base64,{{image_base64}}" />

    # Don't forget to close the buffer and clear the figure to free up memory
    buf.close()
    plt.close(fig)

    return image_base64



 
@app.route('/', methods=['POST'])
def upload_image():
    if 'files[]' not in request.files:
        flash('No file part')
        return redirect(request.url)

    files = request.files.getlist('files[]')
    clustering = request.form.get('clustering')
    threshold = request.form.get('vol')

    file_names=[] 
    for file in files:   
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_names.append(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) 
            
            img = Image.open("static/uploads/"+ filename)
            # if img.width > 190 or img.height > 150:
            #     output_size = (190, 150)
            #     img.thumbnail(output_size)
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print('img',img.getdata())
          
        else:
            flash('Mettre un image de types  - png, jpg, jpeg, gif')
            return redirect(request.url)

    flash('Image est charger avec succes')
    
    # flash(f'Clastring et Vol',clustering + threshold)
    # Zipp=zip(file_names,clustering,threshold)
    
    image_path = os.path.join('static/uploads/', file_names[0])
    print(image_path)
    image_base64_string = imageSegmentor(image_path,clustering,threshold)
    # print(image_base64_string)
    context = {
        "n_clusters" : clustering,
        "threshold" : threshold,
        "origine_image_path" : image_path,
        "segmented_image_base64_string" : image_base64_string
    }
    
    return render_template('index.html', RESULTAT=context )

@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

if __name__ == "__main__":
   app.run(debug=True)