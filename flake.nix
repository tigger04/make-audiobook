# ABOUTME: Nix flake for building and running make-audiobook.
# ABOUTME: Provides CLI and GUI packages plus a development shell.

{
  description = "Convert documents to audiobooks using Piper TTS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    shell-helpers = {
      url = "github:tigger04/shell-and-scripting-helpers";
      flake = false;
    };
  };

  outputs = { self, nixpkgs, flake-utils, shell-helpers }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python312;

        version = "2.0.2";

        # Runtime dependencies for CLI scripts
        runtimeDeps = with pkgs; [
          bash
          piper-tts
          ffmpeg
          pandoc
          fzf
          fd
          pv
          bc
          gnused
          coreutils
          curl
          gnugrep
        ];

        # Python environment for GUI
        pythonEnv = python.withPackages (ps: with ps; [
          pyside6
          requests
        ]);

        # Shared install logic for CLI scripts
        installCli = ''
          mkdir -p $out/bin $out/share/make-audiobook

          # Copy scripts and shell helpers
          cp make-audiobook $out/share/make-audiobook/
          cp piper-voices-setup $out/share/make-audiobook/
          cp -r ${shell-helpers} $out/share/make-audiobook/shell-and-scripting-helpers

          chmod +x $out/share/make-audiobook/make-audiobook
          chmod +x $out/share/make-audiobook/piper-voices-setup

          # Create wrapper scripts with runtime deps on PATH
          makeWrapper $out/share/make-audiobook/make-audiobook $out/bin/make-audiobook \
            --prefix PATH : ${pkgs.lib.makeBinPath runtimeDeps}

          makeWrapper $out/share/make-audiobook/piper-voices-setup $out/bin/piper-voices-setup \
            --prefix PATH : ${pkgs.lib.makeBinPath runtimeDeps}
        '';

      in {
        packages = {
          # CLI-only package
          cli = pkgs.stdenv.mkDerivation {
            pname = "make-audiobook-cli";
            inherit version;
            src = ./.;

            nativeBuildInputs = [ pkgs.makeWrapper ];

            dontBuild = true;

            installPhase = installCli;

            meta = with pkgs.lib; {
              description = "Convert documents to audiobooks using Piper TTS (CLI)";
              homepage = "https://github.com/tigger04/make-audiobook";
              license = licenses.mit;
              platforms = platforms.unix;
              mainProgram = "make-audiobook";
            };
          };

          # GUI package (includes CLI)
          default = pkgs.stdenv.mkDerivation {
            pname = "make-audiobook";
            inherit version;
            src = ./.;

            nativeBuildInputs = [ pkgs.makeWrapper ];

            dontBuild = true;

            installPhase = ''
              ${installCli}

              # Install GUI Python module
              mkdir -p $out/lib/make-audiobook
              cp -r gui $out/lib/make-audiobook/

              # Create GUI wrapper
              makeWrapper ${pythonEnv}/bin/python3 $out/bin/make-audiobook-gui \
                --add-flags "-m gui" \
                --prefix PATH : ${pkgs.lib.makeBinPath runtimeDeps} \
                --prefix PATH : $out/bin \
                --set PYTHONPATH $out/lib/make-audiobook
            '';

            meta = with pkgs.lib; {
              description = "Convert documents to audiobooks using Piper TTS";
              homepage = "https://github.com/tigger04/make-audiobook";
              license = licenses.mit;
              platforms = platforms.unix;
              mainProgram = "make-audiobook-gui";
            };
          };
        };

        devShells.default = pkgs.mkShell {
          packages = runtimeDeps ++ [
            pythonEnv
            python.pkgs.pytest
            python.pkgs.pytest-qt
          ];
        };
      });
}
