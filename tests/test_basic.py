def test_addition():
    """Simple test checking addition."""
    print("Running test_addition")
    result = 1 + 1
    print(f"Result: {result}")
    assert result == 2, "1 + 1 must equal 2"


def test_string():
    """Simple test with strings."""
    print("Running test_string")
    greeting = "Hello, World!"
    print(f"String: {greeting}")
    assert len(greeting) > 0, "String must not be empty"
    assert "Hello" in greeting, "String must contain 'Hello'"
