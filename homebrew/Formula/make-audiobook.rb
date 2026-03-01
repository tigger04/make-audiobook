# ABOUTME: Homebrew formula for make-audiobook CLI tools.
# ABOUTME: Copy this file to tigger04/homebrew-tap/Formula/ after tagging a release.

class MakeAudiobook < Formula
  desc "Convert documents to audiobooks using Piper or Kokoro TTS (CLI)"
  homepage "https://github.com/tigger04/make-audiobook"
  url "https://github.com/tigger04/make-audiobook/archive/refs/tags/v3.7.0.tar.gz"
  sha256 "d809cde887c21da3046a6b2072e57dfc6c696e5f194a7f7689839cbb3c2aad38"
  license "MIT"
  head "https://github.com/tigger04/make-audiobook.git", branch: "master"

  depends_on "bash" => "5.0"
  depends_on "calibre" => :recommended  # for .mobi file support
  depends_on "espeak"                    # required by Kokoro TTS engine
  depends_on "ffmpeg"
  depends_on "pandoc"
  depends_on "fzf"
  depends_on "fd"
  depends_on "pipx"

  def install
    bin.install "make-audiobook"
    bin.install "piper-voices-setup"
    bin.install "install-dependencies"
  end

  def post_install
    ohai "Installing piper-tts via pipx..."
    system "pipx", "install", "piper-tts"
    ohai "Installing kokoro-tts via pipx..."
    system "pipx", "install", "kokoro-tts"
    ohai "To install default voices, run: piper-voices-setup"
  end

  def caveats
    <<~EOS
      piper-tts has been installed via pipx.

      To install default English voices, run:
        piper-voices-setup

      For additional voices, visit:
        https://huggingface.co/rhasspy/piper-voices

      For Kokoro TTS engine (optional, higher quality):
        brew install espeak
        pipx install kokoro-tts

      For the GUI version, install the cask instead:
        brew install --cask tigger04/tap/make-audiobook
    EOS
  end

  test do
    assert_match "usage", shell_output("#{bin}/make-audiobook --help", 0)
  end
end
