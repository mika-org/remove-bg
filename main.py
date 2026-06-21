import io
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Response, Form, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from PIL import Image

# Set U2NET_HOME to the project's local .u2net folder
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ["U2NET_HOME"] = os.path.join(current_dir, ".u2net")

import rembg

# Create a global session with the lightweight u2netp model
rembg_session = rembg.new_session("u2netp")

app = FastAPI(
    title="Background Removal API",
    description="A free, offline background removal API powered by Python and rembg.",
    version="1.0.0"
)

# Enable CORS for easy cross-origin integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    """
    Remove background from an image.
    Accepts any image format (PNG, JPEG, etc.) and returns a transparent PNG.
    """
    import os
    content_type = file.content_type
    filename = file.filename or ""
    _, ext = os.path.splitext(filename.lower())
    
    is_image = False
    if content_type and content_type.startswith("image/"):
        is_image = True
    elif ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}:
        is_image = True

    if not is_image:
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    try:
        # Read uploaded image bytes
        input_bytes = await file.read()
        
        # Remove background using rembg with the preloaded session
        output_bytes = rembg.remove(input_bytes, session=rembg_session)
        
        # Return the processed image bytes as PNG
        return Response(content=output_bytes, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.api_route("/remove-bg-url", methods=["GET", "POST"])
async def remove_background_from_url(url: str, authorization: str = Header(None)):
    """
    Remove background from an image URL.
    Fetches the image from the provided URL (via GET or POST) and returns a transparent PNG.
    """
    import requests
    if not url:
        raise HTTPException(status_code=400, detail="Missing 'url' query parameter.")
        
    try:
        # Fetch the image from the URL, forwarding the authorization token if present
        headers = {}
        if authorization:
            headers["Authorization"] = authorization
            
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch image from URL. Status code: {response.status_code}"
            )
        
        # Check content type if available
        content_type = response.headers.get("content-type", "")
        if content_type and not content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="URL does not point to a valid image."
            )
            
        input_bytes = response.content
        
        # Remove background using rembg with the preloaded session
        output_bytes = rembg.remove(input_bytes, session=rembg_session)
        
        # Return the processed image bytes as PNG
        return Response(content=output_bytes, media_type="image/png")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Request to fetch image failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def index():
    """
    Stunning web interface for testing the background removal API.
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Magic Bg Remover - Free Python API</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg-primary: #0a0b10;
                --bg-secondary: #12131a;
                --accent-primary: #6366f1;
                --accent-secondary: #a855f7;
                --text-primary: #f8fafc;
                --text-secondary: #94a3b8;
                --border-color: #27273a;
                --success: #10b981;
            }

            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            body {
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: var(--bg-primary);
                color: var(--text-primary);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                overflow-x: hidden;
            }

            /* Glowing radial background spots */
            .glow-bg-1 {
                position: absolute;
                top: -10%;
                left: -10%;
                width: 50%;
                height: 50%;
                background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(0,0,0,0) 70%);
                z-index: -1;
                pointer-events: none;
            }

            .glow-bg-2 {
                position: absolute;
                bottom: -10%;
                right: -10%;
                width: 50%;
                height: 50%;
                background: radial-gradient(circle, rgba(168, 85, 247, 0.15) 0%, rgba(0,0,0,0) 70%);
                z-index: -1;
                pointer-events: none;
            }

            header {
                padding: 2rem 4rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border-color);
                backdrop-filter: blur(10px);
                position: sticky;
                top: 0;
                z-index: 100;
                background: rgba(10, 11, 16, 0.7);
            }

            .logo {
                font-size: 1.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .api-docs-btn {
                background-color: transparent;
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                padding: 0.6rem 1.2rem;
                border-radius: 50px;
                font-weight: 600;
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }

            .api-docs-btn:hover {
                border-color: var(--accent-primary);
                box-shadow: 0 0 15px rgba(99, 102, 241, 0.3);
                transform: translateY(-2px);
            }

            main {
                flex-grow: 1;
                max-width: 1200px;
                width: 100%;
                margin: 0 auto;
                padding: 3rem 2rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 3rem;
            }

            .hero-section {
                text-align: center;
                max-width: 700px;
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }

            .hero-section h1 {
                font-size: 3rem;
                font-weight: 800;
                line-height: 1.2;
                letter-spacing: -1px;
            }

            .hero-section h1 span {
                background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .hero-section p {
                font-size: 1.1rem;
                color: var(--text-secondary);
                line-height: 1.6;
            }

            .workspace {
                width: 100%;
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: 24px;
                padding: 2.5rem;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(20px);
                position: relative;
                overflow: hidden;
            }

            .dropzone {
                border: 2px dashed var(--border-color);
                border-radius: 16px;
                padding: 4rem 2rem;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.01);
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 1.5rem;
            }

            .dropzone.dragover {
                border-color: var(--accent-primary);
                background: rgba(99, 102, 241, 0.05);
                transform: scale(0.99);
            }

            .upload-icon {
                width: 64px;
                height: 64px;
                border-radius: 50%;
                background: rgba(99, 102, 241, 0.1);
                display: flex;
                align-items: center;
                justify-content: center;
                color: var(--accent-primary);
                transition: all 0.3s ease;
            }

            .dropzone:hover .upload-icon {
                background: var(--accent-primary);
                color: var(--text-primary);
                transform: translateY(-5px) scale(1.05);
                box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);
            }

            .dropzone h3 {
                font-size: 1.3rem;
                font-weight: 600;
            }

            .dropzone p {
                font-size: 0.9rem;
                color: var(--text-secondary);
            }

            .file-input {
                display: none;
            }

            /* Preview & Comparison Layout */
            .preview-container {
                display: none;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
                width: 100%;
            }

            @media (max-width: 768px) {
                .preview-container {
                    grid-template-columns: 1fr;
                }
                header {
                    padding: 1.5rem;
                }
                .hero-section h1 {
                    font-size: 2.2rem;
                }
            }

            .image-box {
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 1rem;
                display: flex;
                flex-direction: column;
                gap: 1rem;
                align-items: center;
                position: relative;
            }

            .image-box h4 {
                font-size: 1rem;
                font-weight: 600;
                color: var(--text-secondary);
                width: 100%;
                text-align: left;
                padding-bottom: 0.5rem;
                border-bottom: 1px solid var(--border-color);
            }

            .img-wrapper {
                width: 100%;
                height: 350px;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                border-radius: 10px;
                position: relative;
            }

            /* Checkerboard background for transparency preview */
            .img-wrapper.transparent {
                background-color: #e5e5e5;
                background-image: 
                    linear-gradient(45deg, #ccc 25%, transparent 25%), 
                    linear-gradient(-45deg, #ccc 25%, transparent 25%), 
                    linear-gradient(45deg, transparent 75%, #ccc 75%), 
                    linear-gradient(-45deg, transparent 75%, #ccc 75%);
                background-size: 20px 20px;
                background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
            }

            .img-wrapper img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                border-radius: 8px;
            }

            /* Loading spinner overlay */
            .loader-overlay {
                position: absolute;
                inset: 0;
                background: rgba(18, 19, 26, 0.8);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 1rem;
                border-radius: 16px;
                z-index: 10;
                display: none;
            }

            .spinner {
                width: 50px;
                height: 50px;
                border: 3px solid rgba(99, 102, 241, 0.1);
                border-radius: 50%;
                border-top-color: var(--accent-primary);
                animation: spin 1s ease-in-out infinite;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            /* Action Buttons */
            .action-buttons {
                display: flex;
                gap: 1rem;
                width: 100%;
                justify-content: flex-end;
                margin-top: 1.5rem;
            }

            .btn {
                padding: 0.8rem 1.8rem;
                border-radius: 50px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.95rem;
                border: none;
            }

            .btn-primary {
                background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
                color: var(--text-primary);
                box-shadow: 0 10px 20px rgba(99, 102, 241, 0.2);
            }

            .btn-primary:hover {
                box-shadow: 0 10px 25px rgba(99, 102, 241, 0.4);
                transform: translateY(-2px);
            }

            .btn-secondary {
                background: transparent;
                border: 1px solid var(--border-color);
                color: var(--text-primary);
            }

            .btn-secondary:hover {
                border-color: var(--text-secondary);
                transform: translateY(-2px);
            }

            footer {
                padding: 2rem;
                text-align: center;
                border-top: 1px solid var(--border-color);
                color: var(--text-secondary);
                font-size: 0.9rem;
            }

            footer a {
                color: var(--accent-primary);
                text-decoration: none;
            }

            footer a:hover {
                text-decoration: underline;
            }

            /* Tabs */
            .tabs {
                display: flex;
                gap: 1rem;
                margin-bottom: 1.5rem;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 0.5rem;
                width: 100%;
            }

            .tab {
                padding: 0.5rem 1rem;
                cursor: pointer;
                font-weight: 600;
                color: var(--text-secondary);
                transition: all 0.3s ease;
                border-bottom: 2px solid transparent;
            }

            .tab.active {
                color: var(--accent-primary);
                border-bottom-color: var(--accent-primary);
            }

            .tab:hover {
                color: var(--text-primary);
            }

            /* URL Input Mode */
            .url-input-container {
                display: none;
                flex-direction: column;
                gap: 1rem;
                padding: 2.5rem 1rem;
                align-items: center;
                width: 100%;
                border: 2px dashed var(--border-color);
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.01);
            }

            .url-input-wrapper {
                display: flex;
                width: 100%;
                max-width: 600px;
                gap: 0.5rem;
            }

            .url-input {
                flex-grow: 1;
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid var(--border-color);
                border-radius: 50px;
                padding: 0.8rem 1.5rem;
                color: var(--text-primary);
                font-family: inherit;
                font-size: 0.95rem;
                outline: none;
                transition: all 0.3s ease;
            }

            .url-input:focus {
                border-color: var(--accent-primary);
                box-shadow: 0 0 10px rgba(99, 102, 241, 0.2);
            }

            .url-help {
                font-size: 0.85rem;
                color: var(--text-secondary);
            }

            /* API Docs */
            .docs-section {
                width: 100%;
                max-width: 1200px;
                margin-top: 4rem;
                border-top: 1px solid var(--border-color);
                padding-top: 3rem;
            }

            .docs-section h2 {
                font-size: 2rem;
                margin-bottom: 2rem;
                font-weight: 800;
                background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .docs-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
            }

            @media (max-width: 768px) {
                .docs-grid {
                    grid-template-columns: 1fr;
                }
            }

            .doc-card {
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 1.5rem;
                display: flex;
                flex-direction: column;
                gap: 0.8rem;
            }

            .doc-card h3 {
                font-size: 1.2rem;
                font-weight: 700;
            }

            .doc-card p {
                color: var(--text-secondary);
                font-size: 0.9rem;
                line-height: 1.5;
            }

            .badge {
                padding: 0.25rem 0.6rem;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 700;
                display: inline-block;
                align-self: flex-start;
            }

            .badge-post {
                background: rgba(16, 185, 129, 0.1);
                color: var(--success);
                border: 1px solid rgba(16, 185, 129, 0.2);
            }

            .badge-get {
                background: rgba(99, 102, 241, 0.1);
                color: var(--accent-primary);
                border: 1px solid rgba(99, 102, 241, 0.2);
            }

            .doc-card code {
                background: rgba(0, 0, 0, 0.3);
                padding: 0.2rem 0.5rem;
                border-radius: 6px;
                font-family: monospace;
                font-size: 0.95rem;
                color: var(--text-primary);
                word-break: break-all;
            }

            .doc-card h4 {
                font-size: 0.85rem;
                text-transform: uppercase;
                color: var(--text-secondary);
                margin-top: 0.5rem;
                font-weight: 600;
            }

            .doc-card pre {
                background: rgba(0, 0, 0, 0.3);
                padding: 0.8rem;
                border-radius: 8px;
                font-family: monospace;
                font-size: 0.85rem;
                overflow-x: auto;
                color: #e2e8f0;
                border: 1px solid var(--border-color);
            }
        </style>
    </head>
    <body>
        <div class="glow-bg-1"></div>
        <div class="glow-bg-2"></div>

        <header>
            <div class="logo">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>
                Magic Bg Remover
            </div>
            <a href="/docs" target="_blank" class="api-docs-btn">
                API Docs
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            </a>
        </header>

        <main>
            <div class="hero-section">
                <h1>Remove Image Backgrounds <span>Instantly</span></h1>
                <p>Free, fast, and secure background removal service powered entirely locally by Python & Deep Learning.</p>
            </div>

            <div class="workspace">
                <div class="tabs">
                    <div class="tab active" id="tabUpload">Upload File</div>
                    <div class="tab" id="tabUrl">Image URL</div>
                </div>

                <div class="loader-overlay" id="loader">
                    <div class="spinner"></div>
                    <p style="font-weight: 600;">Removing background... (Takes ~10s for the first image to load AI model)</p>
                </div>

                <div class="dropzone" id="dropzone">
                    <div class="upload-icon">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    </div>
                    <div>
                        <h3>Drag & drop your image here</h3>
                        <p>Supports PNG, JPG, JPEG, WEBP</p>
                    </div>
                    <button class="btn btn-primary" onclick="document.getElementById('fileInput').click()">Browse Files</button>
                    <input type="file" id="fileInput" class="file-input" accept="image/*">
                 </div>

                <div class="url-input-container" id="urlInputContainer">
                    <div class="url-input-wrapper">
                        <input type="text" id="imageUrlInput" placeholder="https://example.com/image.jpg" class="url-input">
                        <button class="btn btn-primary" id="btnProcessUrl">Process URL</button>
                    </div>
                    <p class="url-help">Provide a direct link to any image (JPEG, PNG, WEBP).</p>
                </div>

                <div class="preview-container" id="previewContainer">
                    <div class="image-box">
                        <h4>Original Image</h4>
                        <div class="img-wrapper">
                            <img id="originalImg" src="" alt="Original">
                        </div>
                    </div>
                    <div class="image-box">
                        <h4>Removed Background</h4>
                        <div class="img-wrapper transparent">
                            <img id="resultImg" src="" alt="Result">
                        </div>
                    </div>
                </div>

                <div class="action-buttons" id="actionButtons" style="display: none;">
                    <button class="btn btn-secondary" id="resetBtn">Upload Another</button>
                    <button class="btn btn-primary" id="downloadBtn">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Download Result
                    </button>
                </div>
            </div>

            <!-- API Docs Section -->
            <div class="docs-section">
                <h2>API Documentation</h2>
                <div class="docs-grid">
                    <div class="doc-card">
                        <h3>1. Remove Background (File Upload)</h3>
                        <div>
                            <span class="badge badge-post">POST</span>
                            <code>/remove-bg</code>
                        </div>
                        <p>Upload a local image file and receive a transparent background-removed PNG.</p>
                        <h4>Request Body (multipart/form-data):</h4>
                        <pre>file: [Binary File]</pre>
                        <h4>Example curl:</h4>
                        <pre>curl -X POST -F "file=@photo.jpg" http://[your-domain]/remove-bg --output result.png</pre>
                    </div>
                    <div class="doc-card">
                        <h3>2. Remove Background (From URL)</h3>
                        <div>
                            <span class="badge badge-get">GET</span>
                            <span class="badge badge-post">POST</span>
                            <code>/remove-bg-url</code>
                        </div>
                        <p>Download an image from a URL and remove its background, returning a transparent PNG.</p>
                        <h4>Query Parameters:</h4>
                        <pre>url: [Encoded Image URL]</pre>
                        <h4>Example curl:</h4>
                        <pre>curl "http://[your-domain]/remove-bg-url?url=https://example.com/photo.jpg" --output result.png</pre>
                    </div>
                </div>
            </div>
        </main>

        <footer>
            <p>Created with Python, FastAPI, and rembg. View <a href="/docs" target="_blank">API documentation</a>.</p>
        </footer>

        <script>
            const dropzone = document.getElementById('dropzone');
            const fileInput = document.getElementById('fileInput');
            const previewContainer = document.getElementById('previewContainer');
            const originalImg = document.getElementById('originalImg');
            const resultImg = document.getElementById('resultImg');
            const actionButtons = document.getElementById('actionButtons');
            const resetBtn = document.getElementById('resetBtn');
            const downloadBtn = document.getElementById('downloadBtn');
            const loader = document.getElementById('loader');

            // New elements for URL input mode
            const tabUpload = document.getElementById('tabUpload');
            const tabUrl = document.getElementById('tabUrl');
            const urlInputContainer = document.getElementById('urlInputContainer');
            const imageUrlInput = document.getElementById('imageUrlInput');
            const btnProcessUrl = document.getElementById('btnProcessUrl');

            // Tab switching logic
            tabUpload.addEventListener('click', () => {
                tabUpload.classList.add('active');
                tabUrl.classList.remove('active');
                dropzone.style.display = 'flex';
                urlInputContainer.style.display = 'none';
                resetWorkspace();
            });

            tabUrl.addEventListener('click', () => {
                tabUrl.classList.add('active');
                tabUpload.classList.remove('active');
                dropzone.style.display = 'none';
                urlInputContainer.style.display = 'flex';
                resetWorkspace();
            });

            btnProcessUrl.addEventListener('click', () => {
                const url = imageUrlInput.value.trim();
                if (!url) {
                    alert('Please enter a valid image URL.');
                    return;
                }
                
                originalFileName = 'url_image.png';
                originalImg.src = url; // Display original from URL
                
                urlInputContainer.style.display = 'none';
                previewContainer.style.display = 'grid';
                
                removeBgFromUrl(url);
            });

            async function removeBgFromUrl(url) {
                loader.style.display = 'flex';
                
                try {
                    const response = await fetch('/remove-bg-url?url=' + encodeURIComponent(url));

                    if (!response.ok) {
                        const errText = await response.text();
                        throw new Error(errText || 'Failed to process image');
                    }

                    const blob = await response.blob();
                    processedImageUrl = URL.createObjectURL(blob);
                    resultImg.src = processedImageUrl;
                    
                    actionButtons.style.display = 'flex';
                } catch (error) {
                    console.error(error);
                    alert('An error occurred: ' + error.message);
                    resetWorkspace();
                } finally {
                    loader.style.display = 'none';
                }
            }

            let processedImageUrl = null;
            let originalFileName = 'image.png';

            // Drag and drop handlers
            ['dragenter', 'dragover'].forEach(eventName => {
                dropzone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    dropzone.classList.add('dragover');
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                dropzone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    dropzone.classList.remove('dragover');
                }, false);
            });

            dropzone.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                if (files.length > 0) {
                    processFile(files[0]);
                }
            });

            fileInput.addEventListener('change', (e) => {
                if (fileInput.files.length > 0) {
                    processFile(fileInput.files[0]);
                }
            });

            function processFile(file) {
                if (!file.type.startsWith('image/')) {
                    alert('Please upload an image file.');
                    return;
                }

                originalFileName = file.name;

                // Show original image preview
                const reader = new FileReader();
                reader.onload = (e) => {
                    originalImg.src = e.target.result;
                    dropzone.style.display = 'none';
                    previewContainer.style.display = 'grid';
                    uploadAndRemoveBg(file);
                };
                reader.readAsDataURL(file);
            }

            async function uploadAndRemoveBg(file) {
                loader.style.display = 'flex';
                
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/remove-bg', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error('Failed to process image');
                    }

                    const blob = await response.blob();
                    processedImageUrl = URL.createObjectURL(blob);
                    resultImg.src = processedImageUrl;
                    
                    actionButtons.style.display = 'flex';
                } catch (error) {
                    console.error(error);
                    alert('An error occurred during background removal: ' + error.message);
                    resetWorkspace();
                } finally {
                    loader.style.display = 'none';
                }
            }

            function resetWorkspace() {
                previewContainer.style.display = 'none';
                actionButtons.style.display = 'none';
                fileInput.value = '';
                imageUrlInput.value = '';
                originalImg.src = '';
                resultImg.src = '';
                
                if (tabUpload.classList.contains('active')) {
                    dropzone.style.display = 'flex';
                    urlInputContainer.style.display = 'none';
                } else {
                    dropzone.style.display = 'none';
                    urlInputContainer.style.display = 'flex';
                }

                if (processedImageUrl) {
                    URL.revokeObjectURL(processedImageUrl);
                    processedImageUrl = null;
                }
            }

            resetBtn.addEventListener('click', resetWorkspace);

            downloadBtn.addEventListener('click', () => {
                if (processedImageUrl) {
                    const a = document.createElement('a');
                    a.href = processedImageUrl;
                    // Prepend "no-bg-" to original filename or use png format
                    const nameParts = originalFileName.split('.');
                    if (nameParts.length > 1) {
                        nameParts.pop();
                    }
                    a.download = nameParts.join('.') + '_nobg.png';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content
