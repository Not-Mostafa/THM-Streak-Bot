import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_gmail_report(success, context_summary, execution_logs=None, error_reason="Unknown error occurred"):
    """
    Sends an execution report via Gmail ONLY if today is Saturday.
    """
    # 1. Check if today is Saturday (Monday is 0, Sunday is 6. Saturday is 5)
    # Using UTC to ensure consistency across GitHub Action runners
    if datetime.datetime.now(datetime.timezone.utc).weekday() != 5:
        print("[*] Today is not Saturday. Skipping Gmail notification.")
        return

    # 2. Fetch Environment Variables
    sender_email = os.getenv("GMAIL_ADDRESS")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient_email = os.getenv("GMAIL_RECIPIENT", sender_email) # Defaults to sending to yourself
    
    if not sender_email or not sender_password:
        print("[!] GMAIL_ADDRESS or GMAIL_APP_PASSWORD missing. Cannot send email.")
        return

    # 3. Process Logs
    logs = execution_logs if execution_logs else []
    log_chunk = "\n".join(logs[-20:])[-900:] if logs else "No logs provided."

    # 4. Setup Message Container
    msg = MIMEMultipart("alternative")
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # 5. Build Content Based on Success/Failure
    if success:
        msg['Subject'] = "✅ [SUCCESS] Weekly Automation Sync Report"
        color = "#28a745"
        status_text = "SUCCESS"
        body_content = f"""
        <h2 style="color: {color};">Run Completed Successfully</h2>
        <p><strong>Summary:</strong><br>{context_summary}</p>
        """
    else:
        # High Priority Flags for Failure
        msg['Subject'] = "🚨 [URGENT/FAILED] Automation Sync Execution Failed"
        msg['X-Priority'] = '1'
        msg['X-MSMail-Priority'] = 'High'
        msg['Importance'] = 'High'
        
        color = "#dc3545"
        status_text = "FAILED"
        body_content = f"""
        <div style="background-color: #ffeaea; border: 2px solid {color}; padding: 15px; border-radius: 5px;">
            <h1 style="color: {color}; margin-top: 0;">CRITICAL FAILURE WARNING</h1>
            <p><strong>Reason for Failure:</strong><br>
            <span style="font-size: 18px; color: #a10000; font-weight: bold;">{error_reason}</span></p>
        </div>
        <br>
        <p><strong>Context Summary:</strong><br>{context_summary}</p>
        """

    # 6. HTML Email Template
    html_template = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="border-bottom: 3px solid {color}; padding-bottom: 10px; margin-bottom: 20px;">
            <h2>🛡️ TryHackMe Automation Sync Execution</h2>
        </div>
        
        {body_content}
        
        <h3>Execution Details:</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; width: 30%;">Status</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: {color}; font-weight: bold;">{status_text}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Repository</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{os.getenv("GITHUB_REPOSITORY", "Local Run")}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Run ID</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{os.getenv("GITHUB_RUN_ID", "N/A")}</td>
            </tr>
        </table>

        <h3>📋 Active Application Logs</h3>
        <div style="background-color: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap;">{log_chunk}</div>
        
        <p style="font-size: 12px; color: #777; margin-top: 30px; text-align: center;">
            Executed via GitHub Actions Sync Runner • {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
        </p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_template, 'html'))

    # 7. Send the Email
    try:
        # Gmail uses port 587 for TLS
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("[+] Saturday Gmail report sent successfully.")
    except Exception as e:
        print(f"[!] Critical failure sending Gmail report: {e}")

# Example of how you would call this in your main script:
# if __name__ == "__main__":
#     logs = ["Starting...", "Running task 1", "Error on line 42"]
#     send_gmail_report(False, "Failed to bypass polkit room.", logs, "Selenium WebDriver timeout finding login element.")