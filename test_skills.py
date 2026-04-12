"""
Quick standalone skill tester for JARVIS.
Usage: python test_skills.py
"""
from dotenv import load_dotenv
load_dotenv()

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_open_app():
    from skills.open_app import execute
    print("\n--- TEST: open_app ---")
    result = execute({"text": "notepad"})
    print(f"Result: {result}")

def test_shell():
    from skills.shell_execution import execute
    print("\n--- TEST: shell_execution ---")
    result = execute({"command": "echo Hello from JARVIS"})
    print(f"Result: {result}")

def test_email():
    from skills.email_sender import execute
    print("\n--- TEST: email_sender (dry run) ---")
    result = execute({
        "to": "Recievers Email",
        "subject": "JARVIS Test",
        "body": "This is a test email from JARVIS."
    })
    print(f"Result: {result}")

def test_whatsapp():
    from skills.send_whatsapp_message import execute
    print("\n--- TEST: send_whatsapp_message (dry run) ---")
    print("NOTE: This will open a browser tab to WhatsApp Web.")
    confirm = input("Run this test? (y/n): ").strip().lower()
    if confirm == 'y':
        result = execute({
            "phone": "Recievers Phone Number",
            "message": "Test from JARVIS"
        })
        print(f"Result: {result}")
    else:
        print("Skipped.")

if __name__ == "__main__":
    menu = {
        "1": ("Open App (notepad)", test_open_app),
        "2": ("Shell Command", test_shell),
        "3": ("Email Sender", test_email),
        "4": ("WhatsApp Message", test_whatsapp),
        "5": ("Run ALL", None),
    }

    print("=== JARVIS Skill Tester ===")
    for k, (label, _) in menu.items():
        print(f"  {k}. {label}")
    
    choice = input("\nPick a test (1-5): ").strip()

    if choice == "5":
        test_open_app()
        test_shell()
        test_email()
        test_whatsapp()
    elif choice in menu:
        menu[choice][1]()
    else:
        print("Invalid choice.")
