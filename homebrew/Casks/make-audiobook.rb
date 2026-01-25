# ABOUTME: Homebrew cask for make-audiobook GUI application.
# ABOUTME: Copy this file to tigger04/homebrew-tap/Casks/ after building a release.

cask "make-audiobook" do
  version "0.1.0"
  sha256 "UPDATE_WITH_ACTUAL_SHA256"

  url "https://github.com/tigger04/make-audiobook/releases/download/v#{version}/make-audiobook-#{version}.dmg"
  name "make-audiobook"
  desc "Convert documents to audiobooks using Piper TTS"
  homepage "https://github.com/tigger04/make-audiobook"

  # System dependencies installed via Homebrew
  depends_on formula: "ffmpeg"
  depends_on formula: "pandoc"
  depends_on formula: "fzf"
  depends_on formula: "fd"
  depends_on formula: "pipx"

  app "make-audiobook.app"

  # Make CLI scripts available in PATH
  binary "#{appdir}/make-audiobook.app/Contents/Resources/scripts/make-audiobook"
  binary "#{appdir}/make-audiobook.app/Contents/Resources/scripts/piper-voices-setup"

  postflight do
    # Install piper-tts via pipx (handles Python isolation)
    ohai "Installing piper-tts..."
    system_command "/opt/homebrew/bin/pipx",
                   args: ["install", "piper-tts"],
                   sudo: false

    ohai "To install default voices, run: piper-voices-setup"
  end

  # Note: piper-tts and voices remain after uninstall.
  # To fully remove: pipx uninstall piper-tts && rm -rf ~/.local/share/piper

  zap trash: [
    "~/.local/share/piper",
    "~/Library/Application Support/make-audiobook",
    "~/Library/Preferences/com.tigger04.make-audiobook.plist",
    "~/Library/Caches/make-audiobook",
  ]

  caveats <<~EOS
    To install default English voices, run:
      piper-voices-setup

    For additional voices, use the GUI voice browser or visit:
      https://huggingface.co/rhasspy/piper-voices
  EOS
end
