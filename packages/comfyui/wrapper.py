import json
import os
import shlex
import shutil
import sys

is_debug = bool(os.environ.get("NIX_COMFYUI_DEBUG"))


def main():
    detect_old_state()

    spec_path = sys.argv[1]
    debug(f"Reading file: {shlex.quote(spec_path)}")
    with open(spec_path) as f:
        spec = json.load(f)

    bwrap = spec["bwrap"]
    bwrap_args = spec["bwrap_args"]
    comfyui = spec["comfyui"]
    comfyui_args = spec["comfyui_args"]
    extensions = spec["extensions"]
    frontend = spec["frontend"]
    interpreter = spec["interpreter"]
    prepopulated_state_files = sorted(spec["prepopulated_state_files"])
    state_dirs = spec["state_dirs"]

    for path in os.environ.get("NIX_COMFYUI_STATE_DIRS", "").split(":"):
        if path: state_dirs.append(path)

    state_dirs.sort()

    cwd = os.getcwd()
    cmd = []

    cmd.extend(["bwrap"])

    # Make the world readable and writable. The script's purpose is to make
    # state files to appear under paths hardcoded by ComfyUI and its extensions,
    # and not to isolate the application from the rest of the system. In the
    # latter case, one should use containers, systemd or any other solutions.
    cmd.extend(["--dev-bind", "/", "/"])

    # Mount a tmpfs at the current working directory ($PWD) to avoid unnecessary
    # file creation by bwrap. Without this option, $PWD would be filled with
    # empty files and directories like comfy/, comfy_extras/ etc., on each
    # application restart. Paths within $PWD that should survive restarts are
    # listed explicitly in state_dirs and prepopulated_state_files.
    cmd.extend(["--tmpfs", cwd])

    # Bind-mount ComfyUI's root files one by one.
    # - $PWD/comfy        -> /nix/store/...comfyui-unwrapped.../comfy
    # - $PWD/comfy_extras -> /nix/store/...comfyui-unwrapped.../comfy_extras
    # - $PWD/main.py      -> /nix/store/...comfyui-unwrapped.../main.py
    # and so on.
    for name in os.listdir(comfyui):
        if name == "custom_nodes": continue
        if name in state_dirs: continue
        if name in prepopulated_state_files: continue
        cmd.extend(["--ro-bind", f"{comfyui}/{name}", f"{cwd}/{name}"])

    # Bind-mount the chosen frontend.
    # - $PWD/web -> /nix/store/...comfyui-frontend.../web
    cmd.extend(["--ro-bind", frontend, f"{cwd}/web"])

    # For each extension, bind-mount its corresponding directory.
    # - $PWD/custom_nodes/foo -> /nix/store/...foo...
    # - $PWD/custom_nodes/bar -> /nix/store/...bar...
    # - $PWD/custom_nodes/baz -> /nix/store/...baz...
    # and so on.
    for name, path in extensions.items():
        cmd.extend(["--ro-bind", path, f"{cwd}/custom_nodes/{name}"])

    # Bind-mount each specified state directory to prevent it from being
    # shadowed by the tmpfs at $PWD.
    # - $PWD/input  -> $PWD/input
    # - $PWD/models -> $PWD/models
    # and so on. Additional directories can be added via:
    # comfyui.override { stateDirs = [ "foo" "bar/baz" ]; }
    # They can also be added with $NIX_COMFYUI_STATE_DIRS:
    # export NIX_COMFYUI_STATE_DIRS=foo:bar/baz
    for path in state_dirs:
        mkdir(path)
        cmd.extend(["--bind", f"{cwd}/{path}", f"{cwd}/{path}"])

    # For each prepopulated state file, if it doesn't exist at $PWD, copy it
    # from the ComfyUI or extension directories and bind-mount it.
    # - $PWD/extra_model_paths.yaml -> $PWD/extra_model_paths.yaml
    #   (from /nix/store/...comfyui-unwrapped.../extra_model_paths.yaml)
    # and so on. Additional files can be added via:
    # comfyui.override { prepopulatedStateFiles = [ "foo.txt" ]; }
    for target in prepopulated_state_files:
        parts = target.split("/")

        if parts[0] == "custom_nodes":
            extension_path = extensions[parts[1]]
            rest_path = "/".join(parts[2:])
            source = f"{extension_path}/{rest_path}"
        else:
            source = f"{comfyui}/{target}"

        target_dir = os.path.dirname(target) or "."

        if not exists(target):
            mkdir(target_dir)
            cp(source, target)

        cmd.extend(["--bind", f"{cwd}/{target}", f"{cwd}/{target}"])

    # Use user-specified bwrap arguments. Example usage:
    # comfyui.override { bwrapArgs = [ "--setenv" "FOO" "BAR" ]; }
    cmd.extend(bwrap_args)

    cmd.extend(["--"])

    cmd.extend([interpreter, "main.py"])

    # Use user-specified ComfyUI arguments. Example usage:
    # comfyui.override { commandLineArgs = [ "--preview-method" "taesd" ]; }
    cmd.extend(comfyui_args)

    # The arguments received by this script are passed to ComfyUI.
    cmd.extend(sys.argv[2:])

    # Point rembg to $PWD/models/u2net.
    # https://github.com/danielgatis/rembg/blob/1101c152/rembg/sessions/base.py#L74-L80
    if not os.environ.get("U2NET_HOME"):
        setenv("U2NET_HOME", f"{cwd}/models/u2net")

    if is_debug:
        print("Executing: bwrap \\")
        for i, arg in enumerate(cmd):
            if i == 0: continue
            last_chars = "" if i == len(cmd) - 1 else " \\"
            print(f"  {shlex.quote(arg)}{last_chars}")

    os.execvp(bwrap, cmd)


def detect_old_state():
    if os.environ.get("NIX_COMFYUI_BYPASS_CHECKS"):
        return

    # yapf: disable
    renamed_dirs = {
        "models/controlnet_aux/ckpts": "custom_nodes/fannovel16-controlnet-aux/ckpts",
        "models/fonts": "custom_nodes/cubiq-essentials/fonts",
        "models/frame_interpolation": "custom_nodes/fannovel16-frame-interpolation/ckpts",
        "models/luts": "custom_nodes/cubiq-essentials/luts",
        "models/safetychecker": "custom_nodes/acly-tooling/safetychecker",
    }
    # yapf: enable

    messages = []

    for old_path, new_path in renamed_dirs.items():
        if len(lsdir(old_path)) > 0:
            if new_path is None:
                messages.append(f"{shlex.quote(old_path)} contains files;\n" +
                                f"move them to appropriate places;")
            else:
                messages.append(f"{shlex.quote(old_path)} contains files;\n" +
                                f"move them to {shlex.quote(new_path)};")

    if len(messages) > 0:
        print("Current directory requires migration:")
        for message in messages:
            message = message.replace("\n", "\n  ")
            print(f"\n* {message}")
        print("\nSet NIX_COMFYUI_BYPASS_CHECKS=1 to bypass these checks.")
        exit(1)


def cp(source, target):
    debug(f"Copying {shlex.quote(source)} to {shlex.quote(target)}")
    shutil.copyfile(source, target)


def exists(path):
    debug(f"Checking for existence: {shlex.quote(path)}")
    return os.path.exists(path)


def lsdir(path):
    debug(f"Listing files: {path}")
    try:
        return os.listdir(path)
    except FileNotFoundError:
        return []


def mkdir(path):
    debug(f"Creating directory: {shlex.quote(path)}")
    os.makedirs(path, exist_ok=True)


def setenv(name, value):
    debug(f"Setting {shlex.quote(name)} to {shlex.quote(value)}")
    os.environ[name] = value


def debug(message):
    if is_debug:
        print(message)


if __name__ == "__main__":
    main()
