<?php
// Spotify OAuth Callback Handler for Ansible for Spotify
// Place this at whatever web location you specify for the
// vale of redirect_uri in Ansible_for_Spotify.ini, as imported
// by Ansible_for_Spotify.py; e.g.:
// redirect_uri = https://your-site.com/ansible-spotify

// Get the current URL with all parameters
$protocol = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http';
$host = $_SERVER['HTTP_HOST'];
$uri = $_SERVER['REQUEST_URI'];
$current_url = $protocol . '://' . $host . $uri;

// Get the authorization code and any error from Spotify
$auth_code = isset($_GET['code']) ? $_GET['code'] : null;
$error = isset($_GET['error']) ? $_GET['error'] : null;

// Determine if this is a success or error
$is_success = $auth_code !== null && $error === null;
$has_error = $error !== null;

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Auth - Ansible for Spotify</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #191414;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: rgba(25, 20, 20, 0.95);
            max-width: 800px;
            width: 100%;
            padding: 40px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        h1 {
            color: white;
            font-size: 28px;
            margin-bottom: 8px;
        }
        .subtitle {
            color: #1DB954;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status {
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 25px;
            text-align: center;
        }
        .status.success {
            background: rgba(29, 185, 84, 0.15);
            border: 1px solid rgba(29, 185, 84, 0.3);
        }
        .status.error {
            background: rgba(255, 59, 48, 0.15);
            border: 1px solid rgba(255, 59, 48, 0.3);
        }
        .status-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        .status.success .status-title { color: #1DB954; }
        .status.error .status-title { color: #ff3b30; }
        .status-message {
            color: #b3b3b3;
            font-size: 14px;
        }
        .section {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .label {
            color: #999;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        .url-display {
            background: #0a0a0a;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            color: #ff9f1c;
            word-break: break-all;
            line-height: 1.5;
            border: 1px solid rgba(255, 255, 255, 0.05);
            user-select: all;
            cursor: text;
        }
        .instructions {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 3px solid #1DB954;
        }
        .instructions h3 {
            color: white;
            font-size: 14px;
            margin-bottom: 12px;
        }
        .instructions ol {
            color: #b3b3b3;
            font-size: 13px;
            line-height: 2;
            padding-left: 20px;
        }
        .instructions code {
            color: #ff9f1c;
            background: rgba(255, 255, 255, 0.05);
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            background: #1DB954;
            color: white;
            transition: all 0.2s;
            width: 100%;
            text-align: center;
        }
        .btn:hover {
            background: #1ed760;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
        }
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }
        .debug-section {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }
        .debug-section summary {
            color: #666;
            cursor: pointer;
            font-size: 12px;
        }
        .debug-content {
            color: #888;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 11px;
            line-height: 1.6;
            margin-top: 10px;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
        }
        .copy-notification {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            display: none;
            z-index: 1000;
        }
        .copy-notification.show {
            display: block;
            animation: fadeInUp 0.3s ease;
        }
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateX(-50%) translateY(20px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        .footer {
            margin-top: 25px;
            text-align: center;
            color: #555;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎵 Ansible for Spotify</h1>
            <div class="subtitle">Authentication Handler</div>
        </div>

        <?php if ($is_success): ?>
            <!-- SUCCESS STATE -->
            <div class="status success">
                <div class="status-title">✅ Authentication Successful!</div>
                <div class="status-message">Spotify has authorized this application.</div>
            </div>

            <!-- SHOW THE FULL URL - THIS IS WHAT THE SCRIPT EXPECTS -->
            <div class="section">
                <div class="label">📋 Copy this entire URL and paste it into your terminal:</div>
                <div class="url-display" id="fullUrl"><?php echo htmlspecialchars($current_url); ?></div>
                <div style="margin-top: 12px; font-size: 12px; color: #666;">
                    ⏱️ This URL contains the authorization code and expires in 60 seconds
                </div>
                <button class="btn" onclick="copyUrl()" style="margin-top: 12px;">
                    📋 Copy Full URL
                </button>
            </div>

            <div class="instructions">
                <h3>📝 What to do next:</h3>
                <ol>
                    <li>Click the <strong>"Copy Full URL"</strong> button above</li>
                    <li>Return to your terminal/command prompt</li>
                    <li>When the script asks <code>"Enter the URL you were redirected to:"</code></li>
                    <li><strong>Paste the entire URL</strong> and press Enter</li>
                    <li>The script will complete authentication</li>
                </ol>
            </div>

            <div style="margin-top: 12px; padding: 12px; background: rgba(255,159,28,0.1); border-radius: 6px; border-left: 3px solid #ff9f1c;">
                <div style="color: #ff9f1c; font-size: 13px;">
                    <strong>Note:</strong> The script expects the <strong>entire URL</strong>, not just the code.
                    <br>
                    Example: <code style="color: #fff;">http://earthbound.io/ansible-spotify/?code=AQB...xyz</code>
                </div>
            </div>

        <?php elseif ($has_error): ?>
            <!-- ERROR STATE -->
            <div class="status error">
                <div class="status-title">❌ Authentication Error</div>
                <div class="status-message">Error: <?php echo htmlspecialchars($error); ?></div>
            </div>

            <div style="background: rgba(255,59,48,0.05); padding: 16px; border-radius: 8px; border-left: 3px solid #ff3b30; margin-bottom: 20px;">
                <div style="color: #b3b3b3; font-size: 13px;">
                    <?php
                    $error_messages = [
                        'access_denied' => 'You denied access. Please try again and authorize the app.',
                        'invalid_request' => 'Invalid request. Check your app configuration.',
                        'invalid_client' => 'Invalid client ID. Check your INI file.',
                        'invalid_grant' => 'Authorization code is invalid or expired.',
                        'unauthorized_client' => 'App not authorized for this method.',
                        'invalid_scope' => 'Invalid scopes requested.',
                        'server_error' => 'Spotify internal server error. Try again later.',
                    ];
                    echo $error_messages[$error] ?? 'An unknown error occurred.';
                    ?>
                </div>
            </div>

            <div class="button-group">
                <a href="/ansible-spotify/" class="btn btn-secondary">🔄 Try Again</a>
            </div>

        <?php else: ?>
            <!-- NO CODE YET -->
            <div class="status" style="background: rgba(0, 122, 255, 0.15); border: 1px solid rgba(0, 122, 255, 0.3);">
                <div class="status-title" style="color: #007aff;">🔄 Waiting for Authorization</div>
                <div class="status-message">This page is ready to receive your Spotify authorization.</div>
            </div>

            <div style="background: rgba(255,255,255,0.03); padding: 16px; border-radius: 8px; margin: 20px 0;">
                <div style="color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    Current Configuration
                </div>
                <div style="color: #888; font-size: 13px; font-family: monospace;">
                    Redirect URI: <?php echo htmlspecialchars($current_url); ?>
                </div>
            </div>

            <div class="instructions">
                <h3>ℹ️ How this works:</h3>
                <ol>
                    <li>Run the Python script</li>
                    <li>Your browser will open to Spotify for authorization</li>
                    <li>After you authorize, you'll be redirected back here</li>
                    <li>This page will show the full URL to copy and paste back</li>
                </ol>
            </div>
        <?php endif; ?>

        <?php if (isset($auth_code) && $is_success): ?>
        <!-- Show the code too, in case they want it -->
        <div class="section" style="margin-top: 10px; background: rgba(0,0,0,0.2); border-color: rgba(255,255,255,0.03);">
            <div class="label" style="color: #666;">For reference: Authorization Code (optional)</div>
            <div style="font-family: monospace; font-size: 12px; color: #888; word-break: break-all;">
                <?php echo htmlspecialchars($auth_code); ?>
            </div>
            <div style="margin-top: 6px; font-size: 11px; color: #555;">
                (Only use this if your script specifically asks for the code)
            </div>
        </div>
        <?php endif; ?>

        <div class="footer">
            <p>Ansible for Spotify &bull; 
            <a href="https://developer.spotify.com/dashboard" target="_blank" style="color: #666;">Spotify Developer Dashboard</a>
            </p>
        </div>
    </div>

    <div id="copyNotification" class="copy-notification">✅ URL copied!</div>

    <script>
        function copyUrl() {
            const urlElement = document.getElementById('fullUrl');
            if (!urlElement) return;
            
            const url = urlElement.textContent.trim();
            if (!url || url.includes('Error')) {
                alert('No valid URL to copy!');
                return;
            }

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(() => {
                    showNotification('✅ URL copied to clipboard!');
                }).catch(() => {
                    fallbackCopy(url);
                });
            } else {
                fallbackCopy(url);
            }
        }

        function fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-9999px';
            textArea.style.top = '-9999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
                showNotification('✅ URL copied to clipboard!');
            } catch (err) {
                prompt('Copy this URL manually:', text);
            }
            document.body.removeChild(textArea);
        }

        function showNotification(message) {
            const notification = document.getElementById('copyNotification');
            notification.textContent = message;
            notification.classList.add('show');
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }

        <?php if ($is_success): ?>
        // Auto-close after 60 seconds
        setTimeout(() => {
            if (confirm('Authentication complete. Close this window?')) {
                window.close();
            }
        }, 60000);
        <?php endif; ?>
    </script>
</body>
</html>