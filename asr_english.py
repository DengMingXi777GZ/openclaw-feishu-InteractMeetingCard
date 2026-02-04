#!/usr/bin/env python3
"""
ReSpeaker ASR 模块 (英文版 - Whisper Tiny) - API 修正版
"""

import subprocess
import numpy as np
import sherpa_onnx
import os
import logging
from typing import Optional, Tuple, List
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ASRConfig:
    """ASR 配置"""
    record_card: int = 2
    record_device: int = 0
    channels: int = 2
    sample_rate: int = 16000
    format: str = "S16_LE"
    model_dir: str = "./asr_model_en"  # 修改为本目录
    default_duration: int = 8
    temp_dir: str = "/tmp"


class RespeakerASR:
    def __init__(self, config: Optional[ASRConfig] = None):
        self.config = config or ASRConfig()
        self.config.model_dir = os.path.expanduser(self.config.model_dir)
        self.model_path = Path(self.config.model_dir)
        self.recognizer = None
        self._init_model()
    
    def _find_model_files(self) -> Tuple[str, str, str]:
        """查找模型文件"""
        patterns = [
            ("tiny.en-encoder.onnx", "tiny.en-decoder.onnx", "tiny.en-tokens.txt"),
            ("tiny.en-encoder.int8.onnx", "tiny.en-decoder.int8.onnx", "tiny.en-tokens.txt"),
            ("tiny-encoder.onnx", "tiny-decoder.onnx", "tiny-tokens.txt"),
            ("encoder.onnx", "decoder.onnx", "tokens.txt"),
        ]
        
        for enc_name, dec_name, tok_name in patterns:
            encoder = self.model_path / enc_name
            decoder = self.model_path / dec_name
            tokens = self.model_path / tok_name
            
            if encoder.exists() and decoder.exists() and tokens.exists():
                logger.info(f"✅ 使用模型: {enc_name}")
                return str(encoder), str(decoder), str(tokens)
        
        files = list(self.model_path.glob("*.onnx")) + list(self.model_path.glob("*.txt"))
        raise FileNotFoundError(
            f"模型文件未找到！目录: {[f.name for f in files]}"
        )
    
    def _init_model(self):
        """初始化 Whisper 模型"""
        if not self.model_path.exists():
            # 创建模型目录
            self.model_path.mkdir(parents=True, exist_ok=True)
            logger.warning(f"模型目录不存在，已创建: {self.model_path}")
            logger.warning("请下载Whisper模型文件到该目录")
        
        try:
            encoder_path, decoder_path, tokens_path = self._find_model_files()
        except FileNotFoundError:
            logger.error("模型文件未找到，请下载后重试")
            logger.info("模型下载地址:")
            logger.info("https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/tiny.en-encoder.onnx")
            logger.info("https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/tiny.en-decoder.onnx") 
            logger.info("https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/tiny.en-tokens.txt")
            raise
        
        logger.info("🧠 加载 Whisper Tiny English...")
        
        # Whisper 使用 OfflineRecognizer（整段识别）
        self.recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=encoder_path,
            decoder=decoder_path,
            tokens=tokens_path,
            num_threads=4,
            decoding_method="greedy_search",
            language="en",
            task="transcribe",
        )
        
        logger.info("✅ 模型加载完成")
    
    def record(self, duration: Optional[int] = None, output_file: Optional[str] = None) -> str:
        """录音"""
        duration = duration or self.config.default_duration
        if output_file is None:
            output_file = os.path.join(self.config.temp_dir, f"rec_{os.getpid()}.wav")
        
        logger.info(f"🎙️  录音 {duration}秒...")
        
        cmd = [
            "arecord",
            "-D", f"plughw:{self.config.record_card},{self.config.record_device}",
            "-c", str(self.config.channels),
            "-r", str(self.config.sample_rate),
            "-f", self.config.format,
            "-d", str(duration),
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"录音失败: {result.stderr}")
        
        return output_file
    
    def convert_to_mono(self, input_file: str) -> str:
        """转单声道"""
        output_file = input_file.replace(".wav", "_mono.wav")
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", input_file,
            "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
            output_file
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_file
    
    def recognize_file(self, audio_file: str) -> str:
        """识别音频"""
        # 检查并转换通道
        try:
            info_cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0", 
                       "-show_entries", "stream=channels", "-of", "default=noprint_wrappers=1", audio_file]
            result = subprocess.run(info_cmd, capture_output=True, text=True, check=True)
            channels = int(result.stdout.strip().split("=")[1])
            if channels > 1:
                audio_file = self.convert_to_mono(audio_file)
        except:
            audio_file = self.convert_to_mono(audio_file)
        
        # 读取音频 (16kHz, 16bit, mono)
        cmd = ["ffmpeg", "-i", audio_file, "-ar", "16000", "-ac", "1", "-f", "s16le", "-"]
        result = subprocess.run(cmd, capture_output=True)
        audio_data = np.frombuffer(result.stdout, dtype=np.int16)
        
        # 创建识别流
        stream = self.recognizer.create_stream()
        
        # 送入音频数据 (转换为 float32, 范围 [-1, 1])
        samples = audio_data.astype(np.float32) / 32768.0
        stream.accept_waveform(16000, samples)
        
        # 关键修正：OfflineRecognizer 使用 decode_streams (复数) 返回列表
        streams: List[sherpa_onnx.OfflineStream] = [stream]
        self.recognizer.decode_streams(streams)
        
        # 从 stream 对象直接获取结果
        result = stream.result
        
        return result.text.strip()
    
    def listen_and_recognize(self, duration: Optional[int] = None, cleanup: bool = True) -> Tuple[str, str]:
        """一键录音+识别"""
        wav_file = None
        try:
            wav_file = self.record(duration)
            text = self.recognize_file(wav_file)
            logger.info(f"📝 识别结果: {text}")
            return text, wav_file
        finally:
            if cleanup and wav_file:
                for f in [wav_file, wav_file.replace(".wav", "_mono.wav")]:
                    if os.path.exists(f):
                        os.remove(f)


def quick_recognize(duration: int = 5) -> str:
    asr = RespeakerASR()
    text, _ = asr.listen_and_recognize(duration=duration)
    return text


if __name__ == "__main__":
    print("=" * 60)
    print("🎤 ReSpeaker ASR (Whisper English) - Fixed")
    print("=" * 60)
    
    try:
        asr = RespeakerASR()
        print("🗣️  Please speak English (e.g., 'Schedule a meeting tomorrow at 3 PM')...")
        text, _ = asr.listen_and_recognize(duration=5)
        print(f"\n✅ Result: '{text}'")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise