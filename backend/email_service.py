import os
import html
import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_FROM_EMAIL = os.getenv("BREVO_FROM_EMAIL", "info@quantumpharmx.com")
BREVO_FROM_NAME = os.getenv("BREVO_FROM_NAME", "Quantum PharmX")

def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    if not BREVO_API_KEY:
        print(f"MOCK EMAIL [To: {to_email}] [Subject: {subject}]")
        print(body)
        # Fail if running in production (Render) without an API key
        if os.environ.get("RENDER"):
            print("ERROR: BREVO_API_KEY is missing in Render Environment Variables.")
            return False
        return True
        
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {"name": BREVO_FROM_NAME, "email": BREVO_FROM_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
    }
    
    if is_html:
        payload["htmlContent"] = body
    else:
        payload["textContent"] = body
            
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print(f"Email sent successfully to {to_email}: {response.json()}")
        return True
    except Exception as e:
        print(f"Failed to send email via Brevo: {e}")
        if isinstance(e, requests.exceptions.HTTPError):
            print(f"Response data: {e.response.text}")
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
