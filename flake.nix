{
  description = "flake for factorio manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    poetry2nix.url = "github:nix-community/poetry2nix";
    nuenv.url = "github:DeterminateSystems/nuenv";
  };

  nixConfig = {
    extra-trusted-public-keys = "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw=";
    extra-substituters = "https://devenv.cachix.org";
  };

  outputs = inputs@{ flake-parts, devenv, poetry2nix, nixpkgs, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } ({ withSystem, ... }: {
      imports = [
        inputs.devenv.flakeModule
      ];
      systems = [ "x86_64-linux" "aarch64-linux" ];
      perSystem = { config, self', inputs', pkgs, system, ... }:
        let
          inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication;
        in
        {
          _module.args.pkgs = import inputs.nixpkgs {
            inherit system;
            overlays = with inputs;[
              nuenv.overlays.default
            ];
          };
          packages.default = mkPoetryApplication {
            projectDir = ./.;
          };

          # broken `nix flake show` but doesn't matter.
          devenv.shells.default = {
            languages.python = {
              enable = true;
              poetry.enable = true;
            };
            dotenv.enable = true;
            enterShell = ''
              export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
            '';
          };

          formatter = pkgs.nixpkgs-fmt;
        };
      flake = {
        nixosModules =
          let
            factorio-manager-server = { pkgs, ... }: {
              imports = [ ./nix/module.nix ];
              services.factorio-manager.package =
                withSystem pkgs.stdenv.hostPlatform.system ({ config, ... }:
                  config.packages.default
                );
            };
          in
          {
            inherit factorio-manager-server;
            default = factorio-manager-server;
          };
      };
    });
}
