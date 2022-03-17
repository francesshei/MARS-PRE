from _gui import Model, View, Controller
import ttkbootstrap as ttk
from _serial import SerialPortManager

class App(ttk.Window):
    def __init__(self):
        super().__init__(
        title="MARS-PRE",
        themename="darkly",
        size=(1100, 700),
        resizable=(True, True))

        # Create a model
        _spm = SerialPortManager()
        _spm.start()
        model = Model(_spm)
        # Create a view and place it on the root window
        view = View(self)
        # Create a controller
        controller = Controller(view, model)
        # Set the controller to the view
        view.set_controller(controller)

# Start the application
if __name__ == '__main__':
    app = App()
    app.mainloop()