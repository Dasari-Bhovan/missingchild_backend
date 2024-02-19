import vonage

client = vonage.Client(key="2f7fa600", secret="amSct5W3WWvEoZ00")
sms = vonage.Sms(client)


def send_sms_to_parent(name,age,lat,lon,helper_name,helper_contact,parent_contact):
    responseData = sms.send_message(
        {
            "from": "Vonage APIs",
            "to": "8688581004",
            "text": f"""Urgent: Missing Child Found - Action Required. \nChild's Name: {name}.\nChild's Age: {age}. \nCoordinates: {lat},{lon}. \nGoogle Maps Link: https://www.google.com/maps?q={lat},{lon}. \nAdaptive Helper: {helper_name}, Contact: {helper_contact}. Confirm if this matches the missing child you reported. Contact local authorities at Local Police Contact with additional info. Thank you.""",
        }
    )

    if responseData["messages"][0]["status"] == "0":
        print(responseData["messages"])
        print("Message sent successfully.")
    else:
        print(f"Message failed with error: {responseData['messages'][0]['error-text']}")


# send_sms_to_parent("bhovan","20","16.3448744","80.52477481644553","rizwan","6304447072","8688581004")
