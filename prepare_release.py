# Prepare the release library
import os
import shutil
from subprocess import Popen, PIPE


def compile_clean(name_overlay: str, game_folder: str, out_lib_name: str,
                  disable_console: bool = True, finalize_folder: bool = False,
                  macos=False):
    """Compile an overlay program and clean the building files.

    Parameters
    ----------
    name_overlay       name of this overlay executable
    game_folder        specific game folder name for the path
    out_lib_name       name of the output library
    disable_console    True to disable the console output
    finalize_folder    True to finalize the folder (copy additional files, zip, clean)
    """
    icon = 'pictures/common/icon/salamander_sword_shield.ico'  # icon for the library

    # main nuitka command to run
    if macos:
        main_command = f"python -m nuitka --macos-create-app-bundle --macos-app-icon={icon}"
    else:
        main_command = ('cmd /c "python -m nuitka'
                        ' --standalone'
                        f' --windows-icon-from-ico={icon}'
                        f' --include-data-dir=common=common'
                        )

    main_command = main_command + (
        f" --output-dir={out_lib_name}"
        f" --plugin-enable=pyqt6"
        f' --include-data-dir={game_folder}={game_folder}'
        f' --include-data-dir=pictures/common=pictures/common'
        f' --include-data-dir=pictures/{game_folder}=pictures/{game_folder}'
        f' --include-data-dir=build_orders/{game_folder}=build_orders/{game_folder}'
        f' --include-data-dir=audio=audio'
    )
    if disable_console:  # disable the console
        command = main_command + f' --disable-console {name_overlay}.py'
    else:  # show the console
        command = main_command + f' {name_overlay}.py'

    print(command)
    print(Popen(command, stdout=PIPE, shell=True).communicate()[0].decode())  # compilation

    # rename executable name for version with console
    if not disable_console:
        os.rename(os.path.join(f'{name_overlay}.dist', f'{name_overlay}.exe'),
                  os.path.join(f'{name_overlay}.dist', f'{name_overlay}_with_console.exe'))

    # copy files in output directory
    if not macos:
        shutil.copytree(f'{out_lib_name}/{name_overlay}.dist', out_lib_name, dirs_exist_ok=True)
        shutil.rmtree(f'{out_lib_name}/{name_overlay}.dist')

    # clean building files
    # shutil.rmtree(f'{out_lib_name}/{name_overlay}.build')

    # finalize the output folder
    if finalize_folder:
        # copy readme, changelog, license and version
        shutil.copy('Readme.md', out_lib_name)
        shutil.copy('Changelog.md', out_lib_name)
        shutil.copy('LICENSE', out_lib_name)
        shutil.copy('version.json', out_lib_name)

        # copy remaining source files
        shutil.copy(f'{game_folder}_overlay.py', out_lib_name)
        shutil.copy('prepare_release.py', out_lib_name)

        # zip output folder
        shutil.make_archive(out_lib_name, 'zip', out_lib_name)
        # shutil.rmtree(out_lib_name)  # clean non-zipped files


if __name__ == '__main__':
    # name of the output libraries
    macos = False
    aoe2_library_name = 'aoe2_overlay'
    aoe4_library_name = 'aoe4_overlay'
    shutil.rmtree(aoe2_library_name, ignore_errors=True)
    shutil.rmtree(aoe4_library_name, ignore_errors=True)
    assert (not os.path.isdir(aoe2_library_name)) and (not os.path.isdir(aoe4_library_name))

    # Age of Empires II
    os.mkdir(aoe2_library_name)
    # compile_clean(name_overlay='aoe2_overlay', game_folder='aoe2', out_lib_name=aoe2_library_name,
    #               disable_console=False, finalize_folder=False, macos=macos)
    compile_clean(name_overlay='aoe2_overlay', game_folder='aoe2', out_lib_name=aoe2_library_name,
                  disable_console=True, finalize_folder=True, macos=macos)

    # Age of Empires IV
    # os.mkdir(aoe4_library_name)
    # compile_clean(name_overlay='aoe4_overlay', game_folder='aoe4', out_lib_name=aoe4_library_name,
    #               disable_console=False, finalize_folder=False, macos=macos)
    # compile_clean(name_overlay='aoe4_overlay', game_folder='aoe4', out_lib_name=aoe4_library_name,
    #               disable_console=True, finalize_folder=True, macos=macos)
