# ABOUTME: Homebrew formula for make-audiobook CLI tools.
# ABOUTME: Copy this file to tigger04/homebrew-tap/Formula/ after tagging a release.

class MakeAudiobook < Formula
  desc "Convert documents to audiobooks using Piper or Kokoro TTS (CLI)"
  homepage "https://github.com/tigger04/make-audiobook"
  url "https://github.com/tigger04/make-audiobook/archive/refs/tags/v3.8.4.tar.gz"
  sha256 "620b5f0c8a2fcbd78b3314aa95ec7ec50b7bb11f4b962d15410ee4b2d521c31d"
  license "MIT"
  head "https://github.com/tigger04/make-audiobook.git", branch: "master"

  depends_on "bash" => "5.0"
  depends_on "espeak-ng"                 # required by Kokoro TTS engine
  depends_on "ffmpeg"
  depends_on "pandoc"
  depends_on "fzf"
  depends_on "fd"
  depends_on "pipx"
  depends_on "python@3.12"              # kokoro-tts requires Python <3.13

  def install
    bin.install "make-audiobook"
    bin.install "piper-voices-setup"
    bin.install "install-dependencies"
  end

  def post_install
    ohai "Run the following to complete setup:"
    ohai "  pipx install piper-tts"
    ohai "  pipx install kokoro-tts --python python3.12"
    ohai "  piper-voices-setup"
  end

  def caveats
    <<~EOS
      Complete setup by running:
        pipx install piper-tts
        pipx install kokoro-tts --python python3.12
        piper-voices-setup

      For .mobi file support, install calibre:
        brew install --cask calibre

      For additional Piper voices, visit:
        https://huggingface.co/rhasspy/piper-voices

      For the GUI version, install the cask instead:
        brew install --cask tigger04/tap/make-audiobook
    EOS
  end

  test do
    assert_match "USAGE", shell_output("#{bin}/make-audiobook --help", 0)
  end
end
