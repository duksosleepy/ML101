"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from rxconfig import config


class State(rx.State):
    """The app state."""

    ...


def index() -> rx.Component:
    # Welcome Page (Index)
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Welcome to Reflex!", size="9"),
            rx.text(
                "Get started by editing ",
                rx.code(f"{config.app_name}/{config.app_name}.py"),
                size="5",
            ),
            rx.link(
                rx.button("Check out our docs!"),
                href="https://reflex.dev/docs/getting-started/introduction/",
                is_external=True,
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
        rx.logo(),
    )


class Clock(rx.State):
    time_elapsed: int = 0
    running: bool = False

    @rx.event
    def start(self):
        self.time_elapsed = 0
        self.running = True

    @rx.event
    def stop(self):
        self.running = False

    @rx.event
    def tick(self):
        if self.running:
            self.time_elapsed += 1


def counter():
    return rx.flex(
        rx.button(
            "Start",
            color_scheme="green",
            on_click=Clock.start,
        ),
        rx.heading(Clock.time_elapsed),
        rx.button(
            "Stop",
            color_scheme="red",
            on_click=Clock.stop,
        ),
        rx.interval(1000, Clock.tick),
    )


class TextArea(rx.State):
    text: str = "Output"

    @rx.event
    def set_text(self, new_text: str):
        self.text = new_text


def blur_example():
    return rx.vstack(
        rx.heading(TextArea.text),
        rx.text_area(
            placeholder="Type something...",
            on_blur=lambda e: TextArea.set_text(e.target.value),
        ),
    )


app = rx.App()
app.add_page(index)
app.add_page(counter)
