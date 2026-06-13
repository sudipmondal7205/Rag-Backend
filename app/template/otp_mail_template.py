mail_otp_html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verification Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f6f9fc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f6f9fc; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 500px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
                    
                    <tr>
                        <td align="center" style="padding: 32px 40px 20px 40px; border-bottom: 1px solid #f0f4f8;">
                            <h2 style="margin: 0; color: #1e293b; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">
                                RAG Assistant
                            </h2>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding: 40px 40px 20px 40px;">
                            <p style="margin: 0 0 16px 0; color: #475569; font-size: 16px; line-height: 24px;">
                                Hello,
                            </p>
                            <p style="margin: 0 0 32px 0; color: #475569; font-size: 16px; line-height: 24px;">
                                You requested a one-time verification code to securely access your account. Use the code below to complete your verification block:
                            </p>
                            
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center" style="background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 8px; padding: 20px;">
                                        <span style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 800; color: #0f172a; letter-spacing: 6px; font-variant-numeric: tabular-nums;">
                                            {otp_code}
                                        </span>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 24px 0 0 0; color: #64748b; font-size: 14px; line-height: 20px; text-align: center;">
                                This code is valid for the next <strong>10 minutes</strong>.
                            </p>
                        </td>
                    </tr>

                    <tr>
                        <td style="padding: 0 40px 40px 40px;">
                            <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 4px; padding: 16px;">
                                <p style="margin: 0; color: #b45309; font-size: 13px; line-height: 18px;">
                                    <strong>Security Notice:</strong> Never share this verification code with anyone, including our support agents. If you didn't request this, you can safely ignore this email.
                                </p>
                            </div>
                        </td>
                    </tr>

                    <tr>
                        <td align="center" style="padding: 0 40px 32px 40px; background-color: #fafafa;">
                            <p style="margin: 24px 0 0 0; color: #94a3b8; font-size: 12px; line-height: 16px;">
                                &copy; 2026 RAG Assistant Pipeline Platform. All rights reserved.
                            </p>
                            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 11px;">
                                Automated pipeline transmission — Do not reply to this mailbox.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""