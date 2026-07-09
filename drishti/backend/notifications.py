"""Twilio integration for SMS and Voice call notifications."""

import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

logger = logging.getLogger("drishti.notifications")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
TARGET_PHONE_NUMBER = os.getenv("TARGET_PHONE_NUMBER")

def _get_twilio_client():
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, TARGET_PHONE_NUMBER]) or TWILIO_ACCOUNT_SID == "your_twilio_account_sid":
        return None
    try:
        from twilio.rest import Client
        return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except ImportError:
        logger.warning("Twilio package is not installed. Run `pip install twilio`.")
        return None

def send_sms_alert(message: str) -> Optional[str]:
    """Send an SMS via Twilio. Returns the message SID if successful."""
    client = _get_twilio_client()
    if not client:
        logger.info(f"[SIMULATED SMS] {message}")
        return "SIMULATED_SMS"

    try:
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=TARGET_PHONE_NUMBER
        )
        logger.info(f"SMS sent successfully. SID: {sms.sid}")
        return sms.sid
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return None

def send_voice_alert(message: str) -> Optional[str]:
    """Trigger a Voice Call via Twilio to read out the message."""
    client = _get_twilio_client()
    if not client:
        logger.info(f"[SIMULATED VOICE CALL] {message}")
        return "SIMULATED_CALL"

    try:
        # Twilio uses TwiML (XML) to define voice instructions
        # We use the <Say> verb to read the message.
        twiml = f"<Response><Say voice='Polly.Joanna-Neural'>{message}</Say></Response>"
        
        call = client.calls.create(
            twiml=twiml,
            from_=TWILIO_PHONE_NUMBER,
            to=TARGET_PHONE_NUMBER
        )
        logger.info(f"Voice call initiated. SID: {call.sid}")
        return call.sid
    except Exception as e:
        logger.error(f"Failed to initiate Voice Call: {e}")
        return None
