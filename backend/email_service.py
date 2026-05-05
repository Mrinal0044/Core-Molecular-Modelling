import smtplib
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"MOCK EMAIL [To: {to_email}] [Subject: {subject}]")
        print(body)
        return True
        
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject

        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_otp_email(to_email: str, otp: str):
    subject = "Quantum PharmX - Your Login OTP"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Quantum PharmX Authentication</h2>
            <p>Your One-Time Password (OTP) for access is:</p>
            <h1 style="color: #0ea5e9; font-size: 32px; letter-spacing: 2px;">{otp}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you did not request this code, please ignore this email.</p>
        </body>
    </html>
    """
    return send_email(to_email, subject, body, is_html=True)

def send_submission_notification(user_info: dict, submission_data: dict):
    recipients = ["darryllfonseca@gmail.com"]
    subject = f"New Quantum PharmX Submission - {user_info.get('company_name', 'Unknown')}"
    
    # Format the submission data nicely with cleaner labels
    label_map = {
        "molecules": "Molecules",
        "targetProtein": "Target Proteins",
        "mdDuration": "MD Duration (ns)",
        #"mdTemp": "MD Temp (K)",
        "mdEnsemble": "MD Ensemble"
    }
    
    def format_val(v):
        if isinstance(v, str):
            # Escape HTML and then replace newlines with <br>
            return html.escape(v).replace('\n', '<br>')
        return str(v)

    details_html = "".join([
        f"<li><strong>{label_map.get(k, k)}:</strong> {format_val(v)}</li>" 
        for k, v in submission_data.items() 
        if k not in ('capabilities', 'simulations') and v
    ])
    
    capabilities = submission_data.get('capabilities', [])
    if isinstance(capabilities, list):
        cap_str = ", ".join(capabilities)
    else:
        cap_str = str(capabilities)
        
    simulations = submission_data.get('simulations', [])
    if isinstance(simulations, list):
        sim_str = ", ".join(simulations)
    else:
        sim_str = str(simulations)

    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #0ea5e9;">New Platform Usage Alert</h2>
            <p>A new research submission has been initialized via the Quantum PharmX webform.</p>
            
            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">User Details</h3>
            <ul>
                <li><strong>Name:</strong> {user_info.get('name')}</li>
                <li><strong>Company:</strong> {user_info.get('company_name')}</li>
                <li><strong>Email:</strong> {user_info.get('email')}</li>
                <li><strong>Mobile:</strong> {user_info.get('mobile')}</li>
            </ul>
            
            <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 5px;">Submission Details</h3>
            <ul>
                {details_html}
                <li><strong>Capabilities Selected:</strong> {cap_str}</li>
                <li><strong>Simulations Selected:</strong> {sim_str}</li>
            </ul>
        </body>
    </html>
    """
    
    for recipient in recipients:
        send_email(recipient, subject, body, is_html=True)
