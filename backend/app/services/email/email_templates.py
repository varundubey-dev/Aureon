def generate_otp_email_template(
    otp: str,
) -> str:
    return f"""
    <html>
        <body>
            <h2>Your Aureon Verification Code</h2>

            <p>
                Your OTP code is:
            </p>

            <h1>{otp}</h1>

            <p>
                This code expires in 5 minutes.
            </p>
        </body>
    </html>
    """


def generate_password_reset_email_template(
    otp: str,
) -> str:

    return f"""
    <html>
        <body>
            <h2>
                Aureon Password Reset
            </h2>

            <p>
                Your password reset OTP is:
            </p>

            <h1>{otp}</h1>

            <p>
                This code expires in 5 minutes.
            </p>

            <p>
                If you did not request a password reset,
                please ignore this email.
            </p>
        </body>
    </html>
    """
