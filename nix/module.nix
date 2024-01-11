inputs: { config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.factorio-manager;
  name = "Factorio-Manager";
  stateDir = "/var/lib/${cfg.stateDirName}";
in
{
  options = {
    services.factorio-manager = {
      enable = mkEnableOption (lib.mdDoc name);
      port = mkOption {
        type = types.port;
        default = 50051;
        description = lib.mdDoc ''
          The port to which the service should bind.
        '';
      };

      bind = mkOption {
        type = types.str;
        default = "0.0.0.0";
        description = lib.mdDoc ''
          The address to which the service should bind.
        '';
      };

      openFirewall = mkOption {
        type = types.bool;
        default = false;
        description = lib.mdDoc ''
          grpc server listening.
        '';
      };

      stateDirName = mkOption {
        type = types.str;
        default = "factorio";
        description = lib.mdDoc ''
          Name of the directory under /var/lib holding the server's data.

          The configuration and map will be stored here.
        '';
      };
      package = mkPackageOption inputs.self.packages.${pkgs.stdenv.hostPlatform.system} "default" { };
      factorioPackage = mkPackageOption pkgs "factorio-headless" { };
    };
  };

  config = mkIf cfg.enable {
    systemd.services.factorio-manager-server = {
      description = "Factorio manager server";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];

      serviceConfig = {
        Restart = "always";
        KillSignal = "SIGINT";
        DynamicUser = true;
        StateDirectory = cfg.stateDirName;
        UMask = "0007";
        ExecStart = toString [
          "${getExe' cfg.package "factorio-manager-server"}"
          "--executable ${getExe' cfg.factorioPackage "factorio"}"
          "--data-dir ${stateDir}"
          "--port ${toString cfg.port}"
          "--host ${cfg.bind}"
        ];

        # Sandboxing
        NoNewPrivileges = true;
        PrivateTmp = true;
        PrivateDevices = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ProtectControlGroups = true;
        ProtectKernelModules = true;
        ProtectKernelTunables = true;
        RestrictAddressFamilies = [ "AF_UNIX" "AF_INET" "AF_INET6" "AF_NETLINK" ];
        RestrictRealtime = true;
        RestrictNamespaces = true;
        MemoryDenyWriteExecute = true;
      };
    };

    networking.firewall.allowedUDPPorts = optional cfg.openFirewall cfg.port;
  };
}
