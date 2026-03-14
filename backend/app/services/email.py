"""Email notification service using Resend."""

import os
from typing import Dict, List, Optional
from email.utils import formataddr
from datetime import datetime

import httpx

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmailService:
    """Email service for sending notifications."""

    def __init__(self):
        self.api_key = settings.smtp_from or os.getenv("RESEND_API_KEY")
        self.from_email = settings.smtp_from or os.getenv("SMTP_FROM", "noreply@accessibleai.com")
        self.from_name = "AccessibleAI"
        self.base_url = "https://api.resend.com/emails"

    async def send_email(
        self,
        to: str | List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Dict[str, any]:
        """Send an email via Resend API.

        Args:
            to: Recipient email address or list
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)
            reply_to: Reply-to address (optional)

        Returns:
            Response from Resend API
        """
        if not self.api_key:
            logger.warning("No email API key configured, skipping email send")
            return {"success": False, "message": "Email not configured"}

        # Convert single email to list
        if isinstance(to, str):
            to = [to]

        payload = {
            "from": formataddr((self.from_name, self.from_email)),
            "to": [formataddr((email, email)) for email in to],
            "subject": subject,
            "html": html_content,
        }

        if text_content:
            payload["text"] = text_content

        if reply_to:
            payload["reply_to"] = reply_to

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    logger.info(f"Email sent successfully to {to}")
                    return response.json()
                else:
                    logger.error(f"Failed to send email: {response.status_code} - {response.text}")
                    return {"success": False, "message": response.text}

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {"success": False, "message": str(e)}

    async def send_welcome(self, to: str, user_name: Optional[str] = None) -> Dict[str, any]:
        """Send welcome email to new users (alias for send_welcome_email)."""
        return await self.send_welcome_email(to, user_name)

    async def send_welcome_email(self, to: str, name: Optional[str] = None) -> Dict[str, any]:
        """Send welcome email to new users."""
        subject = "Welcome to AccessibleAI!"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .header {{ background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:30px; border-radius:10px 10px 0 10px; text-align:center; }}
        .content {{ background:#f9f9f9; padding:30px; border-radius:0 0 10px 10px; }}
        h1 {{ margin:0; font-size:24px; }}
        p {{ margin-bottom:15px; }}
        .button {{ display:inline-block; padding:12px 24px; background:#667eea; color:white; text-decoration:none; border-radius:5px; margin-top:20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Welcome to AccessibleAI!</h1>
        </div>
        <div class="content">
            <p>Hi {name or 'there'},</p>
            <p>Thanks for signing up for AccessibleAI! We're excited to help you make your website accessible to everyone.</p>
            <p>Here's what you can do next:</p>
            <ul>
                <li><strong>Add your first website</strong> - Navigate to the dashboard to get started</li>
                <li><strong>Run a scan</strong> - Our AI will check for accessibility issues</li>
                <li><strong>Fix issues</strong> - Get AI-powered suggestions for common problems</li>
            </ul>
            <p>If you have any questions, feel free to reach out to our support team.</p>
            <a href="{settings.frontend_url}/dashboard" class="button">Go to Dashboard</a>
        </div>
    </div>
</body>
</html>
"""
        return await self.send_email(to, subject, html_content)

    async def send_scan_complete(
        self,
        to: str,
        website_name: str,
        score: int,
        total_issues: int,
        scan_url: str,
    ) -> Dict[str, any]:
        """Send email when scan is complete."""
        subject = f"Accessibility Scan Complete: {website_name}"
        score_color = "green" if score >= 90 else "yellow" if score >= 70 else "red"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .score {{ text-align:center; padding:30px; background:#f0f0f0; border-radius:10px; }}
        .score-number {{ font-size:48px; font-weight:bold; color:{score_color}; }}
        .stats {{ display:flex; justify-content:space-around; margin:20px 0; }}
        .stat {{ text-align:center; }}
        .stat-number {{ font-size:24px; font-weight:bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Scan Complete</h1>
        <p>Your accessibility scan for <strong>{website_name}</strong> is complete.</p>

        <div class="score">
            <div class="score-number">{score}/100</div>
            <p>Accessibility Score</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{total_issues}</div>
                <p>Issues Found</p>
            </div>
        </div>

        <p>Log in to view detailed results and get AI-powered fix suggestions.</p>
        <a href="{settings.frontend_url}/dashboard/scans" class="button" style="display:inline-block; padding:12px 24px; background:#667eea; color:white; text-decoration:none; border-radius:5px;">View Results</a>
    </div>
</body>
</html>
"""
        return await self.send_email(to, subject, html_content)

    async def send_critical_issue_alert(
        self,
        to: str,
        website_name: str,
        issue_count: int,
        dashboard_url: str,
    ) -> Dict[str, any]:
        """Send alert for critical accessibility issues."""
        subject = f"⚠️ Critical Accessibility Issues Found: {website_name}"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .alert {{ background:#fee2e2; border-left:4px solid #ef4444; padding:15px; margin:20px 0; }}
        .button {{ display:inline-block; padding:12px 24px; background:#ef4444; color:white; text-decoration:none; border-radius:5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚠️ Critical Accessibility Issues Detected</h1>

        <div class="alert">
            <p><strong>{website_name}</strong> has {issue_count} critical accessibility issues that need immediate attention.</p>
        </div>

        <p>These issues may affect:</p>
        <ul>
            <li>Users with visual impairments</li>
            <li>Screen reader users</li>
            <li>Legal compliance (ADA/WCAG)</li>
        </ul>

        <p>We recommend addressing these issues as soon as possible.</p>
        <a href="{dashboard_url}" class="button">View Details</a>
    </div>
</body>
</html>
"""
        return await self.send_email(to, subject, html_content)

    async def send_password_reset(
        self,
        to: str,
        reset_link: str,
        expiry_hours: int = 24,
    ) -> Dict[str, any]:
        """Send password reset email."""
        subject = "Reset Your Password"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .button {{ display:inline-block; padding:12px 24px; background:#667eea; color:white; text-decoration:none; border-radius:5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reset Your Password</h1>
        <p>We received a request to reset your password. Click the button below to create a new password:</p>

        <p style="text-align:center;">
            <a href="{reset_link}" class="button">Reset Password</a>
        </p>

        <p><strong>This link will expire in {expiry_hours} hours.</strong></p>

        <p>If you didn't request this, you can safely ignore this email.</p>
    </div>
</body>
</html>
"""
        return await self.send_email(to, subject, html_content)

    async def send_subscription_confirmed(
        self,
        to: str,
        plan_name: str,
        amount: int,
    ) -> Dict[str, any]:
        """Send subscription confirmation email."""
        subject = f"Subscription Confirmed: {plan_name} Plan"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .header {{ background:linear-gradient(135deg, #10b981 0%, #059669 100%); color:white; padding:30px; border-radius:10px; text-align:center; }}
        .details {{ background:#f9f9f9; padding:30px; border-radius:0 0 10px 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Subscription Confirmed!</h1>
        </div>
        <div class="details">
            <p>Your subscription has been successfully upgraded to the <strong>{plan_name}</strong> plan.</p>
            <p>You will be charged ${amount/100:.2f}/month.</p>
            <p>What's next?</p>
            <ul>
                <li>Run unlimited accessibility scans</li>
                <li>Access AI-powered fix suggestions</li>
                <li>Get priority support</li>
            </ul>
            <p><a href="{settings.frontend_url}/dashboard" class="button" style="display:inline-block; padding:12px 24px; background:#10b981; color:white; text-decoration:none; border-radius:5px;">Go to Dashboard</a></p>
        </div>
    </div>
</body>
</html>
"""
        return await self.send_email(to, subject, html_content)

    async def send_trial_ending(
        self,
        to: str,
        days_used: int,
        upgrade_url: str,
    ) -> Dict[str, any]:
        """Send trial ending reminder email."""
        subject = "⏰ Your Trial is Ending Soon"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .alert {{ background:#fef3c7; border-left:4px solid #f59e0b; padding:15px; margin:20px 0; }}
        .button {{ display:inline-block; padding:12px 24px; background:#f59e0b; color:white; text-decoration:none; border-radius:5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⏰ Your Trial is Ending</h1>
        <p>You've been using AccessibleAI for {days_used} days, and your trial period is coming to an end.</p>

        <div class="alert">
            <p><strong>Don't lose access!</strong> Upgrade now to continue enjoying unlimited scans and AI-powered fixes.</p>
        </div>

        <p>Choose a plan that works for you:</p>
        <ul>
            <li><strong>Starter ($49/mo)</strong> - 3 websites, unlimited scans</li>
            <li><strong>Pro ($99/mo)</strong> - 10 websites, all CMS integrations</li>
            <li><strong>Agency ($249/mo)</strong> - Unlimited, white-label, SLA</li>
        </ul>

        <p style="text-align:center;">
            <a href="{upgrade_url}" class="button">Upgrade Now</a>
        </p>
    </div>
</body>
</html>
"""
        return await self.send_email(to, subject, html_content)

    async def send_usage_summary(
        self,
        to: str,
        month: str,
        scans_completed: int,
        issues_fixed: int,
        current_score: int,
    ) -> Dict[str, any]:
        """Send monthly usage summary email."""
        subject = f"Monthly Accessibility Summary - {month}"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .stats {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:15px; margin:20px 0; }}
        .stat {{ background:#f9f9f9; padding:20px; border-radius:10px; text-align:center; }}
        .stat-number {{ font-size:32px; font-weight:bold; color:#667eea; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Monthly Accessibility Summary</h1>
        <p>Here's how your website accessibility improved in {month}:</p>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{scans_completed}</div>
                <p>Scans Completed</p>
            </div>
            <div class="stat">
                <div class="stat-number">{issues_fixed}</div>
                <p>Issues Fixed</p>
            </div>
            <div class="stat">
                <div class="stat-number">{current_score}</div>
                <p>Current Score</p>
            </div>
        </div>

        <p>Keep up the good work! Consistent monitoring and fixing issues helps create a more accessible web for everyone.</p>
        <a href="{settings.frontend_url}/dashboard" class="button" style="display:inline-block; padding:12px 24px; background:#667eea; color:white; text-decoration:none; border-radius:5px;">View Dashboard</a>
    </div>
</body>
</html>
"""
        return await self.send_email(to, subject, html_content)

    async def send_scan_complete(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        website_name: str = "",
        website_url: str = "",
        score: int = 0,
        total_issues: int = 0,
        scan_id: str = "",
    ) -> Dict[str, any]:
        """Send email when scan is complete (with extended params)."""
        scan_url = f"{settings.frontend_url}/dashboard/scans/{scan_id}"
        subject = f"Accessibility Scan Complete: {website_name}"
        score_color = "green" if score >= 90 else "#eab308" if score >= 70 else "#ef4444"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .score {{ text-align:center; padding:30px; background:#f0f0f0; border-radius:10px; }}
        .score-number {{ font-size:48px; font-weight:bold; color:{score_color}; }}
        .stats {{ display:flex; justify-content:space-around; margin:20px 0; }}
        .stat {{ text-align:center; }}
        .stat-number {{ font-size:24px; font-weight:bold; }}
        .button {{ display:inline-block; padding:12px 24px; background:#667eea; color:white; text-decoration:none; border-radius:5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✅ Scan Complete</h1>
        <p>Hi {user_name or 'there'},</p>
        <p>Your accessibility scan for <strong>{website_name}</strong> ({website_url}) is complete.</p>

        <div class="score">
            <div class="score-number">{score}/100</div>
            <p>Accessibility Score</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{total_issues}</div>
                <p>Issues Found</p>
            </div>
        </div>

        <p>Log in to view detailed results and get AI-powered fix suggestions.</p>
        <a href="{scan_url}" class="button">View Results</a>
    </div>
</body>
</html>
"""
        return await self.send_email(to_email, subject, html_content)

    async def send_weekly_report(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        total_scans: int = 0,
        avg_score: int = 0,
        total_issues: int = 0,
    ) -> Dict[str, any]:
        """Send weekly summary report to user."""
        subject = f"Weekly Accessibility Report - {total_scans} scans"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .stats {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:15px; margin:20px 0; }}
        .stat {{ background:#f9f9f9; padding:20px; border-radius:10px; text-align:center; }}
        .stat-number {{ font-size:32px; font-weight:bold; color:#667eea; }}
        .button {{ display:inline-block; padding:12px 24px; background:#667eea; color:white; text-decoration:none; border-radius:5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Weekly Accessibility Report</h1>
        <p>Hi {user_name or 'there'},</p>
        <p>Here's your accessibility summary for this week:</p>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{total_scans}</div>
                <p>Scans Run</p>
            </div>
            <div class="stat">
                <div class="stat-number">{avg_score}/100</div>
                <p>Avg Score</p>
            </div>
            <div class="stat">
                <div class="stat-number">{total_issues}</div>
                <p>Issues Found</p>
            </div>
        </div>

        <p>Keep up the good work! Regular scanning helps maintain accessibility compliance.</p>
        <a href="{settings.frontend_url}/dashboard" class="button">View Dashboard</a>
    </div>
</body>
</html>
"""
        return await self.send_email(to_email, subject, html_content)

    async def send_subscription_confirmation(
        self,
        to_email: str,
        user_name: Optional[str] = None,
        tier: str = "free",
    ) -> Dict[str, any]:
        """Send subscription confirmation email."""
        tier_names = {
            "free": "Free",
            "starter": "Starter",
            "pro": "Pro",
            "agency": "Agency",
        }
        plan_name = tier_names.get(tier, tier.title())
        subject = f"Subscription Confirmed: {plan_name} Plan"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height:1.6; color:#333; }}
        .container {{ max-width:600px; margin:0 auto; padding:20px; }}
        .header {{ background:linear-gradient(135deg, #10b981 0%, #059669 100%); color:white; padding:30px; border-radius:10px; text-align:center; }}
        .details {{ background:#f9f9f9; padding:30px; border-radius:0 0 10px 10px; }}
        .button {{ display:inline-block; padding:12px 24px; background:#10b981; color:white; text-decoration:none; border-radius:5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Subscription Confirmed!</h1>
        </div>
        <div class="details">
            <p>Hi {user_name or 'there'},</p>
            <p>Your subscription has been successfully updated to the <strong>{plan_name}</strong> plan.</p>
            <p>What's next?</p>
            <ul>
                <li>Run unlimited accessibility scans</li>
                <li>Access AI-powered fix suggestions</li>
                <li>Get priority support</li>
            </ul>
            <a href="{settings.frontend_url}/dashboard" class="button">Go to Dashboard</a>
        </div>
    </div>
</body>
</html>
"""
        return await self.send_email(to_email, subject, html_content)


# Singleton instance
_email_service = None


def get_email_service() -> EmailService:
    """Get the email service singleton instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
