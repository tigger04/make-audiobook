# ABOUTME: Homebrew cask for make-audiobook GUI application.
# ABOUTME: Copy this file to tigger04/homebrew-tap/Casks/ after tagging a release.

cask "make-audiobook" do
  version "3.8.4"
  sha256 "UPDATE_WITH_ACTUAL_SHA256"

  url "https://github.com/tigger04/make-audiobook/releases/download/v#{version}/make-audiobook-#{version}.dmg"
  name "make-audiobook"
  desc "Convert documents to audiobooks using Kokoro or Piper TTS"
  homepage "https://github.com/tigger04/make-audiobook"

  # System dependencies installed via Homebrew
  depends_on formula: "espeak-ng"  # required by Kokoro TTS engine
  depends_on formula: "ffmpeg"
  depends_on formula: "pandoc"
  depends_on formula: "fzf"
  depends_on formula: "fd"
  depends_on formula: "pipx"
  depends_on formula: "python@3.12"

  app "make-audiobook.app"

  # Make CLI scripts available in PATH
  binary "#{appdir}/make-audiobook.app/Contents/Resources/scripts/make-audiobook"
  binary "#{appdir}/make-audiobook.app/Contents/Resources/scripts/piper-voices-setup"

  postflight do
    # Install kokoro-tts via pipx (default engine)
    ohai "Installing kokoro-tts (default engine)..."
    system_command "/opt/homebrew/bin/pipx",
                   args: ["install", "kokoro-tts", "--python",
                          "/opt/homebrew/opt/python@3.12/bin/python3.12"],
                   sudo: false

    # Install piper-tts via pipx (alternative engine)
    ohai "Installing piper-tts (alternative engine)..."
    system_command "/opt/homebrew/bin/pipx",
                   args: ["install", "piper-tts"],
                   sudo: false

    # Install default English voices for Piper
    ohai "Installing default Piper voices..."
    system_command "#{staged_path}/make-audiobook.app/Contents/Resources/scripts/piper-voices-setup",
                   sudo: false
  end

  # Note: kokoro-tts, piper-tts and voices remain after uninstall.
  # To fully remove: pipx uninstall kokoro-tts && pipx uninstall piper-tts && rm -rf ~/.local/share/piper

  zap trash: [
    "~/.local/share/piper",
    "~/.local/share/kokoro",
    "~/Library/Application Support/make-audiobook",
    "~/Library/Preferences/com.tigger04.make-audiobook.plist",
    "~/Library/Caches/make-audiobook",
  ]

  caveats <<~EOS
    Kokoro TTS (default) and Piper TTS have been installed automatically.
    Default Piper voices have also been installed.

    To update Piper voices, run: piper-voices-setup

    For additional Piper voices, use the GUI voice browser or visit:
      https://huggingface.co/rhasspy/piper-voices

    For .mobi file support, install calibre:
      brew install --cask calibre
  EOS
end
