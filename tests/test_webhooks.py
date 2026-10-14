from app.models.leads import Lead


def test_webhook_unauthorized_without_key(client):
    payload = {"event": "lead_status_updated", "lead_id": 1}
    resp = client.post("/api/webhooks/lead-result", json=payload)
    assert resp.status_code == 401
    assert "Invalid or missing X-API-Key" in resp.json()["detail"]


def test_webhook_unauthorized_with_wrong_key(client):
    payload = {"event": "lead_status_updated", "lead_id": 1}
    headers = {"X-API-Key": "wrong_invalid_secret"}
    resp = client.post("/api/webhooks/lead-result", json=payload, headers=headers)
    assert resp.status_code == 401


def test_webhook_authorized_and_lead_update(client, db):
    # Create lead first
    lead = Lead(
        name="Webhook Test Lead",
        email="webhook.lead@example.com",
        phone="01555443322",
        budget=400000.0,
        interest="Kuakata Share",
        qualification_status="Pending",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    headers = {"X-API-Key": "test_webhook_key_secret"}
    payload = {
        "lead_id": lead.id,
        "status": "Qualified",
        "category": "Hot",
        "score": 95,
        "n8n_notes": "Client scheduled for hotel presentation on Saturday.",
    }
    resp = client.post("/api/webhooks/lead-result", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Verify database update
    db.refresh(lead)
    assert lead.qualification_status == "Qualified"
    assert lead.category == "Hot"
    assert lead.score == 95
    assert "Client scheduled for hotel presentation" in lead.reason
