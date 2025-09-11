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
@click.option('--fp16', is_flag=True, default=True,
              help='반정밀도(FP16) 사용 - GPU 가속 (기본: 켜짐)')
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
@click.option('--fp16', is_flag=True, default=True,
              help='반정밀도(FP16) 사용 - GPU 가속 (기본: 켜짐)')
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
@click.option('--type', type=click.Choice(['all', 'image', 'video']), default='all',
              help='처리할 파일 타입 (기본: all)')
@click.option('--output', type=click.Path(), default='./output',
              help='출력 폴더 경로 (기본: ./output)')
@click.option('--backend', type=click.Choice(['auto', 'torch', 'ncnn']), default='auto',
              help='업스케일링에 사용할 백엔드')
@click.option('--model', default='realesr-general-x4v3',
              help='업스케일링에 사용할 모델')
@click.option('--scale', type=int, default=4,
              help='업스케일링 배율')
@click.option('--recursive', is_flag=True,
              help='하위 폴더도 포함하여 처리')
@click.option('--pattern', default='*',
              help='파일명 패턴 (예: *.mp4, DSC*.jpg)')
@click.option('--skip-existing', is_flag=True,
              help='이미 처리된 파일 건너뛰기')
@click.option('--dry-run', is_flag=True,
              help='실제 처리하지 않고 대상 파일만 표시')
def all(type, output, recursive, pattern, skip_existing, dry_run, **kwargs):
    """현재 폴더의 모든 미디어 파일 업스케일링"""
    import os
    from pathlib import Path
    from .processors import ImageProcessor, VideoProcessor
    from .utils.display_utils import create_progress, console
    from rich.table import Table
    from rich.panel import Panel
    
    # 지원하는 파일 확장자
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.tiff', '.tif'}
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
    
    # 타입별 확장자 필터링
    if type == 'image':
        valid_extensions = image_extensions
    elif type == 'video':
        valid_extensions = video_extensions
    else:  # 'all'
        valid_extensions = image_extensions | video_extensions
    
    # 파일 검색
    current_dir = Path('.')
    if recursive:
        files = list(current_dir.rglob(pattern))
    else:
        files = list(current_dir.glob(pattern))
    
    # 처리할 파일 필터링
    target_files = []
    for file in files:
        if file.is_file() and file.suffix.lower() in valid_extensions:
            # 출력 경로 생성
            output_dir = Path(output)
            if recursive:
                # 하위 폴더 구조 유지
                relative_dir = file.parent.relative_to(current_dir)
                output_file = output_dir / relative_dir / f"{file.stem}_upscaled{file.suffix}"
            else:
                output_file = output_dir / f"{file.stem}_upscaled{file.suffix}"
            
            # 이미 처리된 파일 체크
            if skip_existing and output_file.exists():
                continue
                
            target_files.append((file, output_file, file.suffix.lower() in video_extensions))
    
    if not target_files:
        console.print(f"[yellow]⚠️ 처리할 파일을 찾을 수 없습니다. (타입: {type}, 패턴: {pattern})[/yellow]")
        return
    
    # 파일 목록 표시
    table = Table(title=f"🎯 처리할 파일 목록 ({len(target_files)}개)")
    table.add_column("📁 파일명", style="cyan")
    table.add_column("📊 크기", style="green")
    table.add_column("🎨 타입", style="yellow")
    
    total_size = 0
    for file, _, is_video in target_files:
        file_size = file.stat().st_size
        total_size += file_size
        size_str = f"{file_size / 1024 / 1024:.1f} MB"
        type_str = "🎥 비디오" if is_video else "🖼️ 이미지"
        table.add_row(str(file), size_str, type_str)
    
    console.print(table)
    console.print(f"\n💾 총 크기: {total_size / 1024 / 1024:.1f} MB")
    
    if dry_run:
        console.print("\n[cyan]ℹ️ --dry-run 모드: 실제 처리는 수행하지 않습니다.[/cyan]")
        return
    
    # 출력 폴더 생성
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 처리 시작
    console.print(Panel(f"🚀 {len(target_files)}개 파일 업스케일링 시작!", style="bold green"))
    
    success_count = 0
    error_count = 0
    
    with create_progress() as progress:
        task = progress.add_task(f"[cyan]🚀 Total Progress", total=len(target_files))
        
        for i, (input_file, output_file, is_video) in enumerate(target_files, 1):
            try:
                # 출력 파일의 디렉토리 생성
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                console.print(f"\n📍 Processing [{i}/{len(target_files)}]: {input_file}")
                
                if is_video:
                    processor = VideoProcessor(**kwargs)
                else:
                    processor = ImageProcessor(**kwargs)
                
                processor.process(str(input_file), str(output_file))
                success_count += 1
                
            except Exception as e:
                error_count += 1
                console.print(f"[red]❌ 오류 발생: {input_file} - {str(e)}[/red]")
            
            finally:
                progress.update(task, advance=1)
    
    # 최종 결과 표시
    console.print(Panel(
        f"✅ 완료: {success_count}개 성공, {error_count}개 실패\n"
        f"📁 출력 폴더: {output_dir.absolute()}",
        title="🎉 배치 처리 완료!",
        style="bold green" if error_count == 0 else "bold yellow"
    ))


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