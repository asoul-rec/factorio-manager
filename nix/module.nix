{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.factorio-manager;
  name = "Factorio-Manager";
  stateDir = "/var/lib/${cfg.stateDirName}";
  configFile = pkgs.writeText "factorio.conf" ''
    use-system-read-write-data-directories=true
    [path]
    read-data=${cfg.factorioPackage}/share/factorio/data
    write-data=${stateDir}
  '';
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
      package = mkOption {
        defaultText = lib.literalMD "`packages.default` from this flake";
      };
      factorioPackage = mkPackageOption pkgs "factorio-headless" { };
      botConfigPath = mkOption {
        type = types.str;
        default = "";
      };
      serverSettingsFile = mkOption {
        type = types.str;
        default = "";
        description = lib.mdDoc ''
          The server settings file.
        '';
      };
      serverAdminsFile = mkOption {
        type = types.str;
        default = "";
        description = lib.mdDoc ''
          The server admins file.
        '';
      };
    };
  };

  config = mkIf cfg.enable
    (
      let
        hardeningConfig =
          {
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
      in
      {
        users.users.factorio = {
          group = "factorio";
          isSystemUser = true;
        };
        users.groups.factorio = { };

        systemd.services.factorio-manager-server = {
          description = "Factorio manager server";
          wantedBy = [ "multi-user.target" ];
          after = [ "network.target" ];


          serviceConfig = {
            Restart = "always";
            User = "factorio";
            Environment = [ "FACTORIO_MANAGER_DEBUG=1" ];
            StateDirectory = cfg.stateDirName;
            KillMode = "mixed";
            TimeoutStopSec = 30;
            KillSignal = "SIGINT";
            SendSIGKILL = "yes";
            ExecStart = toString [
              "${getExe' cfg.package "factorio-manager-server"}"
              "--executable ${getExe' cfg.factorioPackage "factorio"}"
              "--data-dir ${stateDir}"
              "--port ${toString cfg.port}"
              "--host ${cfg.bind}"
            ];
          } // hardeningConfig;
        };

        systemd.services.factorio-manager-client = {
          description = "Factorio manager client";
          wantedBy = [ "multi-user.target" ];
          after = [ "network.target" "factorio-manager-server.service" ];

          preStart = "ln -sfT ${configFile} ${stateDir}/factorio.conf";

          serviceConfig = {
            Restart = "always";
            User = "factorio";
            StateDirectory = cfg.stateDirName;
            ExecStart = toString [
              "${getExe' cfg.package "factorio-manager-client"}"
              "--bot_config ${cfg.botConfigPath}"
            ];
          } // hardeningConfig;
        };
        networking.firewall.allowedUDPPorts = optional cfg.openFirewall cfg.port;
      }
    );
}
