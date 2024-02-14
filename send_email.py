import smtplib, ssl

HOST = "smtp-mail.outlook.com"
PORT = 587


def send_email_to_parent(
    email,
    child_name,
    child_age,
    child_description,
    lat,
    lon,
    helper_name,
    helper_mobile,
):
    # FROM_EMAIL = "dasaribhovan@outlook.com"
    FROM_EMAIL="20bq1a4216@vvit.net"
    TO_EMAIL = email
    PASSWORD = "Bhovan123#"

    MESSAGE = f"""Subject: Urgent: Missing Child Found - Action Required

Dear User,

We hope this message finds you well. We are reaching out to inform you that a missing child has been located, and we believe they may be associated with you based on the information provided during our search efforts.

Child's Information:

Name: {child_name}
Age: {child_age}
Description: {child_description}
Coordinates: {lat},{lon}
Google Maps Link: https://www.google.com/maps?q={lat},{lon}


Adaptive Helper's Information:

Name: {helper_name}
Contact: {helper_mobile}
We kindly request your immediate attention to confirm whether this information matches the missing child you reported or have information about. Your prompt response is crucial to ensuring the safety and well-being of the child.

If the details match, please contact the local authorities for  additional information and coordinate the safe return of the child to their family.

We appreciate your cooperation and assistance in this matter. If you have any questions or concerns, please do not hesitate to contact us at [Your Contact Information].

Thank you for your support.

Sincerely,

AI Powered Missign child Locator.

    """

    smtp = smtplib.SMTP(HOST, PORT)

    status_code, response = smtp.ehlo()
    print(f"[*] Echoing the server: {status_code} {response}")

    status_code, response = smtp.starttls()
    print(f"[*] Starting TLS connection: {status_code} {response}")

    status_code, response = smtp.login(FROM_EMAIL, PASSWORD)
    print(f"[*] Logging in: {status_code} {response}")

    smtp.sendmail(FROM_EMAIL, TO_EMAIL, MESSAGE)
    smtp.quit()
