{ buildExtension, fetchFromGitHub, lib, python3 }:

buildExtension {
  name = "gourieff-reactor";
  version = "0.0.0";

  src = fetchFromGitHub {
    owner = "Gourieff";
    repo = "comfyui-reactor-node";
    fetchSubmodules = false;
    rev = "b3d85c761c5c8d113d0ad6e8845996cc83215d29";
    hash = "sha256-Xy0hT5NWd5+k5o8kJtHz4qXyxsBDVfLQ2iYxywgZjoY=";
  };

  propagatedBuildInputs = [
    python3.pkgs.albumentations
    python3.pkgs.insightface
    python3.pkgs.numpy
    python3.pkgs.onnx
    python3.pkgs.onnxruntime
    python3.pkgs.opencv-python
    python3.pkgs.pillow
    python3.pkgs.pyyaml
    python3.pkgs.requests
    python3.pkgs.safetensors
    python3.pkgs.scipy
    python3.pkgs.segment-anything
    python3.pkgs.torch
    python3.pkgs.torchvision
    python3.pkgs.tqdm
    python3.pkgs.ultralytics
  ];

  postPatch = ''
    rm install.py

    find . -type f -name "*.py" | while IFS= read -r filename; do
      substituteInPlace "$filename" \
        --replace-quiet \
          'CATEGORY = "🌌 ReActor' \
          'CATEGORY = "reactor' \
        --replace-quiet " 🌌 ReActor" "" \
        --replace-quiet "ReActor 🌌 " ""

      sed --in-place \
        "s/[[:space:]]*🌌[[:space:]]*//g" \
        -- "$filename"
    done
  '';

  passthru = {
    check-pkgs.ignoredModuleNames = [
      "^custom_nodes.facerestore(\\..+)?$"
      "^lmdb$"
      "^mc$"
      "^modules(\\..+)?$"
      "^r_basicsr(\\..+)?$"
      "^r_chainner(\\..+)?$"
      "^r_facelib(\\..+)?$"
      "^reactor_patcher$"
      "^reactor_utils$"
      "^scripts(\\..+)?$"
      "^tensorboard(\\..+)?$"
      "^torchvision.transforms.functional_tensor$"
      "^wandb$"
    ];
  };

  meta = {
    license = lib.licenses.gpl3;
  };
}
