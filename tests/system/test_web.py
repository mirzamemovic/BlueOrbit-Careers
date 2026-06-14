def test_homepage_loads_branding_and_dashboard_shell(client):
    response = client.get("/")

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "BlueOrbit Careers" in page
    assert "Publish a role" in page


def test_user_can_publish_role_from_dashboard(client):
    response = client.post(
        "/opportunities",
        data={
            "title": "System Test Engineer",
            "company": "Northline Studio",
            "location": "Remote",
            "category": "System Testing",
            "work_mode": "Remote",
            "salary_range": "EUR 1.7k - 2.3k",
            "summary": "Drive end-to-end flows and keep regression risk under control during releases.",
        },
        follow_redirects=True,
    )

    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Role launched." in page
    assert "System Test Engineer" in page


def test_user_can_apply_to_role_from_dashboard(client, auth_headers):
    create_response = client.post(
        "/api/opportunities",
        headers=auth_headers,
        json={
            "title": "REST API Tester",
            "company": "Signal Forge",
            "location": "Skopje",
            "category": "API Testing",
            "work_mode": "Hybrid",
            "salary_range": "EUR 1.4k - 2k",
            "summary": "Own endpoint quality, contract checks, and service-level regression protection.",
        },
    )
    opportunity_id = create_response.get_json()["id"]

    response = client.post(
        f"/opportunities/{opportunity_id}/apply",
        data={
            "applicant_name": "Iris Lane",
            "applicant_email": "iris@example.com",
            "portfolio_url": "https://iris.dev",
            "motivation": "I enjoy testing API-heavy products and keeping failure states predictable.",
        },
        follow_redirects=True,
    )

    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Application received." in page
    assert "Iris Lane" in page
