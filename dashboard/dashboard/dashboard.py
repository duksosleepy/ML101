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


class MomentLiveState(rx.State):
    updating: bool = False

    @rx.event
    def on_update(self, date):
        return rx.toast(f"Date updated: {date}")


def timer():
    return rx.hstack(
        rx.moment(
            format="HH:mm:ss",
            interval=rx.cond(MomentLiveState.updating, 5000, 0),
            on_change=MomentLiveState.on_update,
        ),
        rx.switch(
            is_checked=MomentLiveState.updating,
            on_change=MomentLiveState.set_updating,
        ),
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
app.add_page(timer)
