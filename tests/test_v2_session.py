from src.v2.session import create_session


def test_create_session_employment_onboarding():
    session = create_session("employment_onboarding", mode="speed")
    graph = session["graph"]
    state = session["state"]

    assert "fields" in state["form_schema"]
    assert state["current_field_id"] == state["form_schema"]["fields"][0]["id"]

    config_run = {"configurable": {"thread_id": "test_employment"}}
    # Just ensure the graph can run one step without error
    for _ in graph.stream(state, config_run):
        pass


def test_create_session_rental_application():
    session = create_session("rental_application", mode="speed")
    graph = session["graph"]
    state = session["state"]

    assert "fields" in state["form_schema"]
    assert state["current_field_id"] == state["form_schema"]["fields"][0]["id"]

    config_run = {"configurable": {"thread_id": "test_rental"}}
    for _ in graph.stream(state, config_run):
        pass


