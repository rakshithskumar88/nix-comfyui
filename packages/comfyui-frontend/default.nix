{ buildNpmPackage, fetchFromGitHub }:

buildNpmPackage {
  name = "comfyui-frontend";

  src = fetchFromGitHub {
    owner = "Comfy-Org";
    repo = "ComfyUI_frontend";
    fetchSubmodules = false;
    rev = "43548785b5b0124c81e3a9d7b299bf48631c0253";
    hash = "sha256-G4xvX+TWMGgqnZyqEtlb+yZ9POb5mOadlNZOraq7y68=";
  };

  npmDepsHash = "sha256-KR8NIsPc2J6aj57Gl0nfNB26LpYlC5xyR3mpMVjsemo=";

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
