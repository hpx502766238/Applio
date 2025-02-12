import os
import sys
import json
import argparse
import subprocess
from functools import lru_cache
from distutils.util import strtobool

now_dir = os.getcwd()
sys.path.append(now_dir)

current_script_directory = os.path.dirname(os.path.realpath(__file__))
logs_path = os.path.join(current_script_directory, "logs")

from rvc.lib.tools.prerequisites_download import prequisites_download_pipeline
from rvc.train.extract.preparing_files import generate_config, generate_filelist
from rvc.train.process.model_blender import model_blender
from rvc.train.process.model_information import model_information
from rvc.train.process.extract_small_model import extract_small_model
from rvc.lib.tools.analyzer import analyze_audio
from rvc.lib.tools.launch_tensorboard import launch_tensorboard_pipeline
from rvc.lib.tools.model_download import model_download_pipeline

python = sys.executable


# Get TTS Voices -> https://speech.platform.bing.com/consumer/speech/synthesize/readaloud/voices/list?trustedclienttoken=6A5AA1D4EAFF4E9FB37E23D68491D6F4
@lru_cache(maxsize=1)  # Cache only one result since the file is static
def load_voices_data():
    with open(os.path.join("rvc", "lib", "tools", "tts_voices.json")) as f:
        return json.load(f)


voices_data = load_voices_data()
locales = list({voice["Locale"] for voice in voices_data})


@lru_cache(maxsize=None)
def import_voice_converter():
    from rvc.infer.infer import VoiceConverter

    return VoiceConverter()


@lru_cache(maxsize=1)
def get_config():
    from rvc.configs.config import Config

    return Config()


# Infer
def run_infer_script(
    pitch: int,
    filter_radius: int,
    index_rate: float,
    volume_envelope: int,
    protect: float,
    hop_length: int,
    f0_method: str,
    input_path: str,
    output_path: str,
    pth_path: str,
    index_path: str,
    split_audio: bool,
    f0_autotune: bool,
    clean_audio: bool,
    clean_strength: float,
    export_format: str,
    upscale_audio: bool,
    f0_file: str,
    embedder_model: str,
    embedder_model_custom: str = None,
):
    infer_pipeline = import_voice_converter()
    infer_pipeline.convert_audio(
        pitch=pitch,
        filter_radius=filter_radius,
        index_rate=index_rate,
        volume_envelope=volume_envelope,
        protect=protect,
        hop_length=hop_length,
        f0_method=f0_method,
        audio_input_path=input_path,
        audio_output_path=output_path,
        model_path=pth_path,
        index_path=index_path,
        split_audio=split_audio,
        f0_autotune=f0_autotune,
        clean_audio=clean_audio,
        clean_strength=clean_strength,
        export_format=export_format,
        upscale_audio=upscale_audio,
        f0_file=f0_file,
        embedder_model=embedder_model,
        embedder_model_custom=embedder_model_custom,
    )
    return f"File {input_path} inferred successfully.", output_path.replace(
        ".wav", f".{export_format.lower()}"
    )


# Batch infer
def run_batch_infer_script(
    pitch: int,
    filter_radius: int,
    index_rate: float,
    volume_envelope: int,
    protect: float,
    hop_length: int,
    f0_method: str,
    input_folder: str,
    output_folder: str,
    pth_path: str,
    index_path: str,
    split_audio: bool,
    f0_autotune: bool,
    clean_audio: bool,
    clean_strength: float,
    export_format: str,
    upscale_audio: bool,
    f0_file: str,
    embedder_model: str,
    embedder_model_custom: str = None,
):
    audio_files = [
        f for f in os.listdir(input_folder) if f.endswith((".mp3", ".wav", ".flac"))
    ]
    print(f"Detected {len(audio_files)} audio files for inference.")

    for audio_file in audio_files:
        if "_output" in audio_file:
            pass
        else:
            input_path = os.path.join(input_folder, audio_file)
            output_file_name = os.path.splitext(os.path.basename(audio_file))[0]
            output_path = os.path.join(
                output_folder,
                f"{output_file_name}_output{os.path.splitext(audio_file)[1]}",
            )
            infer_pipeline = import_voice_converter()
            print(f"Inferring {input_path}...")
            infer_pipeline.convert_audio(
                pitch=pitch,
                filter_radius=filter_radius,
                index_rate=index_rate,
                volume_envelope=volume_envelope,
                protect=protect,
                hop_length=hop_length,
                f0_method=f0_method,
                audio_input_path=input_path,
                audio_output_path=output_path,
                model_path=pth_path,
                index_path=index_path,
                split_audio=split_audio,
                f0_autotune=f0_autotune,
                clean_audio=clean_audio,
                clean_strength=clean_strength,
                export_format=export_format,
                upscale_audio=upscale_audio,
                f0_file=f0_file,
                embedder_model=embedder_model,
                embedder_model_custom=embedder_model_custom,
            )

    return f"Files from {input_folder} inferred successfully."


# TTS
def run_tts_script(
    tts_text: str,
    tts_voice: str,
    tts_rate: int,
    pitch: int,
    filter_radius: int,
    index_rate: float,
    volume_envelope: int,
    protect: float,
    hop_length: int,
    f0_method: str,
    output_tts_path: str,
    output_rvc_path: str,
    pth_path: str,
    index_path: str,
    split_audio: bool,
    f0_autotune: bool,
    clean_audio: bool,
    clean_strength: float,
    export_format: str,
    upscale_audio: bool,
    f0_file: str,
    embedder_model: str,
    embedder_model_custom: str = None,
):

    tts_script_path = os.path.join("rvc", "lib", "tools", "tts.py")

    if os.path.exists(output_tts_path):
        os.remove(output_tts_path)

    command_tts = [
        *map(
            str,
            [
                python,
                tts_script_path,
                tts_text,
                tts_voice,
                tts_rate,
                output_tts_path,
            ],
        ),
    ]
    subprocess.run(command_tts)
    infer_pipeline = import_voice_converter()
    infer_pipeline.convert_audio(
        pitch=pitch,
        filter_radius=filter_radius,
        index_rate=index_rate,
        volume_envelope=volume_envelope,
        protect=protect,
        hop_length=hop_length,
        f0_method=f0_method,
        audio_input_path=output_tts_path,
        audio_output_path=output_rvc_path,
        model_path=pth_path,
        index_path=index_path,
        split_audio=split_audio,
        f0_autotune=f0_autotune,
        clean_audio=clean_audio,
        clean_strength=clean_strength,
        export_format=export_format,
        upscale_audio=upscale_audio,
        f0_file=f0_file,
        embedder_model=embedder_model,
        embedder_model_custom=embedder_model_custom,
    )

    return f"Text {tts_text} synthesized successfully.", output_rvc_path.replace(
        ".wav", f".{export_format.lower()}"
    )


# Preprocess
def run_preprocess_script(
    model_name: str, dataset_path: str, sample_rate: int, cpu_cores: int
):
    config = get_config()
    per = 3.0 if config.is_half else 3.7
    preprocess_script_path = os.path.join("rvc", "train", "preprocess", "preprocess.py")
    command = [
        python,
        preprocess_script_path,
        *map(
            str,
            [
                os.path.join(logs_path, model_name),
                dataset_path,
                sample_rate,
                per,
                cpu_cores,
            ],
        ),
    ]
    os.makedirs(os.path.join(logs_path, model_name), exist_ok=True)
    subprocess.run(command)
    return f"Model {model_name} preprocessed successfully."


# Extract
def run_extract_script(
    model_name: str,
    rvc_version: str,
    f0_method: str,
    pitch_guidance: bool,
    hop_length: int,
    cpu_cores: int,
    gpu: int,
    sample_rate: int,
    embedder_model: str,
    embedder_model_custom: str = None,
):
    config = get_config()
    model_path = os.path.join(logs_path, model_name)
    pitch_extractor = os.path.join("rvc", "train", "extract", "pitch_extractor.py")
    embedding_extractor = os.path.join(
        "rvc", "train", "extract", "embedding_extractor.py"
    )

    command_1 = [
        python,
        pitch_extractor,
        *map(
            str,
            [
                model_path,
                f0_method,
                hop_length,
                cpu_cores,
                gpu,
            ],
        ),
    ]

    command_2 = [
        python,
        embedding_extractor,
        *map(
            str,
            [
                model_path,
                rvc_version,
                gpu,
                embedder_model,
                embedder_model_custom,
            ],
        ),
    ]
    subprocess.run(command_1)
    subprocess.run(command_2)

    generate_config(rvc_version, sample_rate, model_path)
    generate_filelist(pitch_guidance, model_path, rvc_version, sample_rate)
    return f"Model {model_name} extracted successfully."


# Train
def run_train_script(
    model_name: str,
    rvc_version: str,
    save_every_epoch: int,
    save_only_latest: bool,
    save_every_weights: bool,
    total_epoch: int,
    sample_rate: int,
    batch_size: int,
    gpu: int,
    pitch_guidance: bool,
    overtraining_detector: bool,
    overtraining_threshold: int,
    pretrained: bool,
    sync_graph: bool,
    cache_data_in_gpu: bool,
    custom_pretrained: bool = False,
    g_pretrained_path: str = None,
    d_pretrained_path: str = None,
):

    if pretrained == True:
        from rvc.lib.tools.pretrained_selector import pretrained_selector

        if custom_pretrained == False:
            pg, pd = pretrained_selector(bool(pitch_guidance))[str(rvc_version)][
                int(sample_rate)
            ]
        else:
            if g_pretrained_path is None or d_pretrained_path is None:
                raise ValueError(
                    "Please provide the path to the pretrained G and D models."
                )
            pg, pd = g_pretrained_path, d_pretrained_path
    else:
        pg, pd = "", ""

    train_script_path = os.path.join("rvc", "train", "train.py")
    command = [
        python,
        train_script_path,
        *map(
            str,
            [
                model_name,
                save_every_epoch,
                total_epoch,
                pg,
                pd,
                rvc_version,
                gpu,
                batch_size,
                sample_rate,
                pitch_guidance,
                save_only_latest,
                save_every_weights,
                cache_data_in_gpu,
                overtraining_detector,
                overtraining_threshold,
                sync_graph,
            ],
        ),
    ]
    subprocess.run(command)
    run_index_script(model_name, rvc_version)
    return f"Model {model_name} trained successfully."


# Index
def run_index_script(model_name: str, rvc_version: str):
    index_script_path = os.path.join("rvc", "train", "process", "extract_index.py")
    command = [
        python,
        index_script_path,
        os.path.join(logs_path, model_name),
        rvc_version,
    ]

    subprocess.run(command)
    return f"Index file for {model_name} generated successfully."


# Model extract
def run_model_extract_script(
    pth_path: str,
    model_name: str,
    sample_rate: int,
    pitch_guidance: bool,
    rvc_version: str,
    epoch: int,
    step: int,
):
    extract_small_model(
        pth_path, model_name, sample_rate, pitch_guidance, rvc_version, epoch, step
    )
    return f"Model {model_name} extracted successfully."


# Model information
def run_model_information_script(pth_path: str):
    print(model_information(pth_path))


# Model blender
def run_model_blender_script(
    model_name: str, pth_path_1: str, pth_path_2: str, ratio: float
):
    message, model_blended = model_blender(model_name, pth_path_1, pth_path_2, ratio)
    return message, model_blended


# Tensorboard
def run_tensorboard_script():
    launch_tensorboard_pipeline()


# Download
def run_download_script(model_link: str):
    model_download_pipeline(model_link)
    return f"Model downloaded successfully."


# Prerequisites
def run_prerequisites_script(
    pretraineds_v1: bool, pretraineds_v2: bool, models: bool, exe: bool
):
    prequisites_download_pipeline(pretraineds_v1, pretraineds_v2, models, exe)
    return "Prerequisites installed successfully."


# Audio analyzer
def run_audio_analyzer_script(
    input_path: str, save_plot_path: str = "logs/audio_analysis.png"
):
    audio_info, plot_path = analyze_audio(input_path, save_plot_path)
    print(
        f"Audio info of {input_path}: {audio_info}",
        f"Audio file {input_path} analyzed successfully. Plot saved at: {plot_path}",
    )
    return audio_info, plot_path


# API
def run_api_script(ip: str, port: int):
    command = [
        "env/Scripts/uvicorn.exe" if os.name == "nt" else "uvicorn",
        "api:app",
        "--host",
        ip,
        "--port",
        port,
    ]
    subprocess.run(command)


# Parse arguments
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run the main.py script with specific parameters."
    )
    subparsers = parser.add_subparsers(
        title="subcommands", dest="mode", help="Choose a mode"
    )

    # Parser for 'infer' mode
    infer_parser = subparsers.add_parser("infer", help="Run inference")
    pitch_description = (
        "Set the pitch of the audio. Higher values result in a higher pitch."
    )
    infer_parser.add_argument(
        "--pitch",
        type=int,
        help=pitch_description,
        choices=range(-24, 25),
        default=0,
    )
    filter_radius_description = "Apply median filtering to the extracted pitch values if this value is greater than or equal to three. This can help reduce breathiness in the output audio."
    infer_parser.add_argument(
        "--filter_radius",
        type=int,
        help=filter_radius_description,
        choices=range(11),
        default=3,
    )
    index_rate_description = "Control the influence of the index file on the output. Higher values mean stronger influence. Lower values can help reduce artifacts but may result in less accurate voice cloning."
    infer_parser.add_argument(
        "--index_rate",
        type=float,
        help=index_rate_description,
        choices=[(i / 10) for i in range(11)],
        default=0.3,
    )
    volume_envelope_description = "Control the blending of the output's volume envelope. A value of 1 means the output envelope is fully used."
    infer_parser.add_argument(
        "--volume_envelope",
        type=float,
        help=volume_envelope_description,
        choices=[(i / 10) for i in range(11)],
        default=1,
    )
    protect_description = "Protect consonants and breathing sounds from artifacts. A value of 0.5 offers the strongest protection, while lower values may reduce the protection level but potentially mitigate the indexing effect."
    infer_parser.add_argument(
        "--protect",
        type=float,
        help=protect_description,
        choices=[(i / 10) for i in range(6)],
        default=0.33,
    )
    hop_length_description = "Only applicable for the Crepe pitch extraction method. Determines the time it takes for the system to react to a significant pitch change. Smaller values require more processing time but can lead to better pitch accuracy."
    infer_parser.add_argument(
        "--hop_length",
        type=int,
        help=hop_length_description,
        choices=range(1, 513),
        default=128,
    )
    f0_method_description = "Choose the pitch extraction algorithm for the conversion. 'rmvpe' is the default and generally recommended."
    infer_parser.add_argument(
        "--f0_method",
        type=str,
        help=f0_method_description,
        choices=[
            "crepe",
            "crepe-tiny",
            "rmvpe",
            "fcpe",
            "hybrid[crepe+rmvpe]",
            "hybrid[crepe+fcpe]",
            "hybrid[rmvpe+fcpe]",
            "hybrid[crepe+rmvpe+fcpe]",
        ],
        default="rmvpe",
    )
    infer_parser.add_argument(
        "--input_path",
        type=str,
        help="Full path to the input audio file.",
        required=True,
    )
    infer_parser.add_argument(
        "--output_path",
        type=str,
        help="Full path to the output audio file.",
        required=True,
    )
    pth_path_description = "Full path to the RVC model file (.pth)."
    infer_parser.add_argument(
        "--pth_path", type=str, help=pth_path_description, required=True
    )
    index_path_description = "Full path to the index file (.index)."
    infer_parser.add_argument(
        "--index_path", type=str, help=index_path_description, required=True
    )
    split_audio_description = "Split the audio into smaller segments before inference. This can improve the quality of the output for longer audio files."
    infer_parser.add_argument(
        "--split_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=split_audio_description,
        default=False,
    )
    f0_autotune_description = "Apply a light autotune to the inferred audio. Particularly useful for singing voice conversions."
    infer_parser.add_argument(
        "--f0_autotune",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=f0_autotune_description,
        default=False,
    )
    clean_audio_description = "Clean the output audio using noise reduction algorithms. Recommended for speech conversions."
    infer_parser.add_argument(
        "--clean_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=clean_audio_description,
        default=False,
    )
    clean_strength_description = "Adjust the intensity of the audio cleaning process. Higher values result in stronger cleaning, but may lead to a more compressed sound."
    infer_parser.add_argument(
        "--clean_strength",
        type=float,
        help=clean_strength_description,
        choices=[(i / 10) for i in range(11)],
        default=0.7,
    )
    export_format_description = "Select the desired output audio format."
    infer_parser.add_argument(
        "--export_format",
        type=str,
        help=export_format_description,
        choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
        default="WAV",
    )
    embedder_model_description = (
        "Choose the model used for generating speaker embeddings."
    )
    infer_parser.add_argument(
        "--embedder_model",
        type=str,
        help=embedder_model_description,
        choices=[
            "contentvec",
            "japanese-hubert-base",
            "chinese-hubert-large",
            "custom",
        ],
        default="contentvec",
    )
    embedder_model_custom_description = "Specify the path to a custom model for speaker embedding. Only applicable if 'embedder_model' is set to 'custom'."
    infer_parser.add_argument(
        "--embedder_model_custom",
        type=str,
        help=embedder_model_custom_description,
        default=None,
    )
    upscale_audio_description = "Upscale the input audio to a higher quality before processing. This can improve the overall quality of the output, especially for low-quality input audio."
    infer_parser.add_argument(
        "--upscale_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=upscale_audio_description,
        default=False,
    )
    f0_file_description = "Full path to an external F0 file (.f0). This allows you to use pre-computed pitch values for the input audio."
    infer_parser.add_argument(
        "--f0_file",
        type=str,
        help=f0_file_description,
        default=None,
    )

    # Parser for 'batch_infer' mode
    batch_infer_parser = subparsers.add_parser(
        "batch_infer",
        help="Run batch inference",
    )
    batch_infer_parser.add_argument(
        "--pitch",
        type=int,
        help=pitch_description,
        choices=range(-24, 25),
        default=0,
    )
    batch_infer_parser.add_argument(
        "--filter_radius",
        type=int,
        help=filter_radius_description,
        choices=range(11),
        default=3,
    )
    batch_infer_parser.add_argument(
        "--index_rate",
        type=float,
        help=index_rate_description,
        choices=[(i / 10) for i in range(11)],
        default=0.3,
    )
    batch_infer_parser.add_argument(
        "--volume_envelope",
        type=float,
        help=volume_envelope_description,
        choices=[(i / 10) for i in range(11)],
        default=1,
    )
    batch_infer_parser.add_argument(
        "--protect",
        type=float,
        help=protect_description,
        choices=[(i / 10) for i in range(6)],
        default=0.33,
    )
    batch_infer_parser.add_argument(
        "--hop_length",
        type=int,
        help=hop_length_description,
        choices=range(1, 513),
        default=128,
    )
    batch_infer_parser.add_argument(
        "--f0_method",
        type=str,
        help=f0_method_description,
        choices=[
            "crepe",
            "crepe-tiny",
            "rmvpe",
            "fcpe",
            "hybrid[crepe+rmvpe]",
            "hybrid[crepe+fcpe]",
            "hybrid[rmvpe+fcpe]",
            "hybrid[crepe+rmvpe+fcpe]",
        ],
        default="rmvpe",
    )
    batch_infer_parser.add_argument(
        "--input_folder",
        type=str,
        help="Path to the folder containing input audio files.",
        required=True,
    )
    batch_infer_parser.add_argument(
        "--output_folder",
        type=str,
        help="Path to the folder for saving output audio files.",
        required=True,
    )
    batch_infer_parser.add_argument(
        "--pth_path", type=str, help=pth_path_description, required=True
    )
    batch_infer_parser.add_argument(
        "--index_path", type=str, help=index_path_description, required=True
    )
    batch_infer_parser.add_argument(
        "--split_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=split_audio_description,
        default=False,
    )
    batch_infer_parser.add_argument(
        "--f0_autotune",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=f0_autotune_description,
        default=False,
    )
    batch_infer_parser.add_argument(
        "--clean_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=clean_audio_description,
        default=False,
    )
    batch_infer_parser.add_argument(
        "--clean_strength",
        type=float,
        help=clean_strength_description,
        choices=[(i / 10) for i in range(11)],
        default=0.7,
    )
    batch_infer_parser.add_argument(
        "--export_format",
        type=str,
        help=export_format_description,
        choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
        default="WAV",
    )
    batch_infer_parser.add_argument(
        "--embedder_model",
        type=str,
        help=embedder_model_description,
        choices=[
            "contentvec",
            "japanese-hubert-base",
            "chinese-hubert-large",
            "custom",
        ],
        default="contentvec",
    )
    batch_infer_parser.add_argument(
        "--embedder_model_custom",
        type=str,
        help=embedder_model_custom_description,
        default=None,
    )
    batch_infer_parser.add_argument(
        "--upscale_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=upscale_audio_description,
        default=False,
    )
    batch_infer_parser.add_argument(
        "--f0_file",
        type=str,
        help=f0_file_description,
        default=None,
    )

    # Parser for 'tts' mode
    tts_parser = subparsers.add_parser("tts", help="Run TTS inference")
    tts_parser.add_argument(
        "--tts_text", type=str, help="Text to be synthesized", required=True
    )
    tts_parser.add_argument(
        "--tts_voice",
        type=str,
        help="Voice to be used for TTS synthesis.",
        choices=locales,
        required=True,
    )
    tts_parser.add_argument(
        "--tts_rate",
        type=int,
        help="Control the speaking rate of the TTS. Values range from -100 (slower) to 100 (faster).",
        choices=range(-100, 101),
        default=0,
    )
    tts_parser.add_argument(
        "--pitch",
        type=int,
        help=pitch_description,
        choices=range(-24, 25),
        default=0,
    )
    tts_parser.add_argument(
        "--filter_radius",
        type=int,
        help=filter_radius_description,
        choices=range(11),
        default=3,
    )
    tts_parser.add_argument(
        "--index_rate",
        type=float,
        help=index_rate_description,
        choices=[(i / 10) for i in range(11)],
        default=0.3,
    )
    tts_parser.add_argument(
        "--volume_envelope",
        type=float,
        help=volume_envelope_description,
        choices=[(i / 10) for i in range(11)],
        default=1,
    )
    tts_parser.add_argument(
        "--protect",
        type=float,
        help=protect_description,
        choices=[(i / 10) for i in range(6)],
        default=0.33,
    )
    tts_parser.add_argument(
        "--hop_length",
        type=int,
        help=hop_length_description,
        choices=range(1, 513),
        default=128,
    )
    tts_parser.add_argument(
        "--f0_method",
        type=str,
        help=f0_method_description,
        choices=[
            "crepe",
            "crepe-tiny",
            "rmvpe",
            "fcpe",
            "hybrid[crepe+rmvpe]",
            "hybrid[crepe+fcpe]",
            "hybrid[rmvpe+fcpe]",
            "hybrid[crepe+rmvpe+fcpe]",
        ],
        default="rmvpe",
    )
    tts_parser.add_argument(
        "--output_tts_path",
        type=str,
        help="Full path to save the synthesized TTS audio.",
        required=True,
    )
    tts_parser.add_argument(
        "--output_rvc_path",
        type=str,
        help="Full path to save the voice-converted audio using the synthesized TTS.",
        required=True,
    )
    tts_parser.add_argument(
        "--pth_path", type=str, help=pth_path_description, required=True
    )
    tts_parser.add_argument(
        "--index_path", type=str, help=index_path_description, required=True
    )
    tts_parser.add_argument(
        "--split_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=split_audio_description,
        default=False,
    )
    tts_parser.add_argument(
        "--f0_autotune",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=f0_autotune_description,
        default=False,
    )
    tts_parser.add_argument(
        "--clean_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=clean_audio_description,
        default=False,
    )
    tts_parser.add_argument(
        "--clean_strength",
        type=float,
        help=clean_strength_description,
        choices=[(i / 10) for i in range(11)],
        default=0.7,
    )
    tts_parser.add_argument(
        "--export_format",
        type=str,
        help=export_format_description,
        choices=["WAV", "MP3", "FLAC", "OGG", "M4A"],
        default="WAV",
    )
    tts_parser.add_argument(
        "--embedder_model",
        type=str,
        help=embedder_model_description,
        choices=[
            "contentvec",
            "japanese-hubert-base",
            "chinese-hubert-large",
            "custom",
        ],
        default="contentvec",
    )
    tts_parser.add_argument(
        "--embedder_model_custom",
        type=str,
        help=embedder_model_custom_description,
        default=None,
    )
    tts_parser.add_argument(
        "--upscale_audio",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help=upscale_audio_description,
        default=False,
    )
    tts_parser.add_argument(
        "--f0_file",
        type=str,
        help=f0_file_description,
        default=None,
    )

    # Parser for 'preprocess' mode
    preprocess_parser = subparsers.add_parser(
        "preprocess", help="Preprocess a dataset for training."
    )
    preprocess_parser.add_argument(
        "--model_name", type=str, help="Name of the model to be trained.", required=True
    )
    preprocess_parser.add_argument(
        "--dataset_path", type=str, help="Path to the dataset directory.", required=True
    )
    preprocess_parser.add_argument(
        "--sample_rate",
        type=int,
        help="Target sampling rate for the audio data.",
        choices=[32000, 40000, 48000],
        required=True,
    )
    preprocess_parser.add_argument(
        "--cpu_cores",
        type=int,
        help="Number of CPU cores to use for preprocessing.",
        choices=range(1, 65),
    )

    # Parser for 'extract' mode
    extract_parser = subparsers.add_parser(
        "extract", help="Extract features from a dataset."
    )
    extract_parser.add_argument(
        "--model_name", type=str, help="Name of the model.", required=True
    )
    extract_parser.add_argument(
        "--rvc_version",
        type=str,
        help="Version of the RVC model ('v1' or 'v2').",
        choices=["v1", "v2"],
        default="v2",
    )
    extract_parser.add_argument(
        "--f0_method",
        type=str,
        help="Pitch extraction method to use.",
        choices=[
            "crepe",
            "crepe-tiny",
            "rmvpe",
        ],
        default="rmvpe",
    )
    extract_parser.add_argument(
        "--pitch_guidance",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Enable or disable pitch guidance during feature extraction.",
        default=True,
    )
    extract_parser.add_argument(
        "--hop_length",
        type=int,
        help="Hop length for feature extraction. Only applicable for Crepe pitch extraction.",
        choices=range(1, 513),
        default=128,
    )
    extract_parser.add_argument(
        "--cpu_cores",
        type=int,
        help="Number of CPU cores to use for feature extraction (optional).",
        choices=range(1, 65),
        default=None,
    )
    extract_parser.add_argument(
        "--gpu",
        type=int,
        help="GPU device to use for feature extraction (optional).",
        default="-",
    )
    extract_parser.add_argument(
        "--sample_rate",
        type=int,
        help="Target sampling rate for the audio data.",
        choices=[32000, 40000, 48000],
        required=True,
    )
    extract_parser.add_argument(
        "--embedder_model",
        type=str,
        help=embedder_model_description,
        choices=[
            "contentvec",
            "japanese-hubert-base",
            "chinese-hubert-large",
            "custom",
        ],
        default="contentvec",
    )
    extract_parser.add_argument(
        "--embedder_model_custom",
        type=str,
        help=embedder_model_custom_description,
        default=None,
    )

    # Parser for 'train' mode
    train_parser = subparsers.add_parser("train", help="Train an RVC model.")
    train_parser.add_argument(
        "--model_name", type=str, help="Name of the model to be trained.", required=True
    )
    train_parser.add_argument(
        "--rvc_version",
        type=str,
        help="Version of the RVC model to train ('v1' or 'v2').",
        choices=["v1", "v2"],
        default="v2",
    )
    train_parser.add_argument(
        "--save_every_epoch",
        type=int,
        help="Save the model every specified number of epochs.",
        choices=range(1, 101),
        required=True,
    )
    train_parser.add_argument(
        "--save_only_latest",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Save only the latest model checkpoint.",
        default=False,
    )
    train_parser.add_argument(
        "--save_every_weights",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Save model weights every epoch.",
        default=True,
    )
    train_parser.add_argument(
        "--total_epoch",
        type=int,
        help="Total number of epochs to train for.",
        choices=range(1, 10001),
        default=1000,
    )
    train_parser.add_argument(
        "--sample_rate",
        type=int,
        help="Sampling rate of the training data.",
        choices=[32000, 40000, 48000],
        required=True,
    )
    train_parser.add_argument(
        "--batch_size",
        type=int,
        help="Batch size for training.",
        choices=range(1, 51),
        default=8,
    )
    train_parser.add_argument(
        "--gpu",
        type=str,
        help="GPU device to use for training (e.g., '0').",
        default="0",
    )
    train_parser.add_argument(
        "--pitch_guidance",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Enable or disable pitch guidance during training.",
        default=True,
    )
    train_parser.add_argument(
        "--pretrained",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Use a pretrained model for initialization.",
        default=True,
    )
    train_parser.add_argument(
        "--custom_pretrained",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Use a custom pretrained model.",
        default=False,
    )
    train_parser.add_argument(
        "--g_pretrained_path",
        type=str,
        nargs="?",
        default=None,
        help="Path to the pretrained generator model file.",
    )
    train_parser.add_argument(
        "--d_pretrained_path",
        type=str,
        nargs="?",
        default=None,
        help="Path to the pretrained discriminator model file.",
    )
    train_parser.add_argument(
        "--overtraining_detector",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Enable overtraining detection.",
        default=False,
    )
    train_parser.add_argument(
        "--overtraining_threshold",
        type=int,
        help="Threshold for overtraining detection.",
        choices=range(1, 101),
        default=50,
    )
    train_parser.add_argument(
        "--sync_graph",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Enable graph synchronization for distributed training.",
        default=False,
    )
    train_parser.add_argument(
        "--cache_data_in_gpu",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Cache training data in GPU memory.",
        default=False,
    )

    # Parser for 'index' mode
    index_parser = subparsers.add_parser(
        "index", help="Generate an index file for an RVC model."
    )
    index_parser.add_argument(
        "--model_name", type=str, help="Name of the model.", required=True
    )
    index_parser.add_argument(
        "--rvc_version",
        type=str,
        help="Version of the RVC model ('v1' or 'v2').",
        choices=["v1", "v2"],
        default="v2",
    )

    # Parser for 'model_extract' mode
    model_extract_parser = subparsers.add_parser(
        "model_extract", help="Extract a specific epoch from a trained model."
    )
    model_extract_parser.add_argument(
        "--pth_path", type=str, help="Path to the main .pth model file.", required=True
    )
    model_extract_parser.add_argument(
        "--model_name", type=str, help="Name of the model.", required=True
    )
    model_extract_parser.add_argument(
        "--sample_rate",
        type=int,
        help="Sampling rate of the extracted model.",
        choices=[32000, 40000, 48000],
        required=True,
    )
    model_extract_parser.add_argument(
        "--pitch_guidance",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        help="Enable or disable pitch guidance for the extracted model.",
        required=True,
    )
    model_extract_parser.add_argument(
        "--rvc_version",
        type=str,
        help="Version of the extracted RVC model ('v1' or 'v2').",
        choices=["v1", "v2"],
        default="v2",
    )
    model_extract_parser.add_argument(
        "--epoch",
        type=int,
        help="Epoch number to extract from the model.",
        choices=range(1, 10001),
        required=True,
    )
    model_extract_parser.add_argument(
        "--step",
        type=str,
        help="Step number to extract from the model (optional).",
        required=False,
    )

    # Parser for 'model_information' mode
    model_information_parser = subparsers.add_parser(
        "model_information", help="Display information about a trained model."
    )
    model_information_parser.add_argument(
        "--pth_path", type=str, help="Path to the .pth model file.", required=True
    )

    # Parser for 'model_blender' mode
    model_blender_parser = subparsers.add_parser(
        "model_blender", help="Fuse two RVC models together."
    )
    model_blender_parser.add_argument(
        "--model_name", type=str, help="Name of the new fused model.", required=True
    )
    model_blender_parser.add_argument(
        "--pth_path_1",
        type=str,
        help="Path to the first .pth model file.",
        required=True,
    )
    model_blender_parser.add_argument(
        "--pth_path_2",
        type=str,
        help="Path to the second .pth model file.",
        required=True,
    )
    model_blender_parser.add_argument(
        "--ratio",
        type=float,
        help="Ratio for blending the two models (0.0 to 1.0).",
        choices=[(i / 10) for i in range(11)],
        default=0.5,
    )

    # Parser for 'tensorboard' mode
    subparsers.add_parser(
        "tensorboard", help="Launch TensorBoard for monitoring training progress."
    )

    # Parser for 'download' mode
    download_parser = subparsers.add_parser(
        "download", help="Download a model from a provided link."
    )
    download_parser.add_argument(
        "--model_link", type=str, help="Direct link to the model file.", required=True
    )

    # Parser for 'prerequisites' mode
    prerequisites_parser = subparsers.add_parser(
        "prerequisites", help="Install prerequisites for RVC."
    )
    prerequisites_parser.add_argument(
        "--pretraineds_v1",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        default=True,
        help="Download pretrained models for RVC v1.",
    )
    prerequisites_parser.add_argument(
        "--pretraineds_v2",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        default=True,
        help="Download pretrained models for RVC v2.",
    )
    prerequisites_parser.add_argument(
        "--models",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        default=True,
        help="Download additional models.",
    )
    prerequisites_parser.add_argument(
        "--exe",
        type=lambda x: bool(strtobool(x)),
        choices=[True, False],
        default=True,
        help="Download required executables.",
    )

    # Parser for 'audio_analyzer' mode
    audio_analyzer = subparsers.add_parser(
        "audio_analyzer", help="Analyze an audio file."
    )
    audio_analyzer.add_argument(
        "--input_path", type=str, help="Path to the input audio file.", required=True
    )

    # Parser for 'api' mode
    api_parser = subparsers.add_parser("api", help="Start the RVC API server.")
    api_parser.add_argument(
        "--host", type=str, help="Host address for the API server.", default="127.0.0.1"
    )
    api_parser.add_argument(
        "--port", type=int, help="Port for the API server.", default=8000
    )

    return parser.parse_args()


def main():
    if len(sys.argv) == 1:
        print("Please run the script with '-h' for more information.")
        sys.exit(1)

    args = parse_arguments()

    try:
        if args.mode == "infer":
            run_infer_script(
                pitch=args.pitch,
                filter_radius=args.filter_radius,
                index_rate=args.index_rate,
                volume_envelope=args.volume_envelope,
                protect=args.protect,
                hop_length=args.hop_length,
                f0_method=args.f0_method,
                input_path=args.input_path,
                output_path=args.output_path,
                pth_path=args.pth_path,
                index_path=args.index_path,
                split_audio=args.split_audio,
                f0_autotune=args.f0_autotune,
                clean_audio=args.clean_audio,
                clean_strength=args.clean_strength,
                export_format=args.export_format,
                embedder_model=args.embedder_model,
                embedder_model_custom=args.embedder_model_custom,
                upscale_audio=args.upscale_audio,
                f0_file=args.f0_file,
            )
        elif args.mode == "batch_infer":
            run_batch_infer_script(
                pitch=args.pitch,
                filter_radius=args.filter_radius,
                index_rate=args.index_rate,
                volume_envelope=args.volume_envelope,
                protect=args.protect,
                hop_length=args.hop_length,
                f0_method=args.f0_method,
                input_folder=args.input_folder,
                output_folder=args.output_folder,
                pth_path=args.pth_path,
                index_path=args.index_path,
                split_audio=args.split_audio,
                f0_autotune=args.f0_autotune,
                clean_audio=args.clean_audio,
                clean_strength=args.clean_strength,
                export_format=args.export_format,
                embedder_model=args.embedder_model,
                embedder_model_custom=args.embedder_model_custom,
                upscale_audio=args.upscale_audio,
                f0_file=args.f0_file,
            )
        elif args.mode == "tts":
            run_tts_script(
                tts_text=args.tts_text,
                tts_voice=args.tts_voice,
                tts_rate=args.tts_rate,
                pitch=args.pitch,
                filter_radius=args.filter_radius,
                index_rate=args.index_rate,
                volume_envelope=args.volume_envelope,
                protect=args.protect,
                hop_length=args.hop_length,
                f0_method=args.f0_method,
                input_path=args.input_path,
                output_path=args.output_path,
                pth_path=args.pth_path,
                index_path=args.index_path,
                split_audio=args.split_audio,
                f0_autotune=args.f0_autotune,
                clean_audio=args.clean_audio,
                clean_strength=args.clean_strength,
                export_format=args.export_format,
                embedder_model=args.embedder_model,
                embedder_model_custom=args.embedder_model_custom,
                upscale_audio=args.upscale_audio,
                f0_file=args.f0_file,
            )
        elif args.mode == "preprocess":
            run_preprocess_script(
                model_name=args.model_name,
                dataset_path=args.dataset_path,
                sample_rate=args.sample_rate,
                cpu_cores=args.cpu_cores,
            )
        elif args.mode == "extract":
            run_extract_script(
                model_name=args.model_name,
                rvc_version=args.rvc_version,
                f0_method=args.f0_method,
                pitch_guidance=args.pitch_guidance,
                hop_length=args.hop_length,
                cpu_cores=args.cpu_cores,
                gpu=args.gpu,
                sample_rate=args.sample_rate,
                embedder_model=args.embedder_model,
                embedder_model_custom=args.embedder_model_custom,
            )
        elif args.mode == "train":
            run_train_script(
                model_name=args.model_name,
                rvc_version=args.rvc_version,
                save_every_epoch=args.save_every_epoch,
                save_only_latest=args.save_only_latest,
                save_every_weights=args.save_every_weights,
                total_epoch=args.total_epoch,
                sample_rate=args.sample_rate,
                batch_size=args.batch_size,
                gpu=args.gpu,
                pitch_guidance=args.pitch_guidance,
                overtraining_detector=args.overtraining_detector,
                overtraining_threshold=args.overtraining_threshold,
                pretrained=args.pretrained,
                custom_pretrained=args.custom_pretrained,
                sync_graph=args.sync_graph,
                cache_data_in_gpu=args.cache_data_in_gpu,
                g_pretrained_path=args.g_pretrained_path,
                d_pretrained_path=args.d_pretrained_path,
            )
        elif args.mode == "index":
            run_index_script(
                model_name=args.model_name,
                rvc_version=args.rvc_version,
            )
        elif args.mode == "model_extract":
            run_model_extract_script(
                pth_path=args.pth_path,
                model_name=args.model_name,
                sample_rate=args.sample_rate,
                pitch_guidance=args.pitch_guidance,
                rvc_version=args.rvc_version,
                epoch=args.epoch,
                step=args.step,
            )
        elif args.mode == "model_information":
            run_model_information_script(
                pth_path=args.pth_path,
            )
        elif args.mode == "model_blender":
            run_model_blender_script(
                model_name=args.model_name,
                pth_path_1=args.pth_path_1,
                pth_path_2=args.pth_path_2,
                ratio=args.ratio,
            )
        elif args.mode == "tensorboard":
            run_tensorboard_script()
        elif args.mode == "download":
            run_download_script(
                model_link=args.model_link,
            )
        elif args.mode == "prerequisites":
            run_prerequisites_script(
                pretraineds_v1=args.pretraineds_v1,
                pretraineds_v2=args.pretraineds_v2,
                models=args.models,
                exe=args.exe,
            )
        elif args.mode == "audio_analyzer":
            run_audio_analyzer_script(
                input_path=args.input_path,
            )
        elif args.mode == "api":
            run_api_script(
                ip=args.host,
                port=args.port,
            )
    except Exception as error:
        print(f"An error occurred during execution: {error}")

        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
