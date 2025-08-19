import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import os
from wichteln.models import Participant


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        
    async def send_participant_codes(self, participants: List[Participant], exchange_name: str):
        """Send unique codes to all participants."""
        if not self.sender_email or not self.sender_password:
            print("Email credentials not configured. Printing codes instead:")
            for participant in participants:
                print(f"{participant.name} ({participant.email}): {participant.code}")
            return
            
        context = ssl.create_default_context()
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.sender_password)
                
                for participant in participants:
                    message = self._create_code_email(participant, exchange_name)
                    server.sendmail(self.sender_email, participant.email, message.as_string())
                    
        except Exception as e:
            print(f"Failed to send emails: {e}")
            print("Printing codes instead:")
            for participant in participants:
                print(f"{participant.name} ({participant.email}): {participant.code}")
    
    def _create_code_email(self, participant: Participant, exchange_name: str) -> MIMEMultipart:
        """Create email with participant's unique code."""
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Your Secret Santa Code for {exchange_name}"
        message["From"] = self.sender_email
        message["To"] = participant.email
        
        text = f"""
        Hi {participant.name}!
        
        You've been added to the Secret Santa exchange: {exchange_name}
        
        Your unique code is: {participant.code}
        
        Use this code to find out who you're buying a gift for when the matches are ready.
        
        Happy gifting! 🎁
        """
        
        html = f"""
        <html>
        <body>
            <h2>🎁 Secret Santa Exchange</h2>
            <p>Hi {participant.name}!</p>
            <p>You've been added to the Secret Santa exchange: <strong>{exchange_name}</strong></p>
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 15px 0;">
                <p>Your unique code is: <strong style="font-size: 18px; color: #d32f2f;">{participant.code}</strong></p>
            </div>
            <p>Use this code to find out who you're buying a gift for when the matches are ready.</p>
            <p>Happy gifting! 🎁</p>
        </body>
        </html>
        """
        
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        
        message.attach(part1)
        message.attach(part2)
        
        return message


email_service = EmailService()