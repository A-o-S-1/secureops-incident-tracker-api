def incident_payload(**overrides):
    data = {"title":"Suspicious login pattern", "description":"Synthetic lab event for testing.", "category":"unauthorized_access", "severity":"high", "source":"test-sensor"}
    data.update(overrides)
    return data

def test_auth_success_and_failure(client):
    assert client.post("/auth/token", data={"username":"analyst_test","password":"AnalystPassword123!"}).status_code == 200
    assert client.post("/auth/token", data={"username":"analyst_test","password":"wrong-password"}).status_code == 401

def test_unauthorized_and_forbidden(client, analyst_headers):
    assert client.get("/incidents").status_code == 401
    assert client.get("/audit-logs", headers=analyst_headers).status_code == 403
    assert client.post("/users", headers=analyst_headers, json={"username":"new_user","password":"LongPassword123!","role":"analyst"}).status_code == 403

def test_create_retrieve_and_audit(client, analyst_headers, admin_headers):
    r = client.post("/incidents", headers=analyst_headers, json=incident_payload())
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["reference_id"].startswith("INC-")
    assert client.get(f"/incidents/{item['reference_id']}", headers=analyst_headers).status_code == 200
    logs = client.get("/audit-logs", headers=admin_headers)
    assert logs.status_code == 200
    assert any(x["action"] == "incident.created" for x in logs.json())

def test_validation_filter_pagination(client, analyst_headers):
    assert client.post("/incidents", headers=analyst_headers, json=incident_payload(severity="urgent")).status_code == 422
    for i in range(3):
        assert client.post("/incidents", headers=analyst_headers, json=incident_payload(title=f"Suspicious login {i}")).status_code == 201
    r = client.get("/incidents?severity=high&page=1&page_size=2", headers=analyst_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 3
    assert len(r.json()["items"]) == 2
    assert r.json()["page"] == 1

def test_invalid_state_transition_and_resolution(client, analyst_headers, admin_headers):
    item = client.post("/incidents", headers=analyst_headers, json=incident_payload()).json()
    ref = item["reference_id"]
    assert client.patch(f"/incidents/{ref}/status", headers=analyst_headers, json={"status":"closed"}).status_code == 409
    assert client.patch(f"/incidents/{ref}/status", headers=analyst_headers, json={"status":"investigating"}).status_code == 200
    assert client.patch(f"/incidents/{ref}/status", headers=analyst_headers, json={"status":"resolved"}).status_code == 422
    assert client.patch(f"/incidents/{ref}/status", headers=analyst_headers, json={"status":"resolved","resolution_notes":"Synthetic test completed."}).status_code == 200
    assert client.patch(f"/incidents/{ref}/status", headers=analyst_headers, json={"status":"closed"}).status_code == 403
    assert client.patch(f"/incidents/{ref}/status", headers=admin_headers, json={"status":"closed"}).status_code == 200

def test_admin_delete_and_audit(client, analyst_headers, admin_headers):
    item = client.post("/incidents", headers=analyst_headers, json=incident_payload()).json()
    ref = item["reference_id"]
    assert client.delete(f"/incidents/{ref}", headers=analyst_headers).status_code == 403
    assert client.delete(f"/incidents/{ref}", headers=admin_headers).status_code == 204
    logs = client.get("/audit-logs", headers=admin_headers).json()
    assert any(x["action"] == "incident.deleted" for x in logs)

def test_updates_permissions_and_no_secrets_in_audit(client, analyst_headers, admin_headers):
    item = client.post("/incidents", headers=analyst_headers, json=incident_payload()).json()
    ref = item["reference_id"]
    assert client.patch(f"/incidents/{ref}", headers=analyst_headers, json={"title":"Updated synthetic title"}).status_code == 200
    assert client.patch(f"/incidents/{ref}", headers=analyst_headers, json={"title":"x"}).status_code == 422
    assert client.patch(f"/incidents/{ref}", headers=analyst_headers, json={"title":"Closed edit"}).status_code == 200
    logs = client.get("/audit-logs", headers=admin_headers).json()
    assert all("password" not in str(log["details"]).lower() for log in logs)
    assert all("token" not in str(log["details"]).lower() for log in logs)
