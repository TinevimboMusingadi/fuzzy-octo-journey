"""CLI entry point for V2.0 pre-built forms.

Example usage:

    python -m src.main_v2 --form-id employment_onboarding --mode speed
"""

import argparse

from langchain_core.messages import HumanMessage

from src.v2.session import create_session


def run_cli(form_id: str, mode: str) -> None:
    """Run an interactive CLI session for a given form."""
    session = create_session(form_id=form_id, mode=mode)
    graph = session["graph"]
    state = session["state"]

    print("=" * 60)
    print(f"Dynamic Intake Form Agent - V2.0 ({form_id})")
    print("=" * 60)
    print(f"Mode: {mode}")
    print()

    config_run = {"configurable": {"thread_id": f"v2_cli_{form_id}"}}

    # First run to get to the first question
    for _ in graph.stream(state, config_run):
        pass

    current_state = graph.get_state(config_run)

    while True:
        if not current_state.next:
            if current_state.values.get("is_complete"):
                break
            if not current_state.next:
                break

        # Get last AI message (question)
        messages = current_state.values.get("messages", [])
        last_message = None
        for msg in reversed(messages):
            msg_type = getattr(msg, "type", None) or getattr(msg, "role", None) or msg.__dict__.get("type")
            if msg_type == "ai":
                last_message = msg
                break

        if last_message:
            content = getattr(last_message, "content", "") or getattr(last_message, "text", "")
            print(f"Agent: {content}")

        try:
            user_input = input("\nYou: ").strip()
        except EOFError:
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        graph.update_state(
            config_run,
            {"messages": [HumanMessage(content=user_input)]},
        )

        for _ in graph.stream(None, config_run):
            pass

        current_state = graph.get_state(config_run)

    final_state = graph.get_state(config_run).values
    collected_fields = final_state.get("collected_fields", {})

    print("\n" + "=" * 60)
    print("Form Complete!")
    print("=" * 60)
    print("\nCollected Data:")
    for field_id, data in collected_fields.items():
        value = data.get("value", "N/A")
        notes = data.get("notes", [])
        print(f"  {field_id}: {value}")
        if notes:
            print(f"    Notes: {', '.join(notes)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V2.0 pre-built form agent")
    parser.add_argument(
        "--form-id",
        required=True,
        help="Form ID to run (e.g., employment_onboarding, rental_application)",
    )
    parser.add_argument(
        "--mode",
        choices=["speed", "quality", "hybrid"],
        default="hybrid",
        help="Mode to run the agent in",
    )
    args = parser.parse_args()

    run_cli(form_id=args.form_id, mode=args.mode)


if __name__ == "__main__":
    main()


