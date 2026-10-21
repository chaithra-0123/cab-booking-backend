from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from database import conn
from fastapi.responses import Response
from weasyprint import HTML
from html import escape

import re
import googlemaps
from datetime import datetime
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import secrets
import hashlib
from datetime import timedelta
import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

def send_otp_email(to_email, otp):
    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "RideEasy",
            "email": "chaidandgulkar123@gmail.com"
        },
        "to": [
            {"email": to_email}
        ],
        "subject": "RideEasy Password Reset OTP",
        "textContent": f"Your RideEasy OTP is {otp}. It expires in 5 minutes."
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=15
    )

    if response.status_code not in (200, 201, 202):
     print("Brevo status:", response.status_code)
     print("Brevo response:", response.text)
     raise HTTPException(
        status_code=502,
        detail="Unable to send OTP email."
    )
app = FastAPI()
password_hash = PasswordHash.recommended()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    name: str
    email: EmailStr
    phone: str = Field(pattern=r"^[0-9]{10}$")
    password: str = Field(min_length=8)
    role: str = "user"
class Ride(BaseModel):
    pickup_location: str
    drop_location: str
    pickup_datetime: datetime
    drop_datetime: datetime
    cab_type: str
    user_id: int
    estimated_fare: float
    payment_method: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    reset_token: str
    new_password: str = Field(min_length=8) 

class Review(BaseModel):
    ride_id: int
    user_id: int
    rating: int = Field(ge=1, le=5)
    review_text: str = ""    

@app.get("/")
def home():
    return{"Message":"Welcome to the cab booking platform"}

def validate_password(password: str):
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True

@app.post("/user")
def create_user(user: User):
    if not validate_password(user.password):
        raise HTTPException(
            status_code=422,
            detail="Password must contain a lowercase letter, uppercase letter, number, and special character."
        )

    cursor = conn.cursor()

    try:
        hashed_password = password_hash.hash(user.password)

        cursor.execute(
            """
            INSERT INTO public.users
                (name, email, phone, password_hash, role)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
            """,
            (
                user.name,
                user.email,
                user.phone,
                hashed_password,
                user.role
            )
        )

        user_id = cursor.fetchone()[0]
        conn.commit()

        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "name": user.name,
            "email": user.email
        }

    except Exception as error:
        conn.rollback()

        if getattr(error, "pgcode", None) == "23505":
            raise HTTPException(
                status_code=409,
                detail="This email is already registered."
            )

        raise HTTPException(
            status_code=500,
            detail="Unable to register user."
        )

    finally:
        cursor.close()       

@app.post("/login")
def login_user(login: LoginRequest):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT user_id, name, email, password_hash
            FROM public.users
            WHERE email = %s
            """,
            (login.email,)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        if not password_hash.verify(login.password, user[3]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        return {
            "message": "Login successful",
            "user_id": user[0],
            "name": user[1],
            "email": user[2]
        }

    finally:
        cursor.close()
# NEW CODE: Get all saved rides

# Get all saved rides
@app.get("/rides")
def get_all_rides(user_id: int = Query(...)):
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT
                ride_id,
                pickup_location,
                drop_location,
                pickup_datetime,
                drop_datetime,
                cab_type,
                user_id,
                cab_id,
                estimated_fare,
                payment_method,
                payment_status
            FROM public.rides
            WHERE user_id = %s
            ORDER BY ride_id
        """, (user_id,))

        results = cursor.fetchall()
        rides = []

        for row in results:
            rides.append({
                "ride_id": row[0],
                "pickup_location": row[1],
                "drop_location": row[2],
                "pickup_datetime": str(row[3]) if row[3] else None,
                "drop_datetime": str(row[4]) if row[4] else None,
                "cab_type": row[5],
                "user_id": row[6],
                "cab_id": row[7],
                "estimated_fare": float(row[8]) if row[8] is not None else None,
                "payment_method": row[9],
                "payment_status": row[10]
            })

        return rides

    finally:
        cursor.close()


# EXISTING CODE: Keep your original function below
@app.get("/rides/{ride_id}")
def get_ride(ride_id: int):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                ride_id,
                pickup_location,
                drop_location,
                pickup_time,
                cab_type,
                user_id,
                cab_id,
                pickup_datetime,
                drop_datetime,
                estimated_fare,
                payment_method,
                payment_status,
                status
            FROM public.rides
            WHERE ride_id = %s
            """,
            (ride_id,)
        )

        result = cursor.fetchone()

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Booking not found"
            )

        return {
            "ride_id": result[0],
            "pickup_location": result[1],
            "drop_location": result[2],
            "pickup_time": str(result[3]) if result[3] else None,
            "cab_type": result[4],
            "user_id": result[5],
            "cab_id": result[6],
            "pickup_datetime": str(result[7]) if result[7] else None,
            "drop_datetime": str(result[8]) if result[8] else None,
            "estimated_fare": float(result[9]) if result[9] is not None else None,
            "payment_method": result[10],
            "payment_status": result[11],
            "status": result[12]
        }

    finally:
        cursor.close()



@app.delete("/rides/{ride_id}")
def delete_ride(ride_id: int):
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM rides WHERE ride_id = %s",
            (ride_id,)
        )

        if cursor.rowcount == 0:
            conn.rollback()
            raise HTTPException(
                status_code=404,
                detail="Booking not found"
            )

        conn.commit()
        return {"message": "Booking deleted successfully"}

    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to delete booking"
        )
    finally:
        cursor.close()
@app.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    email = request.email.lower()

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT user_id FROM public.users WHERE LOWER(email) = %s",
            (email,)
        )
        user = cursor.fetchone()

        if user:
            otp = f"{secrets.randbelow(1000000):06d}"
            otp_hash = hashlib.sha256(otp.encode()).hexdigest()
            expires_at = datetime.now() + timedelta(minutes=5)

            cursor.execute(
                """
                INSERT INTO password_reset_otps
                    (email, otp_hash, expires_at, attempts,
                     reset_token_hash, reset_token_expires_at)
                VALUES (%s, %s, %s, 0, NULL, NULL)
                ON CONFLICT (email) DO UPDATE SET
                    otp_hash = EXCLUDED.otp_hash,
                    expires_at = EXCLUDED.expires_at,
                    attempts = 0,
                    reset_token_hash = NULL,
                    reset_token_expires_at = NULL
                """,
                (email, otp_hash, expires_at)
            )
            conn.commit()

            send_otp_email(email, otp)

        return {
            "message": "If the email is registered, an OTP will be sent."
        }

    except Exception as e:
        conn.rollback()
        print("Forgot password error:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Unable to process the request."
        )
    finally:
        cursor.close()

@app.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest):
    email = request.email.lower()
    otp_hash = hashlib.sha256(request.otp.encode()).hexdigest()

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT otp_hash, expires_at, attempts
            FROM password_reset_otps
            WHERE email = %s
            """,
            (email,)
        )

        record = cursor.fetchone()

        if record is None or record[0] is None:
            raise HTTPException(
                status_code=400,
                detail="Please request a new OTP."
            )

        if record[1] <= datetime.now():
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Please request a new one."
            )

        if record[2] >= 5:
            raise HTTPException(
                status_code=429,
                detail="Too many attempts. Please request a new OTP."
            )

        if record[0] != otp_hash:
            cursor.execute(
                """
                UPDATE password_reset_otps
                SET attempts = attempts + 1
                WHERE email = %s
                """,
                (email,)
            )
            conn.commit()

            raise HTTPException(
                status_code=400,
                detail="Incorrect OTP. Please try again."
            )

        reset_token = secrets.token_urlsafe(32)
        reset_token_hash = hashlib.sha256(
            reset_token.encode()
        ).hexdigest()

        cursor.execute(
            """
            UPDATE password_reset_otps
            SET otp_hash = NULL,
                expires_at = CURRENT_TIMESTAMP,
                reset_token_hash = %s,
                reset_token_expires_at = %s
            WHERE email = %s
            """,
            (
                reset_token_hash,
                datetime.now() + timedelta(minutes=10),
                email
            )
        )

        conn.commit()

        return {
            "message": "OTP verified successfully.",
            "reset_token": reset_token
        }

    except HTTPException:
        raise

    except Exception as e:
        conn.rollback()
        print("OTP verification error:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Unable to verify OTP."
        )

    finally:
        cursor.close()


@app.post("/reset-password")
def reset_password(request: ResetPasswordRequest):
    email = request.email.lower()

    # Validate the new password
    if not validate_password(request.new_password):
        raise HTTPException(
            status_code=400,
            detail=(
                "Password must contain an uppercase letter, "
                "a lowercase letter, a number, and a special character."
            )
        )

    # Hash the reset token
    reset_token_hash = hashlib.sha256(
        request.reset_token.encode()
    ).hexdigest()

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT reset_token_hash, reset_token_expires_at
            FROM password_reset_otps
            WHERE email = %s
            """,
            (email,)
        )

        record = cursor.fetchone()

        if (
            record is None
            or record[0] is None
            or record[1] is None
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid reset token. Please verify your OTP again."
            )

        if record[0] != reset_token_hash:
            raise HTTPException(
                status_code=400,
                detail="Invalid reset token."
            )

        if record[1] <= datetime.now():
            raise HTTPException(
                status_code=400,
                detail="Reset token expired. Please verify your OTP again."
            )

        new_password_hash = password_hash.hash(
            request.new_password
        )

        cursor.execute(
            """
            UPDATE public.users
            SET password_hash = %s
            WHERE LOWER(email) = %s
            """,
            (new_password_hash, email)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="User not found."
            )

        # Make the reset token single-use
        cursor.execute(
            """
            UPDATE password_reset_otps
            SET reset_token_hash = NULL,
                reset_token_expires_at = NULL
            WHERE email = %s
            """,
            (email,)
        )

        conn.commit()

        return {"message": "Password reset successfully."}

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        print("Password reset error:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Unable to reset password."
        )

    finally:
        cursor.close()


@app.post("/ride")
def create_ride(ride: Ride):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO public.rides (
                pickup_location,
                drop_location,
                pickup_time,
                cab_type,
                user_id,
                pickup_datetime,
                drop_datetime,
                estimated_fare,
                payment_method,
                payment_status,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING ride_id
            """,
            (
                ride.pickup_location,
                ride.drop_location,
                ride.pickup_datetime.time(),
                ride.cab_type,
                ride.user_id,
                ride.pickup_datetime,
                ride.drop_datetime,
                ride.estimated_fare,
                ride.payment_method,
                "Pending",
                "Booked"
            )
        )

        ride_id = cursor.fetchone()[0]
        conn.commit()

        return {
            "message": "Ride booked successfully",
            "ride_id": ride_id,
            "status": "Booked",
            "payment_status": "Pending"
        }

    except Exception as error:
        conn.rollback()
        print("Ride booking error:", repr(error))
        raise HTTPException(
            status_code=500,
            detail="Unable to book ride."
        )

    finally:
        cursor.close()
@app.get("/rides/{ride_id}/receipt")
def get_receipt(ride_id: int, user_id: int = Query(...)):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT
                r.ride_id,
                r.pickup_location,
                r.drop_location,
                r.pickup_datetime,
                r.drop_datetime,
                r.cab_type,
                r.estimated_fare,
                r.payment_method,
                r.payment_status,
                u.name,
                u.email
            FROM public.rides r
            JOIN public.users u ON r.user_id = u.user_id
            WHERE r.ride_id = %s
              AND r.user_id = %s
            """,
            (ride_id, user_id)
        )

        ride = cursor.fetchone()

        if ride is None:
            raise HTTPException(
                status_code=404,
                detail="Booking not found for this user"
            )

        receipt_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ text-align: center; }}
                table {{ width: 100%; border-collapse: collapse; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                td:first-child {{ font-weight: bold; width: 40%; }}
            </style>
        </head>
        <body>
            <h1>Cab Booking Receipt</h1>
            <p><b>Receipt Number:</b> {ride[0]}</p>
            <p><b>Customer:</b> {escape(str(ride[9] or ""))}</p>
            <p><b>Email:</b> {escape(str(ride[10] or ""))}</p>
            <table>
                <tr><td>Pickup</td><td>{escape(str(ride[1] or ""))}</td></tr>
                <tr><td>Destination</td><td>{escape(str(ride[2] or ""))}</td></tr>
                <tr><td>Pickup Time</td><td>{escape(str(ride[3] or ""))}</td></tr>
                <tr><td>Drop Time</td><td>{escape(str(ride[4] or ""))}</td></tr>
                <tr><td>Cab Type</td><td>{escape(str(ride[5] or ""))}</td></tr>
                <tr><td>Fare</td><td>₹{escape(str(ride[6] or 0))}</td></tr>
                <tr><td>Payment Method</td><td>{escape(str(ride[7] or ""))}</td></tr>
                <tr><td>Payment Status</td><td>{escape(str(ride[8] or ""))}</td></tr>
            </table>
            <p>Thank you for choosing our cab service!</p>
        </body>
        </html>
        """

        pdf_bytes = HTML(string=receipt_html).write_pdf()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="ride_receipt_{ride_id}.pdf"'
            }
        )

    finally:
        cursor.close()


@app.post("/reviews")
def create_review(review: Review):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO public.reviews
                (ride_id, user_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
            RETURNING review_id
            """,
            (
                review.ride_id,
                review.user_id,
                review.rating,
                review.review_text
            )
        )

        review_id = cursor.fetchone()[0]
        conn.commit()

        return {
            "message": "Review submitted successfully",
            "review_id": review_id
        }

    except Exception as error:
        conn.rollback()
        print("Review error:", repr(error))
        raise HTTPException(
            status_code=400,
            detail="Unable to submit review. Check the ride and user IDs or whether a review already exists."
        )

    finally:
        cursor.close()        


@app.get("/reviews")
def get_reviews(ride_id: int = Query(...)):
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT review_id, ride_id, user_id,
                   rating, review_text, created_at
            FROM public.reviews
            WHERE ride_id = %s
            ORDER BY created_at DESC
            """,
            (ride_id,)
        )

        rows = cursor.fetchall()

        return [
            {
                "review_id": row[0],
                "ride_id": row[1],
                "user_id": row[2],
                "rating": row[3],
                "review_text": row[4],
                "created_at": str(row[5]) if row[5] else None
            }
            for row in rows
        ]

    finally:
        cursor.close()        