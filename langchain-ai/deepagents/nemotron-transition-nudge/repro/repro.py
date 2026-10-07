"""Reproduce a false task-transition decision in the Nemotron Ultra profile."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from deepagents.profiles.harness._nvidia_nemotron_3_ultra import (
    NemotronPolicyNudgeMiddleware,
)


def tool_call(name: str, args: dict[str, object], call_id: str) -> AIMessage:
    """Create a minimal AI message containing one filesystem tool call."""
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": name,
                "args": args,
                "id": call_id,
                "type": "tool_call",
            }
        ],
    )


def main() -> None:
    # This is one user turn followed by ordinary filesystem work. There is no
    # second external user request and therefore no task transition.
    messages = [
        HumanMessage(
            content="Analyze input.csv and create the required output file."
        ),
        tool_call("ls", {"path": "/"}, "call-1"),
        ToolMessage(content="input\noutput", tool_call_id="call-1"),
        tool_call(
            "read_file",
            {"file_path": "/input/data.csv"},
            "call-2",
        ),
        ToolMessage(
            content="region,revenue\nwest,100",
            tool_call_id="call-2",
        ),
        tool_call(
            "read_file",
            {"file_path": "/input/products.json"},
            "call-3",
        ),
        ToolMessage(content='{"products": []}', tool_call_id="call-3"),
    ]

    external_user_messages = [
        message for message in messages if isinstance(message, HumanMessage)
    ]
    assert len(external_user_messages) == 1

    should_compact = (
        NemotronPolicyNudgeMiddleware._should_compact_on_transition(messages)
    )

    print(f"External user messages: {len(external_user_messages)}")
    print(f"Should compact on transition: {should_compact}")

    # Expected: False, because the user has not started another task.
    # Actual with deepagents 0.7.10: True.
    assert should_compact is False


if __name__ == "__main__":
    main()
