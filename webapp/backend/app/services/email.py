"""
Email service for sending notifications.
Uses Resend for email delivery.
"""

from typing import Optional
import httpx

from app.config import get_settings
from app.models.research import ResearchJob
from app.models.user import User

settings = get_settings()


async def send_email(
    to: str,
    subject: str,
    html: str,
    text: Optional[str] = None
) -> bool:
    """Send an email using Resend API."""
    if not settings.resend_api_key:
        print("Email not configured (no RESEND_API_KEY)")
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": settings.from_email,
                    "to": to,
                    "subject": subject,
                    "html": html,
                    "text": text or html
                }
            )
            return response.status_code == 200
    except Exception as e:
        print(f"Email send error: {e}")
        return False


def send_report_ready_email(job: ResearchJob, user: User) -> bool:
    """Send notification that research report is ready."""
    subject = f"Your Research Report is Ready: {job.target}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .button {{ display: inline-block; background: #4f46e5; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 500; }}
            .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Research Report Ready</h1>
            </div>
            <div class="content">
                <p>Hi {user.name or 'there'},</p>
                <p>Your research dossier on <strong>{job.target}</strong> is complete and ready to view.</p>
                <p style="margin: 30px 0;">
                    <a href="{settings.frontend_url}/research/{job.id}" class="button">View Report</a>
                </p>
                <p>This report includes:</p>
                <ul>
                    <li>Company/person overview and key facts</li>
                    <li>Recent news and developments</li>
                    <li>Financial data (if available)</li>
                    <li>SWOT analysis</li>
                    <li>Online presence summary</li>
                </ul>
                <p>You can download the report as a PDF from your dashboard.</p>
            </div>
            <div class="footer">
                <p>Research Dossier - Comprehensive Intelligence Reports</p>
            </div>
        </div>
    </body>
    </html>
    """

    import asyncio
    return asyncio.run(send_email(user.email, subject, html))


async def send_password_reset_email(to: str, name: Optional[str], reset_url: str) -> bool:
    """Send password reset email."""
    subject = "Reset Your Password - Research Dossier"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
            .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .button {{ display: inline-block; background: #4f46e5; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; }}
            .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
            .warning {{ background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; padding: 12px; margin-top: 20px; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Password Reset</h1>
            </div>
            <div class="content">
                <p>Hi {name or 'there'},</p>
                <p>We received a request to reset the password for your Research Dossier account.</p>
                <p style="margin: 30px 0; text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #4f46e5;">{reset_url}</p>
                <div class="warning">
                    <strong>This link expires in 1 hour.</strong><br>
                    If you didn't request this, you can safely ignore this email.
                </div>
            </div>
            <div class="footer">
                <p>Research Dossier - Comprehensive Intelligence Reports</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(to, subject, html)


async def send_verification_email(to: str, name: Optional[str], verify_url: str) -> bool:
    """Send email verification email."""
    subject = "Verify Your Email - Research Dossier"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
            .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .button {{ display: inline-block; background: #10b981; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; }}
            .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Verify Your Email</h1>
            </div>
            <div class="content">
                <p>Hi {name or 'there'},</p>
                <p>Thanks for signing up for Research Dossier! Please verify your email address to get started.</p>
                <p style="margin: 30px 0; text-align: center;">
                    <a href="{verify_url}" class="button">Verify Email</a>
                </p>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #10b981;">{verify_url}</p>
                <p style="margin-top: 20px;">This link expires in 24 hours.</p>
            </div>
            <div class="footer">
                <p>Research Dossier - Comprehensive Intelligence Reports</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(to, subject, html)


async def send_welcome_email(to: str, name: Optional[str]) -> bool:
    """Send welcome email after verification."""
    subject = "Welcome to Research Dossier!"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
            .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .button {{ display: inline-block; background: #4f46e5; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; }}
            .feature {{ display: flex; align-items: start; margin-bottom: 15px; }}
            .feature-icon {{ font-size: 24px; margin-right: 15px; }}
            .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Welcome!</h1>
            </div>
            <div class="content">
                <p>Hi {name or 'there'},</p>
                <p>Your email is verified and your account is ready! Here's what you can do:</p>

                <div style="margin: 25px 0;">
                    <div class="feature">
                        <span class="feature-icon">🔍</span>
                        <div>
                            <strong>Research Companies & People</strong><br>
                            Get comprehensive dossiers with financial data, news, and insights.
                        </div>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">📊</span>
                        <div>
                            <strong>SWOT Analysis</strong><br>
                            AI-powered analysis of strengths, weaknesses, opportunities, and threats.
                        </div>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">📥</span>
                        <div>
                            <strong>Download Reports</strong><br>
                            Export your research as PDF or Markdown files.
                        </div>
                    </div>
                </div>

                <p>You have <strong>1 free credit</strong> to get started!</p>

                <p style="margin: 30px 0; text-align: center;">
                    <a href="{settings.frontend_url}/research/new" class="button">Start Your First Research</a>
                </p>
            </div>
            <div class="footer">
                <p>Research Dossier - Comprehensive Intelligence Reports</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(to, subject, html)


async def send_credit_purchase_email(
    to: str,
    name: Optional[str],
    credits_purchased: int,
    amount_dollars: float,
    new_balance: int
) -> bool:
    """Send credit purchase confirmation email."""
    subject = "Credits Purchased - Research Dossier"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
            .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .button {{ display: inline-block; background: #4f46e5; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; }}
            .receipt {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .receipt-row {{ display: flex; justify-content: space-between; padding: 8px 0; }}
            .receipt-total {{ border-top: 1px solid #e5e7eb; padding-top: 12px; margin-top: 8px; }}
            .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Purchase Confirmed</h1>
            </div>
            <div class="content">
                <p>Hi {name or 'there'},</p>
                <p>Thank you for your purchase! Your credits have been added to your account.</p>

                <div class="receipt">
                    <div class="receipt-row">
                        <span style="color: #6b7280;">Credits Purchased:</span>
                        <span style="font-weight: 600;">{credits_purchased}</span>
                    </div>
                    <div class="receipt-row">
                        <span style="color: #6b7280;">Amount Paid:</span>
                        <span style="font-weight: 600;">${amount_dollars:.2f}</span>
                    </div>
                    <div class="receipt-row receipt-total">
                        <span style="color: #6b7280;">New Balance:</span>
                        <span style="font-weight: 600; color: #10b981;">{new_balance} credits</span>
                    </div>
                </div>

                <p style="margin: 30px 0; text-align: center;">
                    <a href="{settings.frontend_url}/dashboard" class="button">Go to Dashboard</a>
                </p>

                <p>Thank you for using Research Dossier!</p>
            </div>
            <div class="footer">
                <p>Research Dossier - Comprehensive Intelligence Reports</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(to, subject, html)


async def send_low_credit_alert(
    to: str,
    name: Optional[str],
    remaining_credits: int = 0
) -> bool:
    """Send low credit alert when credits drop to 0."""
    subject = "Low Credits Alert - Research Dossier"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
            .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none; }}
            .button {{ display: inline-block; background: #4f46e5; color: white; padding: 14px 28px; border-radius: 6px; text-decoration: none; font-weight: 600; }}
            .alert-box {{ background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center; }}
            .pricing {{ background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .pricing-item {{ padding: 10px 0; border-bottom: 1px solid #f3f4f6; }}
            .pricing-item:last-child {{ border-bottom: none; }}
            .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0;">Low Credits Alert</h1>
            </div>
            <div class="content">
                <p>Hi {name or 'there'},</p>

                <div class="alert-box">
                    <p style="margin: 0; font-size: 18px;">You have <strong>{remaining_credits} credits</strong> remaining</p>
                </div>

                <p>To continue generating research reports, you'll need to purchase more credits.</p>

                <div class="pricing">
                    <div class="pricing-item">
                        <strong>Single Report</strong> - 1 credit for $15
                    </div>
                    <div class="pricing-item">
                        <strong>Starter Pack</strong> - 5 credits for $60 <span style="color: #10b981;">($12/credit)</span>
                    </div>
                    <div class="pricing-item">
                        <strong>Pro Pack</strong> - 20 credits for $200 <span style="color: #10b981;">($10/credit)</span>
                    </div>
                </div>

                <p style="margin: 30px 0; text-align: center;">
                    <a href="{settings.frontend_url}/credits" class="button">Buy More Credits</a>
                </p>
            </div>
            <div class="footer">
                <p>Research Dossier - Comprehensive Intelligence Reports</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(to, subject, html)
