# ABOUTME: Homebrew formula for make-audiobook CLI tools.
# ABOUTME: Copy this file to tigger04/homebrew-tap/Formula/ after tagging a release.

class MakeAudiobook < Formula
  desc "Convert documents to audiobooks using Piper TTS (CLI)"
  homepage "https://github.com/tigger04/make-audiobook"
  url "https://github.com/tigger04/make-audiobook/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "UPDATE_WITH_ACTUAL_SHA256"
  license "MIT"
  head "https://github.com/tigger04/make-audiobook.git", branch: "master"

  depends_on "bash" => "5.0"
  depends_on "ffmpeg"
  depends_on "pandoc"
  depends_on "fzf"
  depends_on "fd"
  depends_on "pipx"

  def install
    bin.install "make-audiobook"
    bin.install "piper-voices-setup"
    bin.install "install-dependencies"

    # Install shell helper scripts
    (libexec/"shell-and-scripting-helpers").install Dir["shell-and-scripting-helpers/*"]

    # Create wrapper that sources helpers from correct location
    (bin/"piper-voices-setup").write <<~EOS
      #!/usr/bin/env bash
      source "#{libexec}/shell-and-scripting-helpers/.qfuncs.sh"
      exec "#{libexec}/piper-voices-setup.real" "$@"
    EOS

    # Move original script
    libexec.install bin/"piper-voices-setup" => "piper-voices-setup.real"
  end

  def post_install
    ohai "Installing piper-tts via pipx..."
    system "pipx", "install", "piper-tts"

    ohai "To install default voices, run: piper-voices-setup"
  end

  def caveats
    <<~EOS
      piper-tts has been installed via pipx.

      To install default English voices, run:
        piper-voices-setup

      For additional voices, visit:
        https://huggingface.co/rhasspy/piper-voices

      For the GUI version, install the cask instead:
        brew install --cask tigger04/tap/make-audiobook
    EOS
  end

  test do
    assert_match "usage", shell_output("#{bin}/make-audiobook --help", 0)
  end
end
