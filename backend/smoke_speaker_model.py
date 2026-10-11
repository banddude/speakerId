"""Optional local NeMo compatibility check, using a generated tone only.

Requires the full backend requirements. Downloads NVIDIA's public TitaNet model
on first run. Does not invoke AssemblyAI, Pinecone or use a real recording.
This proves API/embedding compatibility, not speaker-identification accuracy.
"""
import math
from pathlib import Path
import struct
import tempfile
import wave

import torch
from nemo.collections.asr.models import EncDecSpeakerLabelModel


def main():
    model = EncDecSpeakerLabelModel.from_pretrained(
        'nvidia/speakerverification_en_titanet_large', map_location='cpu'
    )
    model.eval()
    with tempfile.TemporaryDirectory() as directory:
        audio = Path(directory) / 'synthetic-tone.wav'
        with wave.open(str(audio), 'wb') as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(b''.join(
                struct.pack('<h', int(1000 * math.sin(2 * math.pi * 220 * t / 16000)))
                for t in range(32000)
            ))
        with torch.inference_mode():
            embedding = model.get_embedding(str(audio))
        assert embedding.shape == (1, 192), embedding.shape
        assert torch.isfinite(embedding).all()
        print('Synthetic speaker embedding passed:', tuple(embedding.shape))


if __name__ == '__main__':
    main()
