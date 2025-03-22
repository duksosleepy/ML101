"""Speech to Text Converter application built with Reflex featuring a dark theme."""

import reflex as rx


class MicrophoneState(rx.State):
    is_recording: bool = False

    @rx.event
    def toggle_recording(self):
        return rx.call_script("""
            navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                console.log('Microphone access granted');
            })
            .catch(function(error) {
                console.log('Error accessing microphone:', error);
            });
        """)


class State(rx.State):
    """The app state."""

    # State variables
    language: str = "English"
    transcribed_text: str = ">"
    is_recording: bool = False

    def toggle_recording(self):
        """Toggle recording state."""
        self.is_recording = not self.is_recording

    def copy_text(self):
        """Copy text to clipboard."""
        # In actual implementation, this would copy text to clipboard
        pass


def index() -> rx.Component:
    """Create the minimal dark-themed Speech to Text Converter page."""
    return rx.box(
        rx.center(
            rx.vstack(
                rx.heading(
                    "Speech to Text Converter",
                    font_size="2rem",
                    color="white",
                    margin_y="2rem",
                ),
                rx.box(
                    rx.vstack(
                        # Minimal language selector with simple border
                        rx.select(
                            [
                                "English",
                                "Spanish",
                                "Vietnamese",
                                "French",
                                "German",
                            ],
                            default_value="English",
                            color="white",
                            width="100%",
                            height="50px",
                            border="1px solid white",
                            border_radius="md",
                            margin_bottom="1rem",
                            bg="black",
                            _focus={"border": "1px solid white"},
                        ),
                        # Minimal text area with simple border and ">" character
                        rx.box(
                            rx.text(
                                ">",
                                color="white",
                                padding="10px",
                                height="100%",
                            ),
                            height="150px",
                            width="100%",
                            bg="black",
                            border="1px solid white",
                            border_radius="md",
                            margin_bottom="1.5rem",
                            overflow="auto",
                        ),
                        rx.hstack(
                            rx.button(
                                "Start Recording",
                                bg="#0000FF",
                                color="white",
                                border_radius="md",
                                padding_x="1.5rem",
                                padding_y="0.5rem",
                                _hover={"bg": "#0000DD"},
                            ),
                            rx.button(
                                "Copy Text",
                                bg="#808080",
                                color="white",
                                border_radius="md",
                                padding_x="1.5rem",
                                padding_y="0.5rem",
                                _hover={"bg": "#707070"},
                            ),
                            spacing="4",
                            margin_bottom="1.5rem",
                        ),
                        spacing="3",
                        width="100%",
                        align_items="start",
                        padding="1.5rem",
                    ),
                    width="100%",
                    max_width="750px",
                    bg="black",
                    border_radius="md",
                ),
                width="100%",
                max_width="800px",
                spacing="4",
                padding_x="1rem",
            ),
            width="100%",
            height="100vh",
            bg="black",
        ),
        width="100%",
        min_height="100vh",
        bg="black",
    )


# Configure the app
app = rx.App()
app.add_page(index)
