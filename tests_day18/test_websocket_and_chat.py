import pytest


def receive_message_of_type(websocket, expected_type, max_reads=5):
    for _ in range(max_reads):
        msg = websocket.receive_json()
        if msg.get("type") == expected_type:
            return msg
    raise AssertionError(f"Expected frame type '{expected_type}' not found in {max_reads} reads")


def test_websocket_connection_and_ping_pong(client, shopper_token):
    with client.websocket_connect(f"/ws?token={shopper_token}") as websocket:
        welcome = receive_message_of_type(websocket, "CONNECTION_ESTABLISHED")
        assert welcome["data"]["user"]["email"] == "shopper@example.com"

        # Send PING
        websocket.send_json({"type": "PING"})
        pong = receive_message_of_type(websocket, "PONG")
        assert pong["type"] == "PONG"


def test_live_chat_and_messages_api(client, shopper_token, admin_token):
    # Customer sends message via REST API
    send_resp = client.post(
        "/chat/messages",
        json={"message": "Hello admin, I need help with my order!"},
        headers={"Authorization": f"Bearer {shopper_token}"},
    )
    assert send_resp.status_code == 200
    sent_data = send_resp.json()
    assert sent_data["success"] is True
    assert sent_data["data"]["text"] == "Hello admin, I need help with my order!"

    # Customer retrieves chat messages
    get_resp = client.get(
        "/chat/messages",
        headers={"Authorization": f"Bearer {shopper_token}"},
    )
    assert get_resp.status_code == 200
    messages = get_resp.json()
    assert isinstance(messages, list)
    assert any("help with my order" in m["text"] for m in messages)

    # Admin retrieves chat messages
    admin_get_resp = client.get(
        "/chat/messages?customer=shopper@example.com",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_get_resp.status_code == 200
    admin_messages = admin_get_resp.json()
    assert any("help with my order" in m["text"] for m in admin_messages)


def test_websocket_chat_exchange(client, shopper_token, admin_token):
    # Open customer and admin websockets concurrently
    with client.websocket_connect(f"/ws?token={admin_token}") as admin_ws:
        admin_welcome = receive_message_of_type(admin_ws, "CONNECTION_ESTABLISHED")
        assert admin_welcome["type"] == "CONNECTION_ESTABLISHED"

        with client.websocket_connect(f"/ws?token={shopper_token}") as shopper_ws:
            shopper_welcome = receive_message_of_type(shopper_ws, "CONNECTION_ESTABLISHED")
            assert shopper_welcome["type"] == "CONNECTION_ESTABLISHED"

            # Shopper sends chat message over websocket
            shopper_ws.send_json({
                "type": "CHAT_MESSAGE",
                "text": "Live WebSocket support request",
                "recipient_email": "admin",
            })

            # Shopper receives echo/ack
            shopper_msg = receive_message_of_type(shopper_ws, "CHAT_MESSAGE")
            assert shopper_msg["data"]["text"] == "Live WebSocket support request"

            # Admin receives the live message
            admin_msg = receive_message_of_type(admin_ws, "CHAT_MESSAGE")
            assert admin_msg["data"]["text"] == "Live WebSocket support request"
