import click
import sys
import os
from pathlib import Path
import json
import logging

from .backends import get_backend
from .models import ModelManager
from .utils import setup_logging, get_video_info, validate_input


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='상세 로그 출력 활성화')
@click.option('--debug', is_flag=True, help='디버그 로그 활성화')
def cli(verbose, debug):
    """Real-ESRGAN과 기타 모델을 사용한 영상 업스케일링 CLI 도구"""
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    setup_logging(level)


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--backend', type=click.Choice(['auto', 'torch', 'ncnn']), default='auto',
              help='업스케일링에 사용할 백엔드')
@click.option('--model', default='realesr-general-x4v3',
              help='업스케일링에 사용할 모델')
@click.option('--scale', type=int, default=4,
              help='업스케일링 배율')
@click.option('--tile', type=int, default=0,
              help='타일 크기 (0: 자동)')
@click.option('--tile-overlap', type=int, default=32,
              help='타일 겹침 크기 (픽셀)')
@click.option('--face-enhance', is_flag=True,
              help='GFPGAN으로 얼굴 향상 활성화')
@click.option('--face-strength', type=float, default=1.0,
              help='얼굴 향상 강도 (0.0-1.0)')
@click.option('--denoise', type=float, default=-1,
              help='노이즈 제거 강도 (-1: 자동)')
@click.option('--gamma', type=float, default=1.0,
              help='감마 보정 값 (1.0: 변경없음, <1.0: 밝게, >1.0: 어둡게)')
@click.option('--preserve-tone', is_flag=True, default=True,
              help='원본 이미지의 색상 톤 유지 (히스토그램 매칭)')
@click.option('--fp16', is_flag=True,
              help='반정밀도(FP16) 사용')
@click.option('--progress', type=click.Choice(['bar', 'json']), default='bar',
              help='진행 상황 표시 형식')
def image(input_path, output_path, **kwargs):
    """단일 이미지 업스케일링"""
    from .processors import ImageProcessor
    
    processor = ImageProcessor(**kwargs)
    processor.process(input_path, output_path)


@cli.command()
@click.argument('input_path', type=click.Path())
@click.argument('output_path', type=click.Path())
@click.option('--backend', type=click.Choice(['auto', 'torch', 'ncnn']), default='auto',
              help='업스케일링에 사용할 백엔드')
@click.option('--model', default='realesr-general-x4v3',
              help='업스케일링에 사용할 모델')
@click.option('--scale', type=int, default=4,
              help='업스케일링 배율')
@click.option('--tile', type=int, default=0,
              help='타일 크기 (0: 자동)')
@click.option('--tile-overlap', type=int, default=32,
              help='타일 겹침 크기 (픽셀)')
@click.option('--face-enhance', is_flag=True,
              help='GFPGAN으로 얼굴 향상 활성화')
@click.option('--face-strength', type=float, default=1.0,
              help='얼굴 향상 강도 (0.0-1.0)')
@click.option('--denoise', type=float, default=-1,
              help='노이즈 제거 강도 (-1: 자동)')
@click.option('--gamma', type=float, default=1.0,
              help='감마 보정 값 (1.0: 변경없음, <1.0: 밝게, >1.0: 어둡게)')
@click.option('--preserve-tone', is_flag=True, default=True,
              help='원본 이미지의 색상 톤 유지 (히스토그램 매칭)')
@click.option('--fp16', is_flag=True,
              help='반정밀도(FP16) 사용')
@click.option('--stdin', is_flag=True,
              help='표준 입력에서 읽기 (yuv4mpeg 형식)')
@click.option('--stdout', is_flag=True,
              help='표준 출력으로 쓰기 (yuv4mpeg 형식)')
@click.option('--copy-audio', is_flag=True,
              help='입력에서 출력으로 오디오 복사')
@click.option('--fps', type=float,
              help='출력 FPS (지정하지 않으면 자동 감지)')
@click.option('--progress', type=click.Choice(['bar', 'json']), default='bar',
              help='진행 상황 표시 형식')
def video(input_path, output_path, stdin, stdout, **kwargs):
    """비디오 파일 또는 스트림 업스케일링"""
    from .processors import VideoProcessor
    
    if stdin and input_path != '-':
        click.echo("오류: --stdin 옵션은 input_path가 '-'여야 합니다", err=True)
        sys.exit(1)
    
    if stdout and output_path != '-':
        click.echo("오류: --stdout 옵션은 output_path가 '-'여야 합니다", err=True)
        sys.exit(1)
    
    processor = VideoProcessor(stdin=stdin, stdout=stdout, **kwargs)
    processor.process(input_path, output_path)


@cli.command()
@click.option('--list', 'list_models', is_flag=True,
              help='사용 가능한 모델 목록 표시')
@click.option('--download', help='특정 모델 다운로드')
@click.option('--check', help='모델 사용 가능 여부 확인')
def models(list_models, download, check):
    """업스케일링 모델 관리"""
    manager = ModelManager()
    
    if list_models:
        models = manager.list_available_models()
        click.echo("사용 가능한 모델:")
        for model_name, info in models.items():
            status = "✓" if manager.is_model_available(model_name) else "✗"
            click.echo(f"  {status} {model_name}: {info.get('description', '설명 없음')}")
    
    if download:
        click.echo(f"모델 다운로드 중: {download}")
        manager.download_model(download)
        click.echo("다운로드 완료")
    
    if check:
        available = manager.is_model_available(check)
        status = "사용 가능" if available else "사용 불가"
        click.echo(f"모델 {check}: {status}")


@cli.command()
def doctor():
    """시스템 기능 및 구성 확인"""
    from .diagnostics import SystemDiagnostics
    
    diag = SystemDiagnostics()
    report = diag.generate_report()
    
    click.echo("시스템 진단 보고서")
    click.echo("=" * 25)
    
    for section, info in report.items():
        click.echo(f"\n{section}:")
        if isinstance(info, dict):
            for key, value in info.items():
                click.echo(f"  {key}: {value}")
        else:
            click.echo(f"  {info}")


if __name__ == '__main__':
    cli()