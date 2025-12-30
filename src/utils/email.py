import smtplib
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from dotenv import load_dotenv
import markdown

load_dotenv()


def send_email(
    subject: str,
    message: str,
    to_email: Optional[str] = None,
    recipient_name: Optional[str] = None
) -> bool:
    """
    Send an email with markdown-formatted content converted to HTML.
    
    Args:
        subject: Email subject line
        message: Markdown-formatted message content
        to_email: Recipient email address (defaults to TO_EMAIL from .env if not provided)
        recipient_name: Optional recipient name for personalization
        
    Returns:
        True if email was sent successfully, False otherwise
        
    Raises:
        ValueError: If required environment variables are missing
        smtplib.SMTPException: If email sending fails
    """
    # Read SMTP configuration from environment variables
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", smtp_username)
    from_name = os.getenv("FROM_NAME", "LeetCode AI Revision")
    
    # Get recipient email (use parameter or default from .env)
    recipient_email = to_email or os.getenv("TO_EMAIL")
    if not recipient_email:
        raise ValueError("Recipient email is required. Either provide 'to_email' parameter or set TO_EMAIL in .env file")
    
    # Validate required configuration
    if not all([smtp_server, smtp_username, smtp_password]):
        missing = []
        if not smtp_server:
            missing.append("SMTP_SERVER")
        if not smtp_username:
            missing.append("SMTP_USERNAME")
        if not smtp_password:
            missing.append("SMTP_PASSWORD")
        raise ValueError(f"Missing required email configuration in .env: {', '.join(missing)}")
    
    # Convert markdown to HTML
    html_body = markdown.markdown(
        message,
        extensions=['extra', 'codehilite', 'fenced_code']
    )
    
    # Wrap HTML content in styled email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            pre {{
                background-color: #f4f4f4;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 12px;
                overflow-x: auto;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                margin-top: 24px;
                margin-bottom: 16px;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 0;
                padding-left: 16px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    # Create email message with both plain text and HTML versions
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{from_name} <{from_email}>"
    msg['To'] = recipient_email
    
    # Create plain text version (strip markdown formatting for readability)
    # Simple markdown to plain text conversion
    plain_text = message
    # Remove markdown code blocks
    plain_text = re.sub(r'```[\s\S]*?```', '', plain_text)
    # Remove markdown headers
    plain_text = re.sub(r'^#+\s+', '', plain_text, flags=re.MULTILINE)
    # Remove markdown bold/italic
    plain_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', plain_text)
    plain_text = re.sub(r'\*([^\*]+)\*', r'\1', plain_text)
    # Remove markdown links but keep text
    plain_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', plain_text)
    
    # Attach both plain text and HTML parts
    part1 = MIMEText(plain_text, 'plain')
    part2 = MIMEText(html_content, 'html')
    
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        # Create SMTP connection based on port
        if smtp_port == 465:
            # Use SSL for port 465
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            # Use TLS for port 587 or other ports
            server = smtplib.SMTP(smtp_server, smtp_port)
            if smtp_port == 587:
                server.starttls()
        
        try:
            # Login and send email
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        finally:
            server.quit()
        
        return True
    except smtplib.SMTPException as e:
        print(f"Error sending email: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        raise

