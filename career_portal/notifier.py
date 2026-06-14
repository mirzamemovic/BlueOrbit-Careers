def send_application_alert(application, opportunity):
    return {
        "channel": "mock-email",
        "subject": f"New application for {opportunity['title']}",
        "preview": f"{application['applicant_name']} applied to {opportunity['company']}.",
    }
