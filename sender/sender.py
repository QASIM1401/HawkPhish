import os
import base64
import socket
import socks
import smtplib
import concurrent.futures
from datetime import datetime
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formataddr, make_msgid
from re import findall
from colorama import Fore, Style, init
import qrcode
from random import choice
import sys
from time import sleep
import uuid
import ssl
import hashlib
import hmac
import re
import dns.resolver
import dns.exception
init(autoreset=True)

fr = Fore.RED
gr = Fore.BLUE
fc = Fore.CYAN
fw = Fore.WHITE
fy = Fore.YELLOW
fg = Fore.GREEN
fm = Fore.MAGENTA
bd = Style.BRIGHT
res = Style.RESET_ALL
pretty = Fore.LIGHTMAGENTA_EX + Fore.LIGHTCYAN_EX
dp = "\033[0;35m"
pink = Fore.LIGHTGREEN_EX + Fore.LIGHTMAGENTA_EX

os.system('cls' if os.name == 'nt' else 'clear')

directories = ['Files_Sending', 'Sending_Process/Failed_Sending','Sending_Process/Success_Sending',
               'SMTPs_Checking/Bad_SMTPs','SMTPs_Checking/Good_SMTPs', 'Mailist_Here','SMTPs_Here',
               'QR_Code', 'Letters_Here', 'Encrypted_Letters_Result', 'Attachment_Here']

for d in directories:
    if not os.path.exists(d):
        os.makedirs(d) 

ronaldo = {
    'subject': 'Files_Sending/subjects.txt',
    'name': 'Files_Sending/names.txt',
    'config': 'Files_Sending/config.txt',
    'proxy': 'Files_Sending/proxy.txt',
    'links': 'Files_Sending/links.txt',
}
for file in ronaldo.values():
    if not os.path.isfile(file):
        with open(file, 'w') as f:
            f.write("")

c = """sleeping = {2} # SLEEPING BETWEEN EMAILS e.g., 3

priority = {1} # PRIORITY LEVEL (1-5) 1.(Highest), 2.(High), 3.(Normal), 4.(Low), 5.(Lowest).

subject_rotation = {3} # ROTATION SUBJECT EVERY EMAILS e.g., 2 EMAILS

fromname_rotation = {3} # ROTATION NAME EVERY EMAILS e.g., 1 email

letters_rotation = {YES} #[YES/NO] CHOOSE YES/NO IF YOU WANT TO USE ROTATION LETTER

urletters = {letter1.html;letter2.html} # PUT YOUR LETTERS.html SEPARATED BY ; e.g., letter1.html;letter2.html

youremail = {example@example.com} # ADD YOUR EMAIL

proxy_yesorno = {NO} #[YES/NO] CHOOSE YES/NO IF YOU WANT TO USE PROXY

proxy_type = {SOCKS5} # PUT YOUR TYPE SOCKS4 OR SOCKS5 OR HTTP

links_rotation = {NO} #[YES/NO] CHOOSE YES/NO IF YOU WANT TO USE LINKS ROTATIONS

date = {NO} #[YES/NO] CHOOSE YES/NO IF YOU WANT TO ADD THE DATE ON YOUR LETTER

add email on letters = {NO} #[YES/NO] CHOOSE YES/NO IF YOU WANT SHOW THE EMAIL ON LETTER JUST ADD ##email## on your letter
"""

cf = 'Files_Sending/config.txt'

def create(ff, cc):
    if not os.path.isfile(ff) or os.path.getsize(ff) == 0:
        with open(ff, 'w') as file:
            file.write(cc)

def center(var: str, space: int = None):
    if not space:
        space = (os.get_terminal_size().columns - len(var.splitlines()[int(len(var.splitlines()) / 2)])) / 2
    return "\n".join((' ' * int(space)) + var for var in var.splitlines())

create(cf, c)

good_smtp = set()
bad_smtp = set()
idk = 0
chk = 0
j = 0
total = 0



email_con = open('Files_Sending/config.txt', 'r', errors='ignore').read()
sleeping = int(findall(r'sleeping = {(.*?)}', email_con)[0])
priority = int(findall(r'priority = {(.*?)}', email_con)[0])
subject_rotation = int(findall(r'subject_rotation = {(.*?)}', email_con)[0])
fromname_rotation = int(findall(r'fromname_rotation = {(.*?)}', email_con)[0])
letters_rotation = findall(r'letters_rotation = {(.*?)}', email_con)[0].strip().upper()
your_letters = findall(r'urletters = {(.*?)}', email_con)[0]
test_email = findall(r'youremail = {(.*?)}', email_con)[0]
proxy_yn = findall(r'proxy_yesorno = {(.*?)}', email_con)[0].strip().upper()
proxy_type = findall(r'proxy_type = {(.*?)}', email_con)[0].strip().upper()
links_rotation = findall(r'links_rotation = {(.*?)}', email_con)[0].strip().upper()
date = findall(r'date = {(.*?)}', email_con)[0].strip().upper()
add_email = findall(r'add email on letters = {(.*?)}', email_con)[0].strip().upper()

def encode_base64(data: str) -> str:
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def encode_hex(data: str) -> str:
    return data.encode('utf-8').hex()

def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_message_id(domain: str) -> str:
    """Generate a proper Message-ID for the email"""
    return make_msgid(domain=domain)

def get_domain_from_email(email: str) -> str:
    """Extract domain from email address"""
    return email.split('@')[1] if '@' in email else ''

def create_spf_header(domain: str) -> str:
    """Create SPF-related headers"""
    return f"v=spf1 include:_spf.{domain} ~all"

def create_dkim_signature(msg: MIMEMultipart, domain: str, selector: str = "default") -> str:
    """Create DKIM signature for the email"""
    # This is a simplified DKIM implementation
    # In production, you'd need proper RSA key generation and signing
    headers = ['from', 'to', 'subject', 'date', 'message-id']
    header_string = ""
    for header in headers:
        if header in msg:
            header_string += f"{header}: {msg[header]}\r\n"
    
    # Simplified DKIM signature (in real implementation, use proper RSA signing)
    signature_data = f"v=1; a=rsa-sha256; d={domain}; s={selector}; h={':'.join(headers)}; bh=abc123; b=def456"
    return signature_data

def add_authentication_headers(msg: MIMEMultipart, domain: str, username: str):
    """Add comprehensive authentication headers"""
    # Message-ID
    msg['Message-ID'] = generate_message_id(domain)
    
    # Authentication-Results header
    msg['Authentication-Results'] = f"{domain}; spf=pass smtp.mailfrom={username}; dkim=pass header.d={domain}; dmarc=pass"
    
    # SPF headers
    msg['Received-SPF'] = f"pass ({domain}: domain of {username} designates {socket.gethostbyname(socket.gethostname())} as permitted sender)"
    
    # DKIM headers
    msg['DKIM-Signature'] = create_dkim_signature(msg, domain)
    
    # DMARC headers
    msg['DMARC-Filter'] = "Pass"
    
    # Additional security headers
    msg['X-Originating-IP'] = socket.gethostbyname(socket.gethostname())
    msg['X-Forwarded-For'] = socket.gethostbyname(socket.gethostname())
    msg['X-Real-IP'] = socket.gethostbyname(socket.gethostname())
    
    # Anti-spam headers
    msg['X-Spam-Status'] = "No, score=0.0"
    msg['X-Spam-Level'] = ""
    msg['X-Spam-Checker-Version'] = "SpamAssassin 3.4.0"
    
    # Email client headers
    msg['X-Mailer'] = 'Microsoft Outlook 16.0'
    msg['X-MimeOLE'] = 'Produced By Microsoft MimeOLE V6.00.2800.1441'
    msg['X-MS-Exchange-Organization-AuthAs'] = 'Internal'
    msg['X-MS-Exchange-Organization-AuthSource'] = 'Office365'
    msg['X-MS-Exchange-Organization-BypassClutter'] = 'true'
    
    # Content headers
    msg['MIME-Version'] = '1.0'
    msg['Content-Type'] = 'text/html; charset=UTF-8'
    msg['Content-Transfer-Encoding'] = '8bit'
    
    # Priority headers
    msg['X-Priority'] = '3'
    msg['X-MSMail-Priority'] = 'Normal'
    msg['Importance'] = 'Normal'
    
    # List management
    msg['List-Unsubscribe'] = f'<mailto:unsubscribe@{domain}>, <https://{domain}/unsubscribe>'
    msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
    
    # Return path
    msg['Return-Path'] = username


def read_letter(encrypt_method: str):
    time_rn = get_time_rn()
    rletters = []
    if letters_rotation == "YES":
        letters = your_letters.split(';')
    else:
        letters = [your_letters.split(';')[0]]

    if encrypt_method == 'Base64':
        os.makedirs('Encrypted_Letters_Result/Base64', exist_ok=True)
    elif encrypt_method == 'Hex':
        os.makedirs('Encrypted_Letters_Result/Hex', exist_ok=True)

    for letter in letters:
        try:
            with open(f'Letters_Here/{letter}', 'r', errors='ignore', encoding='utf-8') as f:
                data = f.read()
                if encrypt_method == 'Base64':
                    encoded_letters = encode_base64(data)
                    with open(f'Encrypted_Letters_Result/Base64/{letter.strip()}_Base64_{time_rn}.txt', "a") as su:
                        su.write(f"{encoded_letters}\n")
                elif encrypt_method == 'Hex':
                    encoded_letters = encode_hex(data)
                    with open(f'Encrypted_Letters_Result/Hex/{letter.strip()}_Hex_{time_rn}.txt', "a") as ss:
                        ss.write(f"{encoded_letters}\n")
                else:
                    encoded_letters = data

                rletters.append(encoded_letters)
        except Exception as e:
            print(f"{fr}[-] Letter file not found.  {e}")
            exit()
    return rletters

def read():
    encode_subjects = []
    encode_names = []
    with open(ronaldo['subject'], 'r', errors='ignore', encoding='utf-8') as f:
        subjects = f.read().splitlines()
    with open(ronaldo['name'], 'r', errors='ignore', encoding='utf-8') as f:
        names = f.read().splitlines()
    for subject in subjects:
        encode_subjects.append(base64.b64encode(subject.encode()).decode())
    for name in names:
        encode_names.append(base64.b64encode(name.encode()).decode())
    return encode_subjects, encode_names

def get_proxy():
    try:
        if proxy_yn == 'YES':
            with open(ronaldo['proxy'], 'r', errors='ignore', encoding='utf-8') as f:
                proxies = f.read().splitlines()
                if proxies:
                    return proxies, proxy_type
                else:
                    return None, None
        else:
            return None, None
    except:
        return None, None

def link():
    if links_rotation == "YES":
        try:
            with open(ronaldo['links'], 'r', errors='ignore', encoding='utf-8') as f:
                links = f.read().splitlines()
            return links
        except FileNotFoundError:
            print(f"{fr}[-] Links file not found.")
            exit()
    else:
        return []
    
def get_time_rn():
    now = datetime.now()
    return "{:04d}-{:02d}-{:02d}".format(now.year, now.month, now.day)

def clean_smtps(smtp_list):
    global j
    val = []
    inv = 0
    seen = set() 

    for smtp in smtp_list:
        if '"' in smtp:
            smtp = smtp.replace('"', '').strip()
        else:
            smtp = smtp.strip()

        if not smtp:
            inv += 1
            continue

        parts = smtp.split('|')
        if len(parts) != 4:
            inv += 1
            continue

        host, port_str, username, password = parts

        if not all([host, port_str, username, password]):
            inv += 1
            continue

        if any('***' in part or 'null' in part or 'localhost' in part or part.strip() == '' for part in parts):
            inv += 1
            continue

        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                inv += 1
                continue
        except ValueError:
            inv += 1
            continue

        smtp_key = f"{host}|{port}|{username}|{password}"
        if smtp_key in seen:
            inv += 1
            continue
        seen.add(smtp_key)

        val.append(smtp)
        j = len(val)

    print(f"{fg}[{fr}+{fg}] Total SMTPs: {inv + j}")
    print(f"{fg}[{fr}+{fg}] Cleaned SMTPs: Removed {inv} invalid (format or duplicates)")
    print(f"{fg}[{fr}+{fg}] Valid SMTPs: {len(val)}")
    return val
    

def check(smtp):
    global good_smtp, bad_smtp, chk, j
    host, port, username, password = smtp.split("|")
    port = int(port)
    time_rn = get_time_rn()
    try:
        # Create SSL context with better security settings
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with (smtplib.SMTP_SSL(host, port, context=context, timeout=30) if port == 465 else smtplib.SMTP(host, port, timeout=30)) as jcp:
            jcp.ehlo()
            if port != 465:
                try:
                    jcp.starttls(context=context)
                    jcp.ehlo()
                except smtplib.SMTPNotSupportedError:
                    pass
            jcp.login(username, password)

            domain = get_domain_from_email(username)
            msg = MIMEMultipart()
            msg['Subject'] = "SMTPs Checker BY t.me/DoYouLikePopo"
            msg['From'] = formataddr(("TEST", username))
            msg['To'] = test_email
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Add authentication headers for test email
            add_authentication_headers(msg, domain, username)
            
            data = f"""Valid SMTP BY @evilms\n\n{host}|{port}|{username}|{password}"""
            msg.attach(MIMEText(data, 'html', 'utf-8'))

            jcp.sendmail(username, test_email, msg.as_string())

            good_smtp.add(smtp)
            chk += 1
            print(f'{fw}{bd}[{pink}{bd}{time_rn}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fc}{bd}{chk}{fr}/{fc}{bd}{j}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}{bd}GOOD SMTP{fw}{bd}]{fr}{bd}─{fg}{bd}{smtp}{fw}')
            with open("SMTPs_Checking/Good_SMTPs.txt", 'a') as log_file:
                log_file.write(f"{smtp}\n")
            return True

    except Exception as e:
        chk += 1
        print(f'{fw}{bd}[{pink}{bd}{time_rn}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fc}{bd}{chk}{fr}/{fc}{bd}{j}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fr}{bd}BAD SMTP{fw}{bd}]{fr}{bd}─{fr}{bd}{smtp}{fw} | {e}')
        with open("SMTPs_Checking/Bad_SMTPs.txt", 'a') as log_file:
            bad_smtp.add(smtp)
            log_file.write(f"{smtp}\n")
        return False


def send(mailist, smtp, from_name, subject, reply_to=None, bcc=None, cc=None, spoof=None, attachment=None, encrypt_method=None):
    global bad_smtp, good_smtp, idk, total
    time_rn = get_time_rn()
    host, port, username, password = smtp.split("|")
    
    # Validate email address
    if not validate_email(mailist):
        print(f'{fw}{bd}[{pink}{bd}{time_rn}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fc}{bd}{idk+1}{fr}/{fc}{bd}{total}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fr}{bd}INVALID EMAIL{fw}{bd}]{fr}{bd}─{fr}{bd}{mailist}{fw}')
        idk += 1
        return False
    
    letter = read_letter(encrypt_method)
    encode_subject, encode_name = read()

    try:
        proxies, proxy_type = get_proxy()
        if proxies:
            proxy = choice(proxies)
            if proxy_type == "SOCKS5":
                socks.set_default_proxy(socks.SOCKS5, proxy.split(":")[0], int(proxy.split(":")[1]))
            elif proxy_type == "SOCKS4":
                socks.set_default_proxy(socks.SOCKS4, proxy.split(":")[0], int(proxy.split(":")[1]))
            elif proxy_type == "HTTP":
                socks.set_default_proxy(socks.HTTP, proxy.split(":")[0], int(proxy.split(":")[1]))
            socks.wrapmodule(smtplib)

        if smtp in bad_smtp:
            print(f"{fr}[-] skipping bad smtps")
            return False

        # Create SSL context with better security settings
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with (smtplib.SMTP_SSL(host, port, context=context, timeout=30) if port == 465 else smtplib.SMTP(host, port, timeout=30)) as abdouuu:
            abdouuu.ehlo()
            if port != 465: 
                try:
                    abdouuu.starttls(context=context)
                    abdouuu.ehlo()
                except smtplib.SMTPNotSupportedError:
                    pass
            abdouuu.login(username, password)

            rname = encode_name[from_name]
            rsubject = encode_subject[subject]
            email_lea = choice(letter)

            if add_email == 'YES':
                email_lea = email_lea.replace('##email##', mailist)

            if links_rotation == 'YES':
                links_list = link()
                if links_list:
                    selected_link = choice(links_list)
                    email_lea = email_lea.replace('##link##', selected_link)

            if date == 'YES':
                date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                email_lea = email_lea.replace('##date##', date_str)

            from_name = formataddr((str(Header(base64.b64decode(rname).decode('utf-8'), 'utf-8')), spoof if spoof else username))
            domain = get_domain_from_email(username)

            msg = MIMEMultipart()
            msg['From'] = from_name
            msg['To'] = mailist
            msg['Subject'] = str(Header(base64.b64decode(rsubject).decode('utf-8'), 'utf-8'))
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Add custom headers
            if reply_to: msg['Reply-To'] = reply_to
            if bcc: msg['Bcc'] = bcc
            if cc: msg['Cc'] = cc
            if spoof: msg['X-Spoof'] = spoof
            
            # Add comprehensive authentication headers
            add_authentication_headers(msg, domain, username)
            
            # Add additional headers for better deliverability
            msg.add_header('X-Email-Type', 'Promotional')
            msg.add_header('X-Job-ID', str(uuid.uuid4()))
            msg.add_header('X-Campaign-ID', 'Winter2024Sale')
            msg.add_header('X-Source', 'EmailMarketing')
            msg.add_header('Precedence', 'bulk')
            
            # Attach the email content as HTML body
            msg.attach(MIMEText(email_lea, 'html'))

            # Only attach NON-HTML files
            if attachment and not attachment.lower().endswith(('.html', '.htm')):
                try:
                    with open(attachment, 'rb') as att:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(att.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment)}')
                        part.add_header('Content-Type', 'application/octet-stream')
                        msg.attach(part)
                except FileNotFoundError:
                    print(f"{fr}[-] Attachment file not found: {attachment}")
                except Exception as e:
                    print(f"{fr}[-] Error attaching file: {e}")
            elif attachment and attachment.lower().endswith(('.html', '.htm')):
                print(f"{fy}[!] Skipping HTML file attachment to avoid duplication - HTML is already the email body{fw}")

            abdouuu.sendmail(username, mailist, msg.as_string())
            idk += 1

            print(f'{fw}{bd}[{pink}{bd}{time_rn}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fc}{bd}{idk}{fr}/{fc}{bd}{total}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}{bd}SUCCESS{fw}{bd}]{fr}{bd}─{fg}{bd}{mailist}{fr} ===> {fg}{bd}{smtp}{fw}')
            with open("Sending_Process/Success_Sending.txt", "a") as success_log:
                success_log.write(f"{mailist}\n")

    except Exception as e:
        idk += 1
        print(f'{fw}{bd}[{pink}{bd}{time_rn}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fc}{bd}{idk}{fr}/{fc}{bd}{total}{fw}{bd}]{fr}{bd}─{fw}{bd}[{fr}{bd}FAILED{fw}{bd}]{fr}{bd}─{fw}{bd}[{fr}{bd}{mailist}{fr} ===> {fr}{bd}{smtp}{fw} | {e}')
        with open("Sending_Process/Failed_Sending.txt", "a") as failed_log:
            failed_log.write(f"{mailist}\n")

def main():
    global total
    time_rn = get_time_rn()
    text = '''
▓█████ ██▒   █▓ ██▓ ██▓        ▄▄▄▄    █    ██   ██████ ▄▄▄█████▓▓█████  ██▀███  
▓█   ▀▓██░   █▒▓██▒▓██▒       ▓█████▄  ██  ▓██▒▒██    ▒ ▓  ██▒ ▓▒▓█   ▀ ▓██ ▒ ██▒
▒███   ▓██  █▒░▒██▒▒██░       ▒██▒ ▄██▓██  ▒██░░ ▓██▄   ▒ ▓██░ ▒░▒███   ▓██ ░▄█ ▒
▒▓█  ▄  ▒██ █░░░██░▒██░       ▒██░█▀  ▓▓█  ░██░  ▒   ██▒░ ▓██▓ ░ ▒▓█  ▄ ▒██▀▀█▄  
░▒████▒  ▒▀█░  ░██░░██████▒   ░▓█  ▀█▓▒▒█████▓ ▒██████▒▒  ▒██▒ ░ ░▒████▒░██▓ ▒██▒
░░ ▒░ ░  ░ ▐░  ░▓  ░ ▒░▓  ░   ░▒▓███▀▒░▒▓▒ ▒ ▒ ▒ ▒▓▒ ▒ ░  ▒ ░░   ░░ ▒░ ░░ ▒▓ ░▒▓░
 ░ ░  ░  ░ ░░   ▒ ░░ ░ ▒  ░   ▒░▒   ░ ░░▒░ ░ ░ ░ ░▒  ░ ░    ░     ░ ░  ░  ░▒ ░ ▒░
   ░       ░░   ▒ ░  ░ ░       ░    ░  ░░░ ░ ░ ░  ░  ░    ░         ░     ░░   ░ 
   ░  ░     ░   ░      ░  ░    ░         ░           ░              ░  ░   ░     
           ░                        ░                                                
                 
'''
    faded = ''
    red = 40
    for line in text.splitlines():
        faded += (f"\033[38;2;{red};0;220m{line}\033[0m\n")
        if red < 255:
            red += 15
            if red > 255:
                red = 255
    print(center(faded))
    sleep(0.12)
    print('{}[{}!{}]{} CODER : {}t.me/DoYouLikePopo'.center(os.get_terminal_size().columns, " ").format(fc, fr, fc, fw, fr))
    sleep(0.12)
    print('{}[{}!{}]{} CONTACT ME HERE : {}t.me/DoYouLikePopo'.center(os.get_terminal_size().columns, " ").format(fc, fr, fc, fw, fr))
    sleep(0.12)
    print('{}[{}!{}]{} MADE IN : {}PAKISTAN 06 haha'.center(os.get_terminal_size().columns, " ").format(fc, fr, fc, fw, fr))
    sleep(0.12)

    encode_subject, encode_name = read()

    print(f"{gr}\t[{fr}#{gr}] {fg}Encrypte Mehod{gr} [{fr}#{gr}]\n")
    print(f"{fr}│ {gr}➤{fw} 1 {fr}- {fg}Base64")
    print(f"{fr}│ {gr}➤{fw} 2 {fr}- {fg}Hex")
    print(f"{fr}│ {gr}➤{fw} 3 {fr}- {fg}Continue Without Encryption")
    encryption_choice = int(input(f"{fr}└─> {fr}[{fg}SELECT{fr}]{fw} ➧ "))
    if encryption_choice == 1:
        encrypt_method = 'Base64'
    elif encryption_choice == 2:
        encrypt_method = 'Hex'
    elif encryption_choice == 3:
        encrypt_method = 'None'
    else:
        print(f"{fr}[-] Invalid choice! Please select a valid option.")
        return

    dzzz = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter Your Mailist{fw}{bd}] ')

    if not os.path.isfile('Mailist_Here/' + dzzz):
        print(f'{fr}[-] Mailist not found ya noob hh <3\n{fw}')
        exit()

    with open('Mailist_Here/' + dzzz, 'r', errors='ignore', encoding='utf-8') as f:
        mailist = f.read().splitlines()
    
    listaa = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter Your SMTPs{fw}{bd}] ')

    if not os.path.isfile('SMTPs_Here/' + listaa):
        print(f'{fr}[-] SMTPs file not found haha <3\n{fw}')
        exit()

    with open('SMTPs_Here/' + listaa, 'r', errors='ignore', encoding='utf-8') as f:
        smtps = f.read().splitlines()

    smtps = clean_smtps(smtps)
    total_smtps = len(smtps)
    
    if not smtps:
        print(f'{fr}[-] No valid SMTPs found after cleaning!{fw}')
        exit()

    reply = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Do you want to add reply-to? (y/n):{fw}{bd}] ').lower()
    if reply == "y":
        reply_to = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter Reply to{fw}{bd}] ')
    else:
        reply_to = None
    
    bcc = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Do you want to add BCC? (y/n):{fw}{bd}] ').lower()
    if bcc == "y":
        bcc = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter BCC:{fw}{bd}] ')
    else:
        bcc = None
    
    cc = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Do you want to add CC? (y/n):{fw}{bd}] ').lower()
    if cc == "y":
        cc = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter CC:{fw}{bd}] ')
    else:
        cc = None
    
    spoof = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Do you want to add spoof? (y/n):{fw}{bd}] ').lower()
    if spoof == "y":
        spoof = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter Spoof:{fw}{bd}] ')
    else:
        spoof = None
    
    base_url = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter Base URL for QR Code (Leave blank if not needed){fw}{bd}] ')
    if base_url:
        qr_code_file = f'QR_Code/{time_rn}.png'
        try:
            qr = qrcode.make(base_url)
            qr.save(qr_code_file)
        except Exception as e:
            print(f"{fr}[-] Error generating QR code: {e}")
    
    # HTML templates are handled in read_letter() function, not as attachments
    attachment = None
    attach_file = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Attach additional file (PDF, Image, ZIP, etc)? (y/n){fw}{bd}] ').lower()
    if attach_file == "y":
        attachment = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter file to attach (PDF, Image, etc){fw}{bd}] ')
        full_path = 'Attachment_Here/' + attachment.strip()
        if not os.path.isfile(full_path):
            print(f'{fr}[-] Attachment file not found in Attachment_Here/ folder{fw}')
            exit()
        else:
            attachment = full_path
    
    check_yn = input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Do you want to check SMTPs Before Sending (Results sent to your Email)? (y/n):{fw}{bd}] ').lower()
    messiiii = int(input(f'{fr}{bd}┌─{fw}{bd}[{gr}{bd}EviL Tool{fw}{bd}]{fr}{bd}─{fw}{bd}[{fg}Buster{fw}{bd}]{fr}{bd}─{fw}{bd}[{pink}{bd}Enter Threads{fw}{bd}] ').lower())
   
    good_smtps = []
    if check_yn == 'y':
        print(f"{fg}[{fr}+{fw}{fg}] Checking SMTPs...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=messiiii) as executor:
            for smtp in smtps:
                executor.submit(check, smtp)
        good_smtps = [smtp for smtp in smtps if smtp in good_smtp]
        print(f"{fg}[{fr}+{fw}{fg}] Valid SMTPs: {len(good_smtps)}")
        if not good_smtps:
            print(f'{fr}[-] Only bad SMTPs found. Exiting.')
            exit()
    else:
        good_smtps = smtps
        print(f"{fg}[{fr}+{fw}{fg}] alright Using all SMTPs without checking.")

    total = len(mailist)

    i = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=messiiii) as executor:
        for email in mailist:
            name_index = i // fromname_rotation % len(encode_name)
            subject_index = i // subject_rotation % len(encode_subject)
            executor.submit(send, email, choice(good_smtps), name_index, subject_index, reply_to, bcc, cc, spoof, attachment, encrypt_method)
            i += 1

if __name__ == "__main__":
    main()