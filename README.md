# Cab Booking Platform — Backend

## 1. Project Introduction

The Cab Booking Platform is a web application that enables users to register, log in, book cabs, manage their bookings, download booking receipts, and submit ratings and reviews.

This repository contains the backend developed using Python, FastAPI, and PostgreSQL. It exposes REST API endpoints that process frontend requests, validate user information, manage ride records, and interact with the database.

## 2. Project Research

Cab booking applications need reliable backend services to manage user accounts, booking information, payment details, and customer feedback.

This project provides backend functionality for:
- User registration and login.
- Password validation and secure password hashing.
- Forgot-password and email OTP verification.
- Password resetting using a time-limited reset token.
- Creating, retrieving, listing, and deleting ride bookings.
- Generating and downloading PDF booking receipts.
- Submitting and retrieving customer reviews.
- Storing application data in PostgreSQL.

These services allow the React frontend and backend to communicate through HTTP APIs.

## 3. Technology Stack and Reasons

| Technology | Purpose |
|---|---|
| Python | Implements the backend business logic. |
| FastAPI | Defines REST APIs and handles HTTP requests. |
| PostgreSQL | Stores users, ride bookings, password-reset information, and reviews. |
| Psycopg2 | Connects Python to the PostgreSQL database. |
| Pydantic | Validates request data such as email addresses, phone numbers, and passwords. |
| pwdlib | Hashes passwords and verifies login credentials. |
| Brevo API | Sends password-reset OTP emails. |
| WeasyPrint | Generates PDF booking receipts from HTML. |
| Requests | Sends HTTP requests to the Brevo email API. |
| python-dotenv | Loads environment variables from a `.env` file. |
| Uvicorn | Runs the FastAPI application server. |
| Git and GitHub | Provide source-code version control and hosting. |

## 4. Libraries and Their Uses

### FastAPI
Defines backend endpoints for user accounts, cab bookings, password recovery, receipts, and reviews.

### Pydantic
Validates incoming request data. The code uses email validation, a ten-digit phone-number pattern, minimum password length, and a rating range of 1–5.

### pwdlib
Creates password hashes during registration and verifies them during login. Passwords are not stored directly as plaintext by the registration endpoint.

### Psycopg2
Executes SQL queries and communicates with PostgreSQL to create, retrieve, update, and delete relevant records.

### Brevo API and Requests
The Brevo SMTP email API is called through the Requests library to send password-reset OTPs to users.

### python-dotenv
Loads environment variables, including `BREVO_API_KEY`, from the local environment.

### WeasyPrint
Converts an HTML receipt containing the booking and customer information into a downloadable PDF document.

### Uvicorn
Runs the FastAPI application during development.

## 5. Backend Features

### 5.1 User Registration
- Accepts name, email, phone number, password, and optional role.
- Validates the password for lowercase letters, uppercase letters, numbers, and special characters.
- Hashes the password before storing it.
- Returns the newly created user ID.
- Handles duplicate-email registration.

### 5.2 User Login
- Accepts an email address and password.
- Retrieves the matching user record.
- Verifies the submitted password against the stored password hash.
- Returns the user's ID, name, and email following successful login.

### 5.3 Forgot Password
- Accepts the user's email address.
- Generates a six-digit OTP for a registered email.
- Stores the OTP hash and its expiration time in the database.
- Sends the OTP through Brevo.
- Sets the OTP validity period to five minutes.

### 5.4 OTP Verification
- Validates the OTP submitted by the user.
- Checks expiration and failed verification attempts.
- Limits OTP verification to five attempts.
- Generates a secure reset token after successful verification.
- Sets the reset token to expire after ten minutes.

### 5.5 Reset Password
- Validates the new password.
- Verifies the reset token and its expiration.
- Hashes the new password.
- Updates the user's password in PostgreSQL.
- Invalidates the reset token after successful use.

### 5.6 Ride Booking
- Accepts pickup and drop locations.
- Stores pickup and drop date-time values.
- Records the selected cab type, user ID, estimated fare, and payment method.
- Creates the ride record and returns its generated ride ID.
- Sets the initial ride status to `Booked` and payment status to `Pending`.

### 5.7 Booking History
- Retrieves all ride records for a specified user ID.
- Returns pickup and drop details, cab type, ride ID, fare, payment method, payment status, and related fields.

### 5.8 Retrieve a Single Booking
- Fetches a ride using its ride ID.
- Returns the booking information when a record exists.
- Returns a not-found response when the booking does not exist.

### 5.9 Delete a Booking
- Deletes a booking using its ride ID.
- Returns a success message when the record is deleted.
- Returns an error when the booking cannot be found or deleted.

### 5.10 PDF Receipt Generation
- Retrieves ride and customer information from PostgreSQL.
- Creates an HTML receipt.
- Converts the HTML into a PDF using WeasyPrint.
- Returns the PDF as a downloadable file.
- Checks that the specified ride belongs to the supplied user ID.

### 5.11 Submit Ratings and Reviews
- Accepts ride ID, user ID, star rating, and review text.
- Validates that the rating is between one and five.
- Stores the review in PostgreSQL.
- Returns the generated review ID after successful submission.

### 5.12 Retrieve Customer Reviews
- Retrieves reviews for a specified ride ID.
- Returns the reviewer ID, rating, review text, and creation time.
- Orders reviews by their creation time, newest first.

## 6. API Endpoints

The following endpoints are defined in `main.py`.

| HTTP Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Returns the backend welcome message. |
| POST | `/user` | Registers a new user. |
| POST | `/login` | Verifies login credentials. |
| GET | `/rides?user_id={user_id}` | Retrieves all bookings for a user. |
| GET | `/rides/{ride_id}` | Retrieves an individual booking. |
| DELETE | `/rides/{ride_id}` | Deletes a booking. |
| POST | `/forgot-password` | Requests a password-reset OTP. |
| POST | `/verify-otp` | Verifies the OTP and generates a reset token. |
| POST | `/reset-password` | Resets the password using a valid reset token. |
| POST | `/ride` | Creates a new cab booking. |
| GET | `/rides/{ride_id}/receipt?user_id={user_id}` | Generates and downloads a PDF receipt. |
| POST | `/reviews` | Creates a customer review. |
| GET | `/reviews?ride_id={ride_id}` | Retrieves reviews for a ride. |

### Example API requests

**Register a user — `POST /user`**

```json
{
  "name": "Example User",
  "email": "user@example.com",
  "phone": "9876543210",
  "password": "Example@123",
  "role": "user"
}
```

**Create a cab booking — `POST /ride`**

```json
{
  "pickup_location": "Location A",
  "drop_location": "Location B",
  "pickup_datetime": "2026-10-25T10:00:00",
  "drop_datetime": "2026-10-25T11:00:00",
  "cab_type": "Sedan",
  "user_id": 1,
  "estimated_fare": 350.0,
  "payment_method": "Cash"
}
```

These are example request bodies. The actual IDs, dates, and values must correspond to valid data in your local application.

## 7. Database Integration

The backend uses PostgreSQL through the Psycopg2 library.

The supplied code interacts with these database tables:

| Table | Purpose |
|---|---|
| `users` | Stores user profile information and password hashes. |
| `rides` | Stores booking locations, dates, vehicle details, fare, payment information, and ride status. |
| `password_reset_otps` | Stores hashed OTPs, expiration times, attempt counts, and reset-token hashes. |
| `reviews` | Stores ride ratings and written feedback. |

The `database.py` file creates the PostgreSQL connection. Database credentials must be configured for the environment in which the application runs.

**Security:** Never commit database passwords, API keys, or other secrets to GitHub. The `.env` file should be excluded using `.gitignore`.

## 8. Cross-Origin Resource Sharing (CORS)

The backend uses FastAPI's `CORSMiddleware` to allow requests from the configured local frontend origins:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

These settings support communication with the Vite development server. Production deployments require the appropriate frontend origin to be configured.

## 9. How to Run the Backend

### Prerequisites
- Python
- PostgreSQL
- Git
- A configured PostgreSQL database
- A Brevo API key for password-reset email delivery

### Step 1: Clone the repository

```bash
git clone https://github.com/chaithra-0123/cab-booking-backend.git
```

### Step 2: Enter the project directory

```bash
cd cab-booking-backend
```

### Step 3: Create and activate a virtual environment

```bash
python -m venv env
```

On Windows PowerShell:

```powershell
.\env\Scripts\Activate.ps1
```

### Step 4: Install the dependencies

```bash
pip install fastapi uvicorn psycopg2-binary "pydantic[email]" "pwdlib[argon2]" requests python-dotenv weasyprint googlemaps
```

### Step 5: Configure environment variables

Create a local `.env` file for the required environment variables, including:

```text
BREVO_API_KEY=your_brevo_api_key
```

Configure your PostgreSQL connection in `database.py` to match your local database. Do not use the placeholder API key above as a real credential.

### Step 6: Start the backend

```bash
uvicorn main:app --reload
```

### Step 7: Open the API documentation

After the server starts, visit:

`http://127.0.0.1:8000/docs`

FastAPI's Swagger UI provides an interactive interface for inspecting and testing the API endpoints.

## 10. Frontend Integration

The backend is designed to communicate with the React frontend through HTTP APIs.

**Frontend repository:**  
https://github.com/chaithra-0123/cab-booking-frontend

**Backend repository:**  
https://github.com/chaithra-0123/cab-booking-backend

The frontend sends requests to the backend to register and authenticate users, create and retrieve bookings, download receipts, and manage reviews.

## 11. Future Enhancements

- Token-based authentication and authorization.
- Stronger authorization checks across booking and review endpoints.
- Driver assignment and driver management.
- Real-time ride tracking.
- Integration with an online payment gateway.
- Deployment configuration for a production environment.
- Automated API tests and improved logging.

## 12. Conclusion

The Cab Booking Platform backend demonstrates how Python, FastAPI, and PostgreSQL can support user account management, password recovery, cab booking operations, PDF receipt generation, and customer reviews.

The REST API architecture connects the backend with a separate React frontend, while PostgreSQL stores the application's main records.
