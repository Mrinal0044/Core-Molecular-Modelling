from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import random
import string
from datetime import datetime, timedelta
import json

from backend.database import engine, Base, get_db, User, OTPRequest, Submission, DockingJob
from backend.email_service import send_otp_email, send_submission_notification
from backend.app.services.docking import DockingService
from backend.app.services.prediction import BindingAffinityService
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Quantum PharmX Backend")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models for requests
class SignupRequest(BaseModel):
    name: str
    company_name: str
    company_address: str
    email: str
    mobile: str
    whatsapp: Optional[str] = None
    source: Optional[str] = None

class OTPRequestSchema(BaseModel):
    email: str

class OTPVerifySchema(BaseModel):
    email: str
    otp: str

class SubmissionSchema(BaseModel):
    email: str
    formData: Dict[str, Any]


@app.post("/api/signup", status_code=status.HTTP_201_CREATED)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered. Please login using OTP.")
    
    new_user = User(
        name=req.name,
        company_name=req.company_name,
        company_address=req.company_address,
        email=req.email,
        mobile=req.mobile,
        whatsapp=req.whatsapp,
        source=req.source
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}


@app.post("/api/request-otp")
def request_otp(req: OTPRequestSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not found. Please sign up first.")
    
    # Generate 6-digit OTP
    otp_code = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    
    # Store OTP
    otp_record = OTPRequest(
        user_id=user.id,
        email=user.email,
        otp=otp_code,
        expires_at=expires_at
    )
    db.add(otp_record)
    db.commit()
    
    # Send email synchronously to catch errors
    email_sent = send_otp_email(user.email, otp_code)
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email. Please ensure email service is correctly configured."
        )
    
    return {"message": "OTP sent successfully"}


@app.post("/api/verify-otp")
def verify_otp(req: OTPVerifySchema, db: Session = Depends(get_db)):
    # Find latest valid OTP for email
    otp_record = db.query(OTPRequest).filter(
        OTPRequest.email == req.email,
        OTPRequest.otp == req.otp,
        OTPRequest.is_used == False,
        OTPRequest.expires_at > datetime.utcnow()
    ).order_by(OTPRequest.created_at.desc()).first()
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Mark as used
    otp_record.is_used = True
    db.commit()
    
    user = db.query(User).filter(User.id == otp_record.user_id).first()
    
    return {
        "message": "OTP verified successfully",
        "user": {
            "name": user.name,
            "email": user.email,
            "company": user.company_name
        }
    }


@app.post("/api/submit-form")
def submit_form(req: SubmissionSchema, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Save submission
    submission = Submission(
        user_id=user.id,
        data=json.dumps(req.formData)
    )
    db.add(submission)
    db.commit()
    
    # Send Notification to Admins in background
    user_info = {
        "name": user.name,
        "company_name": user.company_name,
        "email": user.email,
        "mobile": user.mobile
    }
    background_tasks.add_task(send_submission_notification, user_info, req.formData)
    
    # Process molecules and targets
    molecules = req.formData.get("molecules", [])
    targets = req.formData.get("targetProteins", [])
    capabilities = req.formData.get("capabilities", [])
    
    # We will submit a job for each combination of molecule and target
    # In a real app, you might want a single job for a batch, or multiple jobs
    job_ids = []
    
    # We will just take the first target if available, or a default
    default_target = targets[0] if targets else "1CRN"

    for mol in molecules:
        if mol.strip() == "": continue
        # Dispatch docking task
        job_id = DockingService.submit_job(user.id, default_target, mol)
        job_ids.append(job_id)
    
    return {
        "message": "Pipeline initialized successfully",
        "job_ids": job_ids
    }


@app.get("/api/job-status/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    status_data = DockingService.get_job_status(job_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if status_data["result_data"]:
        # Parse it back to json
        status_data["result_data"] = json.loads(status_data["result_data"])
        
    return status_data

# Mount frontend directory to serve static files (index.html, css, js)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
