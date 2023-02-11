import os
game_folder="aoe2"

# main nuitka command to run
main_command = ('cmd /c "python -m nuitka'
                ' --standalone'
                ' --plugin-enable=PyQt6'
                ' --onefile'
                ' --macos-create-app-bundle'
                f' --include-data-dir=common=common'
                f' --include-data-dir={game_folder}={game_folder}'
                f' --include-data-dir=pictures/common=pictures/common'
                f' --include-data-dir=pictures/{game_folder}=pictures/{game_folder}'
                f' --include-data-dir=build_orders/{game_folder}=build_orders/{game_folder}'
                f' --include-data-dir=audio=audio'
                )

main_command = main_command + f' aoe2_overlay.py'
os.system(main_command)