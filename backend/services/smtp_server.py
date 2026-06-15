"""HawkPhish - Built-in SMTP Server (from MailSpoof)"""
import socket
import smtplib
import threading
import signal
import re
from typing import List
from datetime import datetime


class SMTPSession:
    """Raw SMTP session handler for built-in server."""

    def __init__(self, client_sock, addr, server):
        self.sock = client_sock
        self.addr = addr
        self.server = server
        self.client_id = f"{addr[0]}:{addr[1]}"
        self.mail_from = ""
        self.rcpt_to: List[str] = []
        self.last_relay_error = ""

    def run(self):
        print(f"[{self.client_id}] New connection")
        self._send(f"220 HawkPhish SMTP Server Ready")

        while self.server.running:
            try:
                data = self._recv_line()
                if not data:
                    break
                if not self._handle_command(data.strip()):
                    break
            except socket.timeout:
                break
            except Exception as exc:
                print(f"[{self.client_id}] Error: {exc}")
                break

        self.sock.close()
        print(f"[{self.client_id}] Disconnected")

    def _recv_line(self) -> str:
        buf = b""
        while True:
            chunk = self.sock.recv(1)
            if not chunk:
                return ""
            buf += chunk
            if buf.endswith(b"\r\n"):
                return buf.decode("utf-8", errors="ignore")

    def _recv_data(self) -> str:
        chunks: List[str] = []
        while True:
            part = self.sock.recv(4096).decode("utf-8", errors="ignore")
            chunks.append(part)
            if "\r\n.\r\n" in part:
                break
        return "".join(chunks).split("\r\n.\r\n")[0]

    def _send(self, text: str):
        self.sock.sendall(f"{text}\r\n".encode())

    def _handle_command(self, cmd: str) -> bool:
        upper = cmd.upper()

        if upper.startswith("EHLO") or upper.startswith("HELO"):
            self._send(f"250-HawkPhish Hello {self.addr[0]}")
            self._send("250 HELP")

        elif upper.startswith("MAIL FROM:"):
            self.mail_from = self._extract_email(cmd)
            self._send("250 OK")

        elif upper.startswith("RCPT TO:"):
            rcpt = self._extract_email(cmd)
            self.rcpt_to.append(rcpt)
            self._send("250 OK")

        elif upper == "DATA":
            self._send("354 End data with <CR><LF>.<CR><LF>")
            email_data = self._recv_data()
            self.last_relay_error = ""
            success = self._process_email(email_data)
            self.server.emails_processed += 1
            if success:
                self._send("250 OK Message queued for delivery")
            else:
                err = self.last_relay_error or "Delivery failed"
                self._send(f"550 {err}")
            self.mail_from = ""
            self.rcpt_to = []

        elif upper == "QUIT":
            self._send("221 Bye")
            return False

        elif upper.startswith("RSET"):
            self.mail_from = ""
            self.rcpt_to = []
            self._send("250 OK")

        else:
            self._send("500 Command not recognized")

        return True

    @staticmethod
    def _extract_email(smtp_line: str) -> str:
        match = re.search(r"<(.+?)>", smtp_line)
        if match:
            return match.group(1)
        parts = smtp_line.split()
        return parts[-1].strip("<>").strip() if len(parts) > 1 else ""

    def _process_email(self, email_data: str) -> bool:
        if not self.mail_from or not self.rcpt_to:
            return False
        successes = 0
        for rcpt in self.rcpt_to:
            if self._relay(self.mail_from, rcpt, email_data):
                successes += 1
        return successes > 0

    def _relay(self, mail_from: str, rcpt_to: str, email_data: str) -> bool:
        try:
            domain = rcpt_to.split("@")[1]
        except IndexError:
            self.last_relay_error = "Invalid recipient domain"
            return False

        mx_servers = self._resolve_mx(domain)
        if not mx_servers:
            self.last_relay_error = f"No MX records found for {domain}"
            return False

        for mx in mx_servers:
            try:
                with smtplib.SMTP(mx, 25, timeout=15) as server:
                    payload = f"From: {mail_from}\r\nTo: {rcpt_to}\r\n{email_data}"
                    server.sendmail(mail_from, [rcpt_to], payload)
                return True
            except Exception:
                continue

        self.last_relay_error = "All MX relays failed"
        return False

    def _resolve_mx(self, domain: str) -> List[str]:
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, "MX")
            return [str(r.exchange).rstrip(".") for r in sorted(answers, key=lambda x: x.preference)]
        except Exception:
            pass

        fallbacks = [f"mail.{domain}", f"mx.{domain}", f"mx1.{domain}"]
        working = []
        for host in fallbacks:
            try:
                socket.gethostbyname(host)
                working.append(host)
            except Exception:
                pass
        return working if working else [domain]


class HawkPhishSMTPServer:
    """Built-in SMTP server for local testing and direct MX relay."""

    def __init__(self, host: str = "0.0.0.0", port: int = 2525):
        self.host = host
        self.port = port
        self.running = False
        self.connections = 0
        self.emails_processed = 0
        self._thread = None
        self._sock = None

    def _bind(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(10)
        self.running = True

    def _serve(self):
        while self.running:
            try:
                client, addr = self._sock.accept()
                self.connections += 1
                session = SMTPSession(client, addr, self)
                t = threading.Thread(target=session.run, daemon=True)
                t.start()
            except OSError:
                if self.running:
                    raise

    def start(self):
        self._bind()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        return {"status": "running", "host": self.host, "port": self.port}

    def stop(self):
        self.running = False
        if self._sock:
            self._sock.close()
        return {"status": "stopped", "connections": self.connections, "emails_processed": self.emails_processed}

    def status(self):
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "connections": self.connections,
            "emails_processed": self.emails_processed,
        }
