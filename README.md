# luce-audio

Short PCM playback for Luce/Base programs. The first backend is macOS
(NSSound). Windows and Linux are not implemented yet; `play_pcm8` fails with
`unsupported` there.

## Use

```toml
[dependencies]
luce_audio = "../luce-audio"
```

```luce
from audio import Player

var player = Player()
defer player.close()
try player.play_pcm8(samples, 7042)
```

`play_pcm8` plays unsigned 8-bit mono PCM. Several overlapping plays are kept
alive until later clips replace them.
