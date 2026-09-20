/* IMF (id Music Format) renderer using the MAME YM3812 core.
   Matches Wolf4SDL SD_StartMusic + SDL_IMFMusicPlayer at 700 Hz. */
#include "fmopl.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

enum { IMF_TICKS = 700 };

static uint16_t u16le(const uint8_t *p)
{
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

static int32_t count_samples(const uint8_t *imf, int32_t imf_len, int rate)
{
    int32_t pos = 0;
    int32_t remaining = imf_len;
    if (imf_len < 4)
        return 0;
    if (u16le(imf) != 0)
    {
        remaining = (int32_t)u16le(imf);
        pos = 2;
    }
    int32_t ticks = 0;
    while (remaining >= 4 && pos + 4 <= imf_len)
    {
        ticks += (int32_t)u16le(imf + pos + 2);
        pos += 4;
        remaining -= 4;
    }
    int64_t samples = ((int64_t)ticks * (int64_t)rate) / IMF_TICKS;
    if (samples < 1)
        samples = rate / 10;
    if (samples > (int64_t)rate * 180)
        samples = (int64_t)rate * 180;
    return (int32_t)samples;
}

int32_t luce_imf_pcm_bytes(const uint8_t *imf, int32_t imf_len, int32_t rate)
{
    if (!imf || imf_len < 4 || rate < 1000 || rate > 48000)
        return 0;
    return count_samples(imf, imf_len, rate) * 2;
}

static void emit_mono(int16_t *dest, int n)
{
    int16_t stereo[2048 * 2];
    while (n > 0)
    {
        int chunk = n > 2048 ? 2048 : n;
        YM3812UpdateOne(0, stereo, chunk);
        int i;
        for (i = 0; i < chunk; i++)
            dest[i] = stereo[i * 2];
        dest += chunk;
        n -= chunk;
    }
}

int32_t luce_imf_render(const uint8_t *imf, int32_t imf_len, int32_t rate,
    const uint8_t *dest, int32_t dest_len)
{
    if (!imf || !dest || imf_len < 4 || dest_len < 2 || rate < 1000)
        return -1;
    YM3812Shutdown();
    if (YM3812Init(1, 3579545, rate))
        return -1;
    int i;
    for (i = 1; i < 0xf6; i++)
        YM3812Write(0, i, 0);
    YM3812Write(0, 1, 0x20);

    int32_t pos = 0;
    int32_t remaining = imf_len;
    if (u16le(imf) != 0)
    {
        remaining = (int32_t)u16le(imf);
        pos = 2;
    }
    int32_t max_samples = dest_len / 2;
    int32_t written = 0;
    int16_t *out = (int16_t *)(void *)dest;
    int32_t samples_per_tick = rate / IMF_TICKS;
    if (samples_per_tick < 1)
        samples_per_tick = 1;

    while (remaining >= 4 && pos + 4 <= imf_len && written < max_samples)
    {
        uint8_t reg = imf[pos];
        uint8_t val = imf[pos + 1];
        int32_t delay = (int32_t)u16le(imf + pos + 2);
        YM3812Write(0, reg, val);
        int32_t n = delay * samples_per_tick;
        if (n > max_samples - written)
            n = max_samples - written;
        if (n > 0)
        {
            emit_mono(out + written, n);
            written += n;
        }
        pos += 4;
        remaining -= 4;
    }
    YM3812Shutdown();
    return written * 2;
}
