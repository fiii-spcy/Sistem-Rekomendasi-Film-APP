"""
Vercel serverless function entry point.
This creates a simple HTTP handler for the Streamlit app.

Note: For best results with Streamlit, consider using Streamlit Cloud instead.
"""
import os
import sys

# Ensure we can import the app
sys.path.insert(0, os.path.dirname(__file__))

def handler(request):
    """
    Vercel serverless function handler.
    Attempts to run Streamlit in a serverless-compatible way.
    """
    try:
        # For Vercel, we'll redirect to Streamlit Cloud or provide instructions
        # Streamlit requires a persistent server which doesn't work well with serverless
        
        html_content = """
        <!DOCTYPE html>
        <html lang="id">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sistem Klasifikasi Film</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #0d1b2a;
                    color: #e0e0e0;
                }
                .container {
                    background: #1b263b;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                }
                h1 { color: #00d4ff; }
                .info { 
                    background: #0d1b2a;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .button {
                    display: inline-block;
                    padding: 12px 24px;
                    background: #00d4ff;
                    color: #0d1b2a;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 10px 5px;
                }
                .button:hover {
                    background: #00ff88;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎬 Sistem Klasifikasi & Pencarian Film</h1>
                <div class="info">
                    <h3>⚠️ Catatan Deployment</h3>
                    <p>Streamlit memerlukan server yang berjalan secara persisten, sehingga tidak ideal untuk Vercel's serverless functions.</p>
                    <p><strong>Rekomendasi:</strong> Gunakan Streamlit Cloud untuk deployment yang optimal.</p>
                </div>
                <h3>Opsi Deployment:</h3>
                <ul>
                    <li><strong>Streamlit Cloud</strong> (Gratis & Mudah) - https://streamlit.io/cloud</li>
                    <li><strong>Railway</strong> - https://railway.app</li>
                    <li><strong>Render</strong> - https://render.com</li>
                </ul>
                <h3>Untuk Menjalankan Lokal:</h3>
                <code>streamlit run api/app.py</code>
            </div>
        </body>
        </html>
        """
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html; charset=utf-8',
            },
            'body': html_content
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/plain',
            },
            'body': f'Error: {str(e)}'
        }

# Vercel expects this function name
def app(request):
    return handler(request)
