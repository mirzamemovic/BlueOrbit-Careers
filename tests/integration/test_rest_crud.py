def test_company_job_application_crud_flow(client, auth_headers):
    company_response = client.post(
        "/company",
        headers=auth_headers,
        json={"name": "Signal Forge", "description": "API testing studio."},
    )
    assert company_response.status_code == 201
    company_id = company_response.get_json()["id"]

    job_response = client.post(
        "/job",
        headers=auth_headers,
        json={
            "title": "API Tester",
            "description": "Own endpoint contracts and regression coverage.",
            "salary": 2100,
            "company_id": company_id,
            "location": "Skopje",
        },
    )
    assert job_response.status_code == 201
    job = job_response.get_json()
    assert job["location"] == "Skopje"
    job_id = job["id"]

    update_response = client.put(
        f"/job/{job_id}",
        headers=auth_headers,
        json={"location": "Remote"},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["location"] == "Remote"

    application_response = client.post(
        "/application",
        headers=auth_headers,
        json={
            "candidate_name": "Noa Finch",
            "email": "noa@example.com",
            "job_id": job_id,
            "resume_link": "https://example.com/noa.pdf",
        },
    )
    assert application_response.status_code == 201
    application = application_response.get_json()
    assert application["resume_link"] == "https://example.com/noa.pdf"
    assert application["job"]["company"]["name"] == "Signal Forge"

    list_response = client.get("/applications")
    assert list_response.status_code == 200
    assert list_response.get_json()["items"][0]["job_id"] == job_id

    delete_response = client.delete(f"/application/{application['id']}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert client.get(f"/application/{application['id']}").status_code == 404


def test_duplicate_username_and_invalid_login_errors(client):
    first = client.post("/register", json={"username": "mila", "password": "secret123"})
    duplicate = client.post("/register", json={"username": "mila", "password": "secret123"})
    login = client.post("/login", json={"username": "mila", "password": "wrong"})

    assert first.status_code == 201
    assert duplicate.status_code == 400
    assert duplicate.get_json()["details"]["username"] == "Username already exists."
    assert login.status_code == 401
