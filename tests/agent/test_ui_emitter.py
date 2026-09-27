import responses
from asas_agent.utils.ui_emitter import UIEmitter

@responses.activate
def test_ui_emitter():
    responses.add(
        responses.POST,
        "http://localhost:8010/api/events",
        json={"status": "success"},
        status=200
    )
    
    emitter = UIEmitter(base_url="http://localhost:8010")
    success = emitter.emit("test_event", {"foo": "bar"})
    
    assert success is True
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == "http://localhost:8010/api/events"
