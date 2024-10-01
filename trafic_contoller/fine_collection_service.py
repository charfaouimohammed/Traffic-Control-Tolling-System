from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import motor.motor_asyncio
import httpx
import aiosmtplib
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


from email.message import EmailMessage



app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient("mongodb://localhost:27017")
db = client["traffic_control"]

# Mailtrap SMTP settings
MAILTRAP_USERNAME = "48b1326a30f68b"
MAILTRAP_PASSWORD = "7343588c5713cf"
MAILTRAP_HOST = "sandbox.smtp.mailtrap.io"
MAILTRAP_PORT = 2525

# Models
class SpeedingViolation(BaseModel):
    license_number: str
    speed: float
    timestamp: str

# Function to get vehicle owner information from the registration service
async def get_owner_info(license_number):
    response:str
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:6002/vehicleinfo/{license_number}")
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as exc:
        raise HTTPException(status_code=500, detail=f"Error contacting Vehicle Registration Service: {exc}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=response.status_code, detail=f"Vehicle not found: {exc}")

# Function to send an email
async def send_email(email_content,receve_mail):
    sender = "from@example.com"
    receiver = receve_mail
    subject = "Speeding Violation Fine"
    content = email_content

    # Creating the MIME message
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    
    # Attaching the email body content
    msg.attach(MIMEText(content, 'html'))

    # Connect to the SMTP server
    try:
        with smtplib.SMTP("sandbox.smtp.mailtrap.io", 25) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login("48b1326a30f68b", "7343588c5713cf")
            server.sendmail(sender, receiver, msg.as_string())  # Send the email
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")
    
    
    
    
    
    


# Endpoint to collect fine for a speeding violation
@app.post("/collectfine")
async def collect_fine(violation: SpeedingViolation):
    fine_amount = calculate_fine(violation.speed)

    # Store fine information initially without owner details
    fine_data = {
        "license_number": violation.license_number,
        "speed": violation.speed,
        "fine_amount": fine_amount,
        "timestamp": violation.timestamp
    }
    result = await db.fines.insert_one(fine_data)

    # Get vehicle owner information from the registration service
    owner_info = await get_owner_info(violation.license_number)

    # Update the fine record with owner information
    try:
        await db.fines.update_one(
            {"_id": result.inserted_id},
            {"$set": {
                "owner_name": owner_info.get("owner_name"),
                "email": owner_info.get("email")
            }}
        )

        # Send an email to the vehicle owner
        email_content = f"""
        <html>
        <head>
            <title>Speeding Violation Fine Notification</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 80%;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                }}
                .header {{
                    background-color: #f8f8f8;
                    padding: 10px;
                    text-align: center;
                    border-bottom: 1px solid #ddd;
                }}
                .footer {{
                    margin-top: 20px;
                    padding: 10px;
                    text-align: center;
                    font-size: 12px;
                    color: #777;
                    border-top: 1px solid #ddd;
                }}
                .unsubscribe {{
                    margin-top: 10px;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Traffic Control System</h2>
                    <p>Notification of Speeding Violation</p>
                </div>
                <p>Dear {owner_info.get('owner_name')},</p>
                <p>You have been fined <strong>{int(fine_amount)}</strong> for speeding at <strong>{int(violation.speed)} km/h</strong> on <strong>{violation.timestamp}</strong>.</p>
                <p>We encourage you to adhere to speed limits to ensure safety on the roads.</p>
                <p>Best regards,<br>
                Traffic Control System</p>
                <div class="footer">
                    <p>This is an automated message. Please do not reply.</p>
                    <p class="unsubscribe">If you wish to unsubscribe from these notifications, please click <a href="unsubscribe_link_here">here</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """

        
        #await send_email(owner_info.get("email"), "Speeding Violation Fine", email_content)
        await send_email(email_content,owner_info.get("email"))

        return {"message": "Fine recorded and email sent successfully", "fine_id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording fine or sending email: {e}")

# Function to calculate fine based on speed
def calculate_fine(speed):
    base_fine = 100  # Base fine amount
    if speed > 60:
        return base_fine + (speed - 60) * 10  # $10 fine for each km/h above the limit
    return base_fine

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6001)
