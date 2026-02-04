class MockController:
    def __init__(self, id = 0):
        self.id = id
        self.num_axes = 4
        self.num_buttons = 6
        self.axes = [0.0] * self.num_axes
        self.buttons = [0] * self.num_buttons

    def get_axis(self, axis_id):
        return self.axes[axis_id]

    def get_button(self, button_id):
        return self.buttons[button_id]

    def get_name(self):
        return "MockJoystick"