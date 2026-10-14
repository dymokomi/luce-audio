# luce-audio

A realtime audio engine for Luce/Base programs (the `engine` module), its
CoreAudio device (`device`), and short PCM playback (`audio`).

## The engine

A program of tracks, units (an instrument or effect: a patch of nodes run per
voice) and lanes of notes and curves, built on the main thread (`begin` …
`commit`) and run on the device's realtime thread or offline (`render`).
Notes start and end on their sample. A new program takes over at a buffer's
start with the running state (voices, phases, filters, envelopes, delay lines,
sounding notes) carried over by id, so editing while playing never clicks.
Knobs, transport and played notes go through a lock-free ring; position,
load and meters come back through atomics. Nothing on the audio thread
allocates, locks, fails or calls into Luce. The node kinds (`kinds`) are a
table an application reads to offer them: oscillators (PolyBLEP), a
state-variable filter, envelopes, LFOs, mixing, panning, drive, delay,
reverb, glide.

```luce
from luce_audio import engine
let e = engine.open(48000.0)
e.begin()
# add_track, add_unit, add_node, wire, add_lane, play_notes, add_note ...
e.commit()
e.start_output(64)        # 64-frame buffers: 1.3 ms at 48 kHz
e.play()
```

`tools/probe` plays a quiet tone on the default output and reports the
device's buffer, latency and the longest callback.

### Scales and live MIDI

`add_key` gives the song (track -1) or a track a timeline of scale keys
(`scale_modes`: Major, Minor, the modes, pentatonics, Blues and more); a
track following them (`add_track(..., keyed = 1)`) plays every note in the
key in force where it starts, written notes unchanged. The Scale Quantize
node snaps a pitch signal to the track's key or its own.

`open_midi` listens to every MIDI source (through luce-midi); a track given
`midi_in` and `channel` plays the units `listen` names, through its scale,
on the audio thread. `midi_next` hands the main thread each message for
recording, and `beat_at` places it on the beat it was heard at.
`set_metronome` clicks the beats.

### Audio input

`device.Device.open(..., inputs = 2, first_input = 0)` opens the output
device duplex: each block carries its input channels too, and
`input_latency` says how far to shift a recording. `tools/input_probe`
measures it (an app bundle, so macOS can ask for the microphone).

## Short PCM playback

Short PCM playback for Luce/Base programs. The first backend is macOS
(NSSound). Windows and Linux are not implemented yet; `play_pcm8` fails with
`unsupported` there.

## Use

```toml
[dependencies]
luce_audio = "../luce-audio"
```

```luce
from luce_audio.audio import Player

var player = Player()
defer player.close()
try player.play_pcm8(samples, 7042)
```

`play_pcm8` plays unsigned 8-bit mono PCM. Several overlapping plays are kept
alive until later clips replace them.
