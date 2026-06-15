<div align="center">
  <br>
  <img src="frontend/assets/HawkPhish%20Logo.png" alt="HawkPhish Logo" width="180" style="border-radius: 24px; box-shadow: 0 0 40px rgba(233,69,96,0.25);">
  <br><br>

  <h1 align="center" style="font-weight: 800; letter-spacing: -1px;">HawkPhish</h1>
  <p align="center">
    <strong>Advanced Phishing Simulation Platform</strong> for Red Teams & Security Awareness Training
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/version-1.2.0-e94560?style=flat-square&logo=git&logoColor=white" alt="Version">
    <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite">
    <img src="https://img.shields.io/badge/license-Red%20Team%20Use-e94560?style=flat-square" alt="License">
  </p>
</div>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage-tutorial">Usage Tutorial</a> •
  <a href="#-support--donate">Support</a> •
  <a href="#-disclaimer">Disclaimer</a>
</p>

---

<div align="center">
  <br>
  <img src="frontend/assets/HawkPhishdashboard.png" alt="HawkPhish Dashboard" width="95%" style="border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.4);">
  <br>
  <p><em>Real-time dashboard with campaign tracking, live feed, target sessions and resource overview.</em></p>
  <br>
</div>

---

## 🦅 What is HawkPhish?

**HawkPhish** is a powerful, self-hosted phishing simulation platform designed for **authorized red team operations**, **penetration testers**, and **security awareness training programs**.

It gives you a complete workflow to build, launch, and measure phishing campaigns from a single dark-themed web dashboard:

- Craft convincing phishing emails with custom or pre-built HTML templates
- Host realistic landing pages that capture credentials
- Import target groups and rotate SMTP providers / proxies
- Track every open, click, and credential submission in real time
- Export professional PDF reports for stakeholders

Everything runs locally with a lightweight **FastAPI** backend, **SQLite** database, and a sleek **vanilla HTML + Tailwind CSS** frontend.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 📊 **Dashboard** | Live stats, open/click/submit rates, live feed, target sessions and system status. |
| 🚀 **Campaigns** | Create, start, pause, resume and cancel campaigns with random delays, proxy rotation, and advanced settings. |
| 📧 **Email Templates** | Custom HTML editor with live preview, variables, severity/tags, categories, and filtering. |
| 🌐 **Landing Pages** | Single-file HTML, multi-file ZIP upload, import any URL, or use 12+ pre-built login page templates. |
| 🔗 **External Integration** | Drop-in JavaScript SDK to track and capture credentials from ANY external landing page. |
| 👥 **Target Groups** | Organize recipients, bulk-import via JSON/CSV, store names, positions and custom data. |
| 🔌 **SMTP Configs** | 30+ providers including API-based (SendGrid, Mailgun, AWS SES, Brevo, Resend, Mailjet, etc.) and SMTP relay. |
| 🛡️ **Proxy Rotator** | HTTP / HTTPS / SOCKS4 / SOCKS5 proxy rotation with health checks, latency testing and bulk import. |
| 📡 **Tracking** | Pixel tracking for opens, link tracking for clicks, credential capture, and full session timelines. |
| 📄 **Reports** | Download per-campaign or dashboard summary PDFs, JSON, and CSV exports. |
| 📋 **Audit Logs** | Every action logged with timestamps for compliance and review. |
| 🔧 **Built-in SMTP Server** | Raw SMTP server for receiving and relaying emails directly. |
| 🔒 **Ethical First** | Built-in warnings and "Authorized Use Only" branding. |

---

## 🛠️ Tech Stack

<div align="center">

  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
  ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
  ![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
  ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
  ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)

</div>

**Backend**

- FastAPI (async Python)
- SQLAlchemy 2.0 + aiosqlite
- aiosmtplib, email-validator, Jinja2
- reportlab (PDF reports), Pillow + qrcode

**Frontend**

- Single-page vanilla JavaScript app
- Tailwind CSS (CDN)
- Font Awesome icons
- Responsive dark UI

---

## ⚡ Installation

### Requirements

- Python 3.11 or higher
- Windows / Linux / macOS
- (Optional) A valid SMTP server or API key for sending

### 1. Clone or extract the project

```bash
cd hawkphish
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
cd backend
python main.py
```

The server will start on:

```
http://0.0.0.0:8000
```

Open your browser and navigate to:

```
http://localhost:8000
```

---

## 🎓 Complete Usage Tutorial

### Step 1 — Start the Server

Open a terminal and navigate to the project:

```bash
cd hawkphish/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Open your browser to:

```
http://localhost:8000
```

The dashboard will load immediately. No build step required.

---

### Step 2 — Configure SMTP (Email Sending)

1. Go to **SMTP Configs** in the sidebar.
2. Click **New SMTP**.
3. Select your provider from the dropdown:

**Standard SMTP (Username + Password):**
- Office 365, Gmail, Google Workspace, Outlook.com
- Zoho, Yandex, Mailtrap, IONOS
- GoDaddy, Namecheap, HostGator, Bluehost, SiteGround
- Custom SMTP (any host/port)

**API Providers (API Key only, no SMTP connection):**
- **SendGrid API** — `api_key` required
- **Amazon SES API** — `access_key` + `secret_key` + `region` (e.g. `us-east-1`)
- **Mailgun API** — `api_key` + `domain` (e.g. `mg.yoursite.com`)
- **Postmark API** — `api_key` (Server Token)
- **SparkPost API** — `api_key`
- **Brevo API** — `api_key`
- **Mailchimp / Mandrill API** — `api_key`
- **MailerSend API** — `api_key`
- **Resend API** — `api_key`
- **Elastic Email API** — `api_key`
- **SMTP2GO API** — `api_key`
- **Pepipost API** — `api_key`
- **SocketLabs API** — `api_key` + `server_id`
- **Mailjet API** — `api_key` + `api_secret`

4. Fill the fields. For API providers, the **API Key** section will appear automatically.
5. Click **Create & Validate SMTP**. The system will test the connection and mark it healthy/unhealthy.

> 💡 **Bulk Import:** Click the **Bulk Import** button to paste multiple configs at once:
> ```text
> smtp.office365.com|587|user@company.com|password
> smtp.gmail.com|587|you@gmail.com|app-password
> ```

> 💡 **Test Send:** Every SMTP config has a **Test Send** button. Use it to send a test email to yourself before launching a campaign.

---

### Step 3 — Create Target Groups

1. Go to **Groups** in the sidebar.
2. Click **New Group**.
3. Give it a name, description, and color.
4. Open the group to add recipients.

**Add Recipients (one by one):**
- Email (required)
- First Name, Last Name
- Position / Role
- Any other data is stored and can be used in templates

**Bulk Import (JSON):**
```json
{
  "recipients": [
    {"email":"user1@company.com","first_name":"John","last_name":"Doe","position":"Manager"},
    {"email":"user2@company.com","first_name":"Jane","last_name":"Smith","position":"Engineer"}
  ]
}
```

> 💡 **Custom Fields:** You can pass any extra fields (department, location, employee_id) and they will be stored. Use them in templates as `##department##`, `##location##`, etc.

---

### Step 4 — Create Email Templates

1. Go to **Templates** in the sidebar.
2. Click **New Template**.
3. Fill in:
   - **Name** — internal name (e.g. "Office 365 Reset")
   - **Subject** — email subject line
   - **Category** — for organization (e.g. "corporate", "social")
   - **Severity** — Low / Medium / High / Critical
   - **Tags** — comma-separated (e.g. "office365, urgent")
   - **HTML Body** — the full email HTML

**Built-in Variables (auto-replaced per recipient):**
| Variable | Replaced With |
|----------|---------------|
| `##email##` | Recipient's email address |
| `##first_name##` | Recipient's first name |
| `##last_name##` | Recipient's last name |
| `##full_name##` | First + Last name |
| `##position##` | Recipient's position |
| `##link##` | Tracking link (auto-generated) |
| `##domain##` | Recipient's email domain |
| `##date##` | Current date |
| `##tracking_id##` | Unique tracking ID |
| `##company##` | Recipient's domain (uppercase) |
| `##phone##` | Recipient's phone (if stored) |
| `##location##` | Recipient's location (if stored) |
| Any custom field | `##field_name##` |

**Subject Line Rotation:**
You can create multiple subject lines separated by `;` for rotation:
```
Security Alert: Action Required;Your account needs verification;Urgent: Confirm your identity
```

> 💡 **Filtering:** Templates can be filtered by name, category, tag, or severity.
> 💡 **Upload:** You can upload an `.html` file instead of pasting.

---

### Step 5 — Create Landing Pages

1. Go to **Landing Pages** in the sidebar.
2. Click **New Page**.

**Method A — Paste HTML (Simple):**
- Paste your HTML directly into the editor.
- Set capture fields (e.g. `email`, `password`, `otp`).
- Set a redirect URL (where users go after submitting).
- Click **Create**.

**Method B — Upload ZIP (Multi-File):**
- Click **Upload ZIP**.
- Select a `.zip` file containing your full landing page (HTML, CSS, JS, images).
- The system extracts all files and serves them.
- The root HTML file is auto-detected (e.g. `index.html`).
- You can also upload individual files (CSS, JS, images) later.

**Method C — Import from URL:**
- Enter any URL (e.g. `https://login.microsoftonline.com`).
- The system fetches the HTML.
- You can then edit it.

**Method D — Pre-built Templates:**
- Click **Use Template**.
- Choose from: Google Login, Microsoft 365, Office 365, LinkedIn, Outlook Web, AWS Console, Slack, GitHub, Zoom, Dropbox, PayPal, Apple ID.
- Each comes with realistic HTML and correct capture fields.

**Capture Fields:**
You can capture ANY form fields by name. Common fields:
- `email`, `password`, `username`, `otp`, `ssn`, `card`, `pin`, `phone`
- Any custom field name works automatically.

> 💡 **File Management:** After creating a landing page, go to **Files** tab to see all uploaded files. You can delete individual files or re-upload.

---

### Step 6 — External Integration (Drop-in SDK)

If you want to track an **external landing page** (not hosted on HawkPhish):

1. Go to **Integrations** in the sidebar.
2. Click **Generate SDK**.
3. Copy the generated JavaScript snippet.
4. Paste it into the `<head>` of your external landing page.

**What the SDK does:**
- Tracks page views, clicks, and form submissions
- Auto-captures any form fields (email, password, etc.)
- Sends data back to HawkPhish via CORS
- Works with any website, any platform (WordPress, Wix, custom HTML)

**How to use:**
1. Create a campaign in HawkPhish.
2. Generate a tracking link for that campaign.
3. Send the tracking link in your email.
4. When the user clicks, they go to your external page.
5. The SDK on that page reports everything back to HawkPhish.

> 💡 **No landing page required in the campaign.** Just set the redirect URL in the email template to point to your external site.

---

### Step 7 — Launch a Campaign

1. Go to **Campaigns** in the sidebar.
2. Click **New Campaign**.
3. Fill in:
   - **Name** — e.g. "Q1 Security Awareness"
   - **Template** — select from your templates
   - **SMTP Config** — select a working provider
   - **Target Group** — select recipients
   - **Landing Page** — optional, select if you want credential capture
   - **Settings:**
     - `min_delay` — minimum seconds between emails (default: 2)
     - `max_delay` — maximum seconds between emails (default: 8)
     - `base_url` — your server URL (e.g. `http://your-server.com`)
   - **Advanced Settings:**
     - **Subject Rotation** — rotate between multiple subject lines
     - **From Name Rotation** — rotate sender names
     - **Letter Rotation** — rotate between multiple templates
     - **Spoof From** — display a different sender address
     - **Reply-To** — set a reply-to address
     - **BCC / CC** — add hidden recipients
     - **Custom Headers** — add any SMTP headers
     - **Disclaimer** — append a legal disclaimer
     - **Attachments** — attach files to the email

4. Click **Create Campaign**.
5. Click **Start** to begin sending.

**Campaign Controls:**
- **Start** — begins sending emails with random delays
- **Pause** — pauses the campaign (can resume later)
- **Cancel** — permanently stops the campaign
- **Status** — Draft → Scheduled → Running → Paused → Completed

> 💡 **Profile Groups:** You can assign SMTP configs to groups (e.g. "default", "clients", "personal"). Campaigns pick from the assigned group.

---

### Step 8 — Monitor & Track Results

**Dashboard:**
- Total campaigns, running/completed count
- Total sent, opened, clicked, submitted
- Open Rate, Click Rate, Submit Rate
- Resource counts (SMTP configs, groups, recipients)

**Live Feed:**
- Real-time stream of opens, clicks, and credential submissions
- Shows email, campaign, IP, browser, OS, device, country, city, ISP
- Updates automatically

**Target Sessions:**
- Click any session to see the full timeline
- Events: sent → opened → clicked → submitted
- IP addresses, browsers, devices, countries
- Full event history with timestamps

**Tracking Methods:**
1. **Pixel Tracking** — invisible 1x1 image in the email. When opened, records the open.
2. **Link Tracking** — all links in the email are wrapped. When clicked, records the click and redirects to the landing page.
3. **Form Submission** — when the user submits the landing page form, all fields are captured.

**Credential Capture:**
- Go to **Landing Pages** → click on a page → **Captured Data** tab.
- See all submitted credentials with timestamps.
- Export to CSV or JSON.

---

### Step 9 — Proxies (Optional)

If you want to rotate proxies during sending:

1. Go to **Proxies** in the sidebar.
2. Click **New Proxy**.
3. Enter:
   - Name, Type (HTTP / HTTPS / SOCKS4 / SOCKS5)
   - Host, Port
   - Username / Password (if authenticated)
4. Click **Test** to verify the proxy works.

**Bulk Import:**
```
http://user:pass@proxy1.com:8080
socks5://proxy2.com:1080
http://proxy3.com:3128
```

**In Campaigns:**
- Enable **Use Proxies** when creating a campaign.
- The system will rotate through active, healthy proxies for each email.
- Failed proxies are auto-skipped.

---

### Step 10 — Built-in SMTP Server (Optional)

1. Go to **SMTP Server** in the sidebar.
2. Click **Start Server**.
3. Set host (e.g. `0.0.0.0`) and port (e.g. `2525`).
4. The server starts listening for raw SMTP connections.
5. You can use it as a local relay or for testing.
6. Click **Stop Server** to shut it down.

> 💡 **Status Panel:** Shows connections, emails processed, and errors in real-time.

---

### Step 11 — Audit Logs

1. Go to **Audit Logs** in the sidebar.
2. View every action: campaign created, started, paused, SMTP added, etc.
3. Filter by action type or entity.
4. See timestamps, user, success/failure status.

---

### Step 12 — Reports & Exports

**Per-Campaign Reports:**
1. Go to **Campaigns**.
2. Click the menu (⋮) on any campaign.
3. Choose:
   - **Download PDF** — full campaign report with charts
   - **Download JSON** — machine-readable report
   - **Download CSV** — spreadsheet-friendly data

**Dashboard Summary PDF:**
1. Go to **Dashboard**.
2. Click **Download Summary PDF**.
3. Gets a PDF of all campaigns and stats.

**Campaign Timeline:**
1. Go to **Campaigns**.
2. Click **Timeline** on any campaign.
3. See every recipient's journey: sent → opened → clicked → submitted.

---

## 🧪 API Endpoints

HawkPhish exposes a full REST API. For interactive documentation, visit `/docs` after starting the server.

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server health check |
| GET | `/api/dashboard` | Dashboard statistics |
| GET/POST | `/api/campaigns` | List / create campaigns |
| GET | `/api/campaigns/{id}` | Get campaign details |
| PUT | `/api/campaigns/{id}` | Update campaign status |
| DELETE | `/api/campaigns/{id}` | Delete campaign |
| POST | `/api/campaigns/{id}/start` | Start sending |
| POST | `/api/campaigns/{id}/pause` | Pause sending |
| POST | `/api/campaigns/{id}/cancel` | Cancel campaign |
| GET | `/api/campaigns/{id}/timeline` | Recipient timeline |
| GET | `/api/campaigns/{id}/report/json` | JSON report |
| GET | `/api/campaigns/{id}/report/csv` | CSV report |
| GET | `/api/campaigns/{id}/report/pdf` | PDF report |
| GET | `/api/campaigns/report/pdf/summary` | Dashboard summary PDF |

### SMTP
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/smtp` | List / create SMTP configs |
| GET | `/api/smtp/{id}` | Get SMTP config |
| PUT | `/api/smtp/{id}` | Update SMTP config |
| DELETE | `/api/smtp/{id}` | Delete SMTP config |
| POST | `/api/smtp/{id}/health` | Test health |
| POST | `/api/smtp/{id}/test-send` | Send test email |
| POST | `/api/smtp/validate-all` | Validate all configs |
| POST | `/api/smtp/bulk-import` | Bulk import configs |

### Templates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/templates` | List / create templates |
| GET | `/api/templates/{id}` | Get template |
| PUT | `/api/templates/{id}` | Update template |
| DELETE | `/api/templates/{id}` | Delete template |

### Landing Pages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/landing-pages` | List / create pages |
| GET | `/api/landing-pages/{id}` | Get page |
| PUT | `/api/landing-pages/{id}` | Update page |
| DELETE | `/api/landing-pages/{id}` | Delete page |
| POST | `/api/landing-pages/{id}/upload-zip` | Upload ZIP file |
| POST | `/api/landing-pages/{id}/upload-file` | Upload single file |
| GET | `/api/landing-pages/{id}/files` | List files |
| DELETE | `/api/landing-pages/{id}/files/{name}` | Delete file |
| POST | `/api/landing-pages/import-url` | Import from URL |
| GET | `/api/landing-pages/templates/list` | List pre-built templates |
| POST | `/api/landing-pages/templates/{name}/use` | Use pre-built template |

### Tracking
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pixel/{tracking_id}` | Tracking pixel (image) |
| GET | `/track/{tracking_id}` | Click redirect |
| GET | `/lp/{id}` | Show landing page |
| GET | `/lp/{id}/{path}` | Serve static files |
| POST | `/lp/{id}/submit` | Capture credentials |
| GET | `/api/sessions` | List sessions |
| GET | `/api/sessions/{id}` | Session details |
| GET | `/api/live-feed` | Real-time events |

### External Integration
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/external/track` | Track external event |
| POST | `/api/external/submit` | Capture external credentials |
| POST | `/api/external/generate-link` | Generate tracking link |
| POST | `/api/external/generate-sdk` | Generate JS SDK |
| GET | `/api/external/sdk.js` | Serve SDK script |

### Groups
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/groups` | List / create groups |
| GET | `/api/groups/{id}` | Get group |
| PUT | `/api/groups/{id}` | Update group |
| DELETE | `/api/groups/{id}` | Delete group |
| POST | `/api/groups/{id}/recipients` | Add recipient |
| POST | `/api/groups/{id}/recipients/import` | Bulk import |
| DELETE | `/api/groups/{id}/recipients/{rid}` | Delete recipient |

### Proxies
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/proxies` | List / create proxies |
| GET | `/api/proxies/{id}` | Get proxy |
| PUT | `/api/proxies/{id}` | Update proxy |
| DELETE | `/api/proxies/{id}` | Delete proxy |
| POST | `/api/proxies/{id}/test` | Test proxy |
| POST | `/api/proxies/test-all` | Test all proxies |
| POST | `/api/proxies/bulk-import` | Bulk import |

### SMTP Server
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/smtp-server/start` | Start built-in SMTP server |
| POST | `/api/smtp-server/stop` | Stop server |
| GET | `/api/smtp-server/status` | Get status |

### Audit Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit-logs` | List logs |
| GET | `/api/audit-logs/stats` | Statistics |

---

## 💰 Support via Crypto

If HawkPhish helped your security work, consider supporting continued development. **Crypto only — no fiat payment methods.**

<div align="center">

  <p>
    <img src="https://img.shields.io/badge/Binance-893759503-F0B90B?style=for-the-badge&logo=binance&logoColor=black" alt="Binance ID">
  </p>

  <table>
    <tr>
      <td align="center">
        <img src="https://img.shields.io/badge/USDT%20TRC20-26A17B?style=for-the-badge&logo=tether&logoColor=white" alt="USDT"><br>
        <code>TNweg4pBxgtABK6g1Jb6isrn3PZawEizVJ</code>
      </td>
      <td align="center">
        <img src="https://img.shields.io/badge/BTC-F7931A?style=for-the-badge&logo=bitcoin&logoColor=white" alt="BTC"><br>
        <code>13JxhEWzo21jcpbiyL8hvemeKEmXcrY7G2</code>
      </td>
    </tr>
    <tr>
      <td align="center">
        <img src="https://img.shields.io/badge/ETH%20ERC20-3C3C3D?style=for-the-badge&logo=ethereum&logoColor=white" alt="ETH"><br>
        <code>13JxhEWzo21jcpbiyL8hvemeKEmXcrY7G2</code>
      </td>
      <td align="center">
        <img src="https://img.shields.io/badge/BNB%20BEP20-F0B90B?style=for-the-badge&logo=binance&logoColor=black" alt="BNB"><br>
        <code>0x0874626d93936f3e17591f10cfe5355e5fd7fcce</code>
      </td>
    </tr>
  </table>

</div>

---

## 📬 Contact & Issues

- **Author:** Qasim Ali — Security Researcher & Red Team Operator
- **Email:** [qasim.sec1401@proton.me](mailto:qasim.sec1401@proton.me)
- **GitHub:** [@QASIM1401](https://github.com/QASIM1401)
- **Bug Reports:** [GitHub Issues](https://github.com/QASIM1401/reconpro/issues)

---

## ⚠️ Disclaimer

**HawkPhish is intended for authorized security testing and educational purposes only.**

Phishing simulations must only be conducted against systems and individuals for whom you have **explicit written permission**. Unauthorized phishing, credential harvesting, or email spoofing is illegal in most jurisdictions and violates most service providers' terms of use.

The authors assume no liability for misuse of this tool. **Use responsibly and ethically.**

---

<div align="center">
  <br>
  <img src="frontend/assets/HawkPhish%20Logo.png" alt="HawkPhish" width="64" style="border-radius: 12px;">
  <br>
  <p><strong>HawkPhish</strong> — See what others click.</p>
  <br>
</div>
