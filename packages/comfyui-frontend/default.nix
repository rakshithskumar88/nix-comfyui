{ buildNpmPackage, fetchFromGitHub }:

buildNpmPackage {
  name = "comfyui-frontend";

  src = fetchFromGitHub {
    owner = "Comfy-Org";
    repo = "ComfyUI_frontend";
    fetchSubmodules = false;
    rev = "a2549f23c74374963a0d98c6ba8cbdbed3ca7ab0";
    hash = "sha256-EisHrKyQcR51KyFKHTO3rf8d1t9vXkeZXwsYD10HAq4=";
  };

  npmDepsHash = "sha256-wHVfxjt77pt5T2Co4+4z2OJuwbvoqny3PPVAJA/lgwc=";

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
