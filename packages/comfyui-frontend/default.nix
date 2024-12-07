{ buildNpmPackage, fetchFromGitHub }:

buildNpmPackage {
  name = "comfyui-frontend";

  src = fetchFromGitHub {
    owner = "Comfy-Org";
    repo = "ComfyUI_frontend";
    fetchSubmodules = false;
    rev = "7025e321de3dfc49226c5f34c85df1c351b80633";
    hash = "sha256-4sJ3l+az1RHe+OyTONjClHLeglpid/CYsNnAPBEcaQk=";
  };

  npmDepsHash = "sha256-vwVvUpZ/W1xcSgtbc0U7XdmwCbIbfzPQljIpXpTSN/E=";

  patches = [
    ./0001-use-neutral-colors.patch
  ];

  installPhase = ''
    runHook preInstall

    mkdir --parents $out/share/comfyui
    cp --archive dist $out/share/comfyui/web

    runHook postInstall
  '';
}
