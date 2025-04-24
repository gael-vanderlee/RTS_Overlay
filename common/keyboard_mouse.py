import time
from pynput import keyboard, mouse

class HotkeyFlagData:
    """Flag for a hotkey, with related data (sequence and timestamp)"""

    def __init__(self, flag: bool = False, sequence: str = ''):
        """Constructor

        Parameters
        ----------
        flag        True if hotkey flag activated
        sequence    sequence corresponding to the hotkey (keyboard or mouse)
        """
        self.sequence: str = sequence
        self.flag: bool = False
        self.timestamp: float = 0  # last timestamp when the flag was set to True [s]
        self.set_flag(flag)

    def set_flag(self, flag: bool):
        """Set the value for a flag and update the timestamp if flag set to True

        Parameters
        ----------
        flag    True if hotkey flag activated
        """
        self.flag = flag
        if flag:
            self.timestamp = time.time()

    def get_elapsed_time(self) -> float:
        """Get the elapsed time since last timestamp

        Returns
        -------
        Elapsed time [s]
        """
        return time.time() - self.timestamp


class KeyboardMouseManagement:
    """Keyboard global hotkeys and mouse global buttons management"""

    def __init__(self, print_unset: bool = True):
        """Constructor

        Parameters
        ----------
        print_unset    True to print unset hotkey & button warnings.
        """
        self.print_unset = print_unset
        self.keyboard_hotkeys = dict()  # list of keyboard hotkeys available as {name: HotkeyFlagData}

        # For pynput, we need to track currently pressed keys
        self.currently_pressed_keys = set()

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()

        # names of the available mouse buttons
        self.mouse_button_names = ['left', 'middle', 'right', 'x', 'x2']
        self.mouse_buttons = dict()  # list of mouse buttons available as {name: HotkeyFlagData}

        # Create a platform-independent button map
        self.button_map = {
            mouse.Button.left: 'left',
            mouse.Button.middle: 'middle',
            mouse.Button.right: 'right'
        }

        # Try to add extra buttons if they exist (platform-specific)
        try:
            self.button_map[mouse.Button.x1] = 'x'
        except AttributeError:
            pass

        try:
            self.button_map[mouse.Button.x2] = 'x2'
        except AttributeError:
            pass

        # Initialize mouse buttons
        for mouse_button_name in self.mouse_button_names:
            self.mouse_buttons[mouse_button_name] = HotkeyFlagData(sequence=mouse_button_name)

        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self._on_click
        )
        self.mouse_listener.start()

    def _on_key_press(self, key):
        """Handle key press events"""
        try:
            # Add key to currently pressed set
            if hasattr(key, 'char'):
                self.currently_pressed_keys.add(key.char)
            else:
                self.currently_pressed_keys.add(key)

            # Check all hotkeys for matches
            self._check_hotkeys()
        except Exception as e:
            print(f"Error in key press handler: {e}")

    def _on_key_release(self, key):
        """Handle key release events"""
        try:
            # Remove key from currently pressed set
            if hasattr(key, 'char') and key.char in self.currently_pressed_keys:
                self.currently_pressed_keys.remove(key.char)
            elif key in self.currently_pressed_keys:
                self.currently_pressed_keys.remove(key)
        except Exception as e:
            print(f"Error in key release handler: {e}")

    def _on_click(self, x, y, button, pressed):
        """Handle mouse click events"""
        try:
            if button in self.button_map and not pressed:  # On button release
                button_name = self.button_map[button]
                self.set_mouse_flag(button_name, True)
        except Exception as e:
            print(f"Error in mouse click handler: {e}")

    def _check_hotkeys(self):
        """Check if any registered hotkey combinations are pressed"""
        for name, hotkey_data in self.keyboard_hotkeys.items():
            if self._is_hotkey_match(hotkey_data.sequence):
                self.set_keyboard_hotkey_flags([name], True)

    def _is_hotkey_match(self, sequence):
        """Check if the current key combination matches the sequence"""
        if not sequence:
            return False

        # Parse the sequence (e.g., 'ctrl+h', 'alt+d')
        keys = sequence.lower().split('+')

        # Map modifier key names to pynput key objects
        modifier_map = {
            'ctrl': keyboard.Key.ctrl,
            'alt': keyboard.Key.alt,
            'shift': keyboard.Key.shift,
        }

        # Check if all keys in the sequence are pressed
        for key in keys:
            if key in modifier_map:
                if modifier_map[key] not in self.currently_pressed_keys:
                    return False
            else:
                # For regular characters
                if key not in self.currently_pressed_keys:
                    return False

        return True

    def set_all_flags(self, value: bool):
        """Set all the flags (keyboard and mouse) to the same value"""
        for key in self.keyboard_hotkeys.keys():
            self.keyboard_hotkeys[key].set_flag(value)

        for key in self.mouse_buttons.keys():
            self.mouse_buttons[key].set_flag(value)

    def update_keyboard_hotkey(self, name: str, sequence: str) -> bool:
        """Update the hotkey binds for a new keyboard hotkey definition."""
        try:
            if name == '':
                print('Name missing to update keyboard hotkey.')
                return False

            # No change for this hotkey
            if name in self.keyboard_hotkeys and self.keyboard_hotkeys[name].sequence == sequence:
                return False

            # Add/update hotkey in dictionary
            self.keyboard_hotkeys[name] = HotkeyFlagData(sequence=sequence)
            return True

        except Exception as e:
            print(f'Could not set hotkey \'{name}\' with sequence \'{sequence}\': {e}')
            return False

    def set_keyboard_hotkey_flags(self, names: list, value: bool):
        """Set the flags related to a list of keyboard hotkeys."""
        for name in names:
            if name in self.keyboard_hotkeys:
                self.keyboard_hotkeys[name].set_flag(value)
            elif self.print_unset:
                print(f'Unknown keyboard hotkey name received ({name}) to set the flag.')

    def is_keyboard_hotkey_pressed(self, name: str) -> bool:
        """Check if a keyboard hotkey is pressed"""
        if name in self.keyboard_hotkeys:
            return self._is_hotkey_match(self.keyboard_hotkeys[name].sequence)
        else:
            if self.print_unset:
                print(f'Unknown keyboard hotkey name received ({name}) to check if it is pressed.')
            return False

    def get_keyboard_hotkey_flag(self, name: str) -> bool:
        """Get the flag related to a specific keyboard hotkey name, and set the corresponding flag to False."""
        if name in self.keyboard_hotkeys:
            flag_value = self.keyboard_hotkeys[name].flag
            self.keyboard_hotkeys[name].set_flag(False)
            return flag_value
        else:
            if self.print_unset:
                print(f'Unknown keyboard hotkey name received ({name}) to get the flag value.')
            return False

    def get_keyboard_hotkey_elapsed_time(self, name: str) -> float:
        """Get the elapsed time related to a specific keyboard hotkey name."""
        if name in self.keyboard_hotkeys:
            return self.keyboard_hotkeys[name].get_elapsed_time()
        else:
            if self.print_unset:
                print(f'Unknown keyboard hotkey name received ({name}) to get the timestamp.')
            return -1.0

    def set_mouse_flag(self, name: str, value: bool):
        """Set the flag related to a mouse button."""
        if name in self.mouse_buttons:
            self.mouse_buttons[name].set_flag(value)
        elif self.print_unset:
            print(f'Unknown mouse button name received ({name}) to set the flag.')

    def get_mouse_flag(self, name: str) -> bool:
        """Get the flag related to a specific mouse button name, and set the corresponding flag to False."""
        if name in self.mouse_buttons:
            flag_value = self.mouse_buttons[name].flag
            self.mouse_buttons[name].set_flag(False)
            return flag_value
        else:
            if self.print_unset:
                print(f'Unknown mouse button name received ({name}) to get the flag value.')
            return False

    def get_mouse_elapsed_time(self, name: str) -> float:
        """Get the elapsed time related to a specific mouse button name."""
        if name in self.mouse_buttons:
            return self.mouse_buttons[name].get_elapsed_time()
        else:
            if self.print_unset:
                print(f'Unknown mouse button name received ({name}) to get the timestamp.')
            return -1.0

    def cleanup(self):
        """Stop all listeners and clean up resources"""
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener.is_alive():
            self.keyboard_listener.stop()
        if hasattr(self, 'mouse_listener') and self.mouse_listener.is_alive():
            self.mouse_listener.stop()


if __name__ == '__main__':
    # initialize keyboard-mouse management
    keyboard_mouse = KeyboardMouseManagement()

    # set initial hotkeys
    keyboard_mouse.update_keyboard_hotkey('print_hello', 'ctrl+h')
    keyboard_mouse.update_keyboard_hotkey('quit', 'ctrl+q')
    keyboard_mouse.update_keyboard_hotkey('change_hotkey', 'alt+s')
    keyboard_mouse.update_keyboard_hotkey('hotkey_mouse_together', 'ctrl')
    keyboard_mouse.update_keyboard_hotkey('unusable_wrong_sequence', 'alt+r')

    try:
        while True:
            # print message
            if keyboard_mouse.get_keyboard_hotkey_flag('print_hello'):
                print('Hello world!')

            # quit the script
            if keyboard_mouse.get_keyboard_hotkey_flag('quit'):
                break

            # change a hotkey
            if keyboard_mouse.get_keyboard_hotkey_flag('change_hotkey'):
                current_sequence = keyboard_mouse.keyboard_hotkeys['change_hotkey'].sequence
                if current_sequence == 'alt+s':
                    keyboard_mouse.update_keyboard_hotkey('change_hotkey', 'alt+d')
                    print('Changing hotkey from \'alt+s\' to \'alt+d\'.')
                elif current_sequence == 'alt+d':
                    keyboard_mouse.update_keyboard_hotkey('change_hotkey', 'alt+s')
                    print('Changing hotkey from \'alt+d\' to \'alt+s\'.')

            # hotkey and mouse button together
            if keyboard_mouse.is_keyboard_hotkey_pressed('hotkey_mouse_together') and keyboard_mouse.get_mouse_flag('x'):
                print('Ctrl and mouse first button combined.')

            # mouse buttons
            for mouse_name in keyboard_mouse.mouse_button_names:
                if keyboard_mouse.get_mouse_flag(mouse_name):
                    print(f'Mouse button: {mouse_name}')

            # sleeping 50 ms
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        keyboard_mouse.cleanup()
        print('End of the script.')