import os
import urllib.parse

def _send_via_twilio(phone, message):
    """Send via Twilio API (fully background, no browser)."""
    try:
        from twilio.rest import Client
    except ImportError:
        return None

    sid = os.getenv("TWILIO_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_WHATSAPP_FROM")

    if not all([sid, token, from_number]):
        return None

    try:
        client = Client(sid, token)
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"
        if not phone.startswith("whatsapp:"):
            phone_wa = f"whatsapp:+{phone}" if not phone.startswith("+") else f"whatsapp:{phone}"
        else:
            phone_wa = phone

        msg = client.messages.create(
            from_=from_number,
            to=phone_wa,
            body=message
        )
        return f"Sir, message delivered via secure channel. SID: {msg.sid}"
    except Exception as e:
        return f"Twilio transmission failed ({e}). Falling back to browser."


def _send_via_browser(phone, message):
    """
    Send via WhatsApp Web using Selenium.
    Waits for the page to actually load instead of blind sleeping.
    """
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options

    clean_phone = "".join(filter(str.isdigit, str(phone)))
    encoded_message = urllib.parse.quote(message)
    url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_message}"

    try:
        options = Options()
        user_data_dir = os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
        if os.path.exists(user_data_dir):
            options.add_argument(f"--user-data-dir={user_data_dir}")
            options.add_argument("--profile-directory=Default")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        wait = WebDriverWait(driver, 45)
        
        send_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Send"], span[data-icon="send"]'))
        )
        
        send_button.click()

        import time
        time.sleep(2)

        driver.quit()
        return f"Sir, the message to {clean_phone} has been sent successfully."

    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        return f"WhatsApp Browser Error: {e}"


def execute(params):
    phone = params.get("phone")
    message = params.get("message")
    
    if not phone or not message:
        return "Sir, I require both a destination number and a message body."

    clean_phone = "".join(filter(str.isdigit, str(phone)))
    if str(phone).strip().startswith("+"):
        clean_phone = "+" + clean_phone

    twilio_result = _send_via_twilio(clean_phone, message)
    
    if twilio_result and "failed" not in twilio_result.lower():
        return twilio_result
    
    return _send_via_browser(clean_phone, message)