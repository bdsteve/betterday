# simple_auth/sawa/email_service/email_service.py

from postmarker.core import PostmarkClient
from sawa.config import config

postmark_api_key = config.POSTMARK_API_KEY
postmark_sender_email = config.POSTMARK_SENDER_EMAIL

postmark = PostmarkClient(postmark_api_key)

def generate_token_email_body(token):
    return f"""
    <html>
    <head>
        <style>
            .container {{
                font-family: Arial, sans-serif;
                margin: 0 auto;
                padding: 20px;
                max-width: 600px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }}
            .header {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin-bottom: 20px;
            }}
            .body {{
                font-size: 16px;
                color: #555;
                margin-bottom: 20px;
            }}
            .token {{
                font-size: 20px;
                font-weight: bold;
                color: #007bff;
                margin: 20px 0;
            }}
            .footer {{
                font-size: 14px;
                color: #999;
                margin-top: 30px;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">Your Superintendent App Login Code</div>
            <div class="body">
                <p>Hello,</p>
                <p>Here is your app login code. Please copy/paste to complete your login. This token is valid for a limited time, so be sure to use it promptly.</p>
                <div class="token">{token}</div>
                <p>If you did not request this token, please ignore this email or contact support if you have any concerns.</p>
            </div>
            <div class="footer">
                <p>Thank you,</p>
                <p>The Tech4Equity Team</p>
            </div>
        </div>
    </body>
    </html>
    """

def send_email(to, otp):
    body = generate_token_email_body(otp)
    try:
        response = postmark.emails.send(
            From=postmark_sender_email,
            To=to,
            Subject=f"{otp} is your Sup App login code",
            HtmlBody=body
        )
        return response
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return None

# Example usage
# def send_token_email(to, token):
#    subject = "Your One-Time Access Token"
#    body = generate_token_email_body(token)
#    return send_email(to, subject, body)
