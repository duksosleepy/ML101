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
    language: str = "Spanish"
    transcribed_text: str = ""
    is_recording: bool = False

    def toggle_recording(self):
        """Toggle recording state."""
        self.is_recording = not self.is_recording

    def copy_text(self):
        """Copy text to clipboard."""
        # In actual implementation, this would copy text to clipboard
        pass


def index() -> rx.Component:
    """Create the main page of the Speech to Text Converter app with dark theme."""
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
                        rx.text(
                            "Select Language:",
                            text_align="left",
                            color="white",
                            font_size="0.9rem",
                        ),
                        rx.select(
                            [
                                "English (United States)",
                                "Spanish",
                                "Vietnamese",
                                "French",
                                "German",
                            ],
                            default_value="Spanish",
                            color="white",
                            width="100%",
                            border_color="#4299E1",
                            bg="#333333",
                            margin_bottom="1rem",
                            _focus={"border_color": "#63B3ED"},
                        ),
                        rx.box(
                            height="170px",
                            width="100%",
                            bg="#333333",
                            border_radius="md",
                            border="1px solid #555555",
                            margin_bottom="1.5rem",
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
                                on_click=MicrophoneState.toggle_recording,
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
                    bg="#1E1E1E",
                    border_radius="md",
                    box_shadow="0px 4px 6px rgba(0, 0, 0, 0.5)",
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
