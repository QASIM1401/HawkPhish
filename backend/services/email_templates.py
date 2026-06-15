"""HawkPhish - Pre-built Email Templates"""
from typing import List, Dict


EMAIL_TEMPLATES: List[Dict] = [
    {
        "name": "Password Expiry Warning",
        "category": "security",
        "subject": "Your password will expire in 24 hours",
        "variables": ["email", "first_name", "link"],
        "html": """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f4f4f4;padding:20px">
<div style="background:#1a73e8;padding:24px;text-align:center">
<h1 style="color:#fff;margin:0;font-size:20px">Password Expiry Notice</h1>
</div>
<div style="background:#fff;padding:32px;border-radius:0 0 8px 8px">
<p style="font-size:15px;color:#333">Hello ##first_name##,</p>
<p style="font-size:15px;color:#333">Your network password for <b>##email##</b> will expire in <b>24 hours</b>.</p>
<p style="font-size:15px;color:#333">To avoid losing access to your accounts, please update your password immediately:</p>
<div style="text-align:center;margin:28px 0">
<a href="##link##" style="background:#1a73e8;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600">Update Password Now</a>
</div>
<p style="font-size:13px;color:#999">If you did not request this change, contact IT Security immediately.</p>
</div>
</div>
"""
    },
    {
        "name": "IT Security Alert",
        "category": "security",
        "subject": "Security Alert: Unusual sign-in activity detected",
        "variables": ["email", "first_name", "link"],
        "html": """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f4f4f4;padding:20px">
<div style="background:#d93025;padding:24px;text-align:center">
<h1 style="color:#fff;margin:0;font-size:20px">&#9888; Security Alert</h1>
</div>
<div style="background:#fff;padding:32px;border-radius:0 0 8px 8px">
<p style="font-size:15px;color:#333">Hello ##first_name##,</p>
<p style="font-size:15px;color:#333">We detected an <b>unauthorized sign-in attempt</b> on your account <b>##email##</b>.</p>
<table style="width:100%;margin:16px 0;border:1px solid #eee;border-radius:6px;font-size:13px">
<tr><td style="padding:8px;color:#666">Location</td><td style="padding:8px">Unknown (Tor Network)</td></tr>
<tr style="background:#f9f9f9"><td style="padding:8px;color:#666">IP Address</td><td style="padding:8px">185.220.101.xx</td></tr>
<tr><td style="padding:8px;color:#666">Device</td><td style="padding:8px">Linux / Chrome 120</td></tr>
<tr style="background:#f9f9f9"><td style="padding:8px;color:#666">Time</td><td style="padding:8px">Just now</td></tr>
</table>
<p style="font-size:15px;color:#333">If this was you, please verify your identity:</p>
<div style="text-align:center;margin:28px 0">
<a href="##link##" style="background:#d93025;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600">Verify It Was Me</a>
</div>
<p style="font-size:13px;color:#999">If you don't recognize this activity, we recommend changing your password immediately.</p>
</div>
</div>
"""
    },
    {
        "name": "Shared Document",
        "category": "collaboration",
        "subject": "##first_name## shared a document with you",
        "variables": ["email", "first_name", "link"],
        "html": """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f4f4f4;padding:20px">
<div style="background:#fff;padding:32px;border-radius:8px">
<div style="text-align:center;margin-bottom:20px">
<div style="width:48px;height:48px;background:#4285f4;border-radius:8px;display:inline-flex;align-items:center;justify-content:center">
<span style="color:#fff;font-size:24px">&#128196;</span>
</div>
</div>
<h2 style="font-size:18px;color:#333;text-align:center;margin-bottom:16px">New Document Shared</h2>
<p style="font-size:15px;color:#333;text-align:center">A document has been shared with you. Click below to view and edit:</p>
<div style="text-align:center;margin:24px 0">
<a href="##link##" style="background:#4285f4;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600">Open Document</a>
</div>
<hr style="border:none;border-top:1px solid #eee;margin:24px 0">
<p style="font-size:12px;color:#999;text-align:center">This email was sent to ##email##</p>
</div>
</div>
"""
    },
    {
        "name": "Wire Transfer Request",
        "category": "finance",
        "subject": "Urgent: Wire Transfer Approval Needed",
        "variables": ["email", "first_name", "link"],
        "html": """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f4f4f4;padding:20px">
<div style="background:#fff;padding:32px;border-radius:8px">
<p style="font-size:15px;color:#333">Hi ##first_name##,</p>
<p style="font-size:15px;color:#333">I need you to process an urgent wire transfer. The vendor is waiting and we need to close this today.</p>
<p style="font-size:15px;color:#333"><b>Amount:</b> $47,500.00<br>
<b>Recipient:</b> Global Ventures LLC<br>
<b>Reference:</b> INV-2024-8847</p>
<p style="font-size:15px;color:#333">Please review and approve at the link below:</p>
<div style="text-align:center;margin:24px 0">
<a href="##link##" style="background:#0d6efd;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600">Approve Transfer</a>
</div>
<p style="font-size:13px;color:#999">Thanks,<br>Finance Team</p>
</div>
</div>
"""
    },
    {
        "name": "VPN Access Update",
        "category": "it",
        "subject": "Action Required: VPN Access Configuration Update",
        "variables": ["email", "first_name", "link"],
        "html": """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f4f4f4;padding:20px">
<div style="background:#0f3460;padding:24px;text-align:center">
<h1 style="color:#fff;margin:0;font-size:20px">VPN Configuration Update</h1>
</div>
<div style="background:#fff;padding:32px;border-radius:0 0 8px 8px">
<p style="font-size:15px;color:#333">Hello ##first_name##,</p>
<p style="font-size:15px;color:#333">As part of our ongoing security infrastructure upgrade, all VPN configurations need to be updated by end of week.</p>
<p style="font-size:15px;color:#333">Please log in to the VPN portal to download your updated configuration:</p>
<div style="text-align:center;margin:28px 0">
<a href="##link##" style="background:#0f3460;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600">Update VPN Config</a>
</div>
<p style="font-size:13px;color:#999">If you need assistance, contact IT Support.</p>
</div>
</div>
"""
    },
    {
        "name": "Package Delivery",
        "category": "logistics",
        "subject": "Your package is ready for delivery",
        "variables": ["email", "first_name", "link"],
        "html": """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f4f4f4;padding:20px">
<div style="background:#ff9900;padding:24px;text-align:center">
<h1 style="color:#fff;margin:0;font-size:20px">Package Delivery Notification</h1>
</div>
<div style="background:#fff;padding:32px;border-radius:0 0 8px 8px">
<p style="font-size:15px;color:#333">Hello ##first_name##,</p>
<p style="font-size:15px;color:#333">We attempted to deliver your package today but no one was available to receive it.</p>
<table style="width:100%;margin:16px 0;border:1px solid #eee;border-radius:6px;font-size:13px">
<tr><td style="padding:8px;color:#666">Tracking #</td><td style="padding:8px">1Z999AA10123456784</td></tr>
<tr style="background:#f9f9f9"><td style="padding:8px;color:#666">Status</td><td style="padding:8px;color:#d93025">Delivery Attempted</td></tr>
</table>
<p style="font-size:15px;color:#333">Please reschedule delivery or provide delivery instructions:</p>
<div style="text-align:center;margin:24px 0">
<a href="##link##" style="background:#ff9900;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600">Reschedule Delivery</a>
</div>
</div>
</div>
"""
    },
]


def get_all_email_templates() -> List[Dict]:
    return [{"name": t["name"], "category": t["category"], "subject": t["subject"], "variables": t["variables"]} for t in EMAIL_TEMPLATES]


def get_email_template(name: str) -> Dict:
    for t in EMAIL_TEMPLATES:
        if t["name"].lower() == name.lower():
            return t
    return None
